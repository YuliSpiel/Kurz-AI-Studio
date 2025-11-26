"""
YouTube API endpoints: OAuth authorization and video upload.
"""
import logging
import httpx
import os
import tempfile
from urllib.parse import urlencode
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user, verify_token
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/youtube", tags=["youtube"])

# YouTube OAuth URLs
YOUTUBE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# YouTube API scopes needed for uploading
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class YouTubeUploadRequest(BaseModel):
    run_id: str
    title: str
    description: str = ""
    scheduled_time: Optional[str] = None  # ISO format datetime string


class YouTubeUploadResponse(BaseModel):
    success: bool
    message: str
    video_id: Optional[str] = None
    video_url: Optional[str] = None


class YouTubeConnectionStatus(BaseModel):
    connected: bool
    channel_name: Optional[str] = None


@router.get("/auth")
async def youtube_auth(token: str = Query(..., description="JWT token for user identification")):
    """
    Initiate YouTube OAuth flow - redirects to Google authorization page.
    Requires JWT token as query param to identify user after callback.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    # Verify token to ensure valid user
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Use state parameter to pass JWT token through OAuth flow
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_ORIGIN.replace('http://localhost:5173', 'http://localhost:8080')}/api/youtube/callback",
        "response_type": "code",
        "scope": " ".join(["openid", "email", "profile"] + YOUTUBE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": token,  # Pass JWT token in state to identify user in callback
    }

    auth_url = f"{YOUTUBE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def youtube_callback(
    code: str,
    state: str,  # JWT token passed from /auth
    db: AsyncSession = Depends(get_db)
):
    """
    YouTube OAuth callback - exchange code for tokens and store refresh_token.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    # Verify JWT token from state
    payload = verify_token(state)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid state token"
        )

    user_id = payload.get("sub")

    try:
        redirect_uri = f"{settings.FRONTEND_ORIGIN.replace('http://localhost:5173', 'http://localhost:8080')}/api/youtube/callback"

        async with httpx.AsyncClient() as client:
            # Exchange code for tokens
            token_response = await client.post(
                YOUTUBE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )

            if token_response.status_code != 200:
                logger.error(f"YouTube token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )

            tokens = token_response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            logger.info(f"[YOUTUBE] Got tokens - refresh_token exists: {bool(refresh_token)}")

            if not refresh_token:
                logger.warning("[YOUTUBE] No refresh token received - user may have already authorized")
                # Try to continue anyway, maybe we already have a refresh token stored

            # Get YouTube channel info
            channel_response = await client.get(
                YOUTUBE_CHANNEL_URL,
                params={"part": "snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"}
            )

            channel_name = None
            if channel_response.status_code == 200:
                channel_data = channel_response.json()
                if channel_data.get("items"):
                    channel_name = channel_data["items"][0]["snippet"]["title"]
                    logger.info(f"[YOUTUBE] Connected channel: {channel_name}")

        # Update user with YouTube tokens
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if refresh_token:
            user.youtube_refresh_token = refresh_token
        if channel_name:
            user.youtube_channel_name = channel_name

        await db.commit()
        logger.info(f"[YOUTUBE] Saved YouTube connection for user {user_id}")

        # Redirect back to frontend with success
        frontend_url = settings.FRONTEND_ORIGIN
        redirect_url = f"{frontend_url}?youtube_connected=true"

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[YOUTUBE] OAuth error: {e}", exc_info=True)
        frontend_url = settings.FRONTEND_ORIGIN
        return RedirectResponse(url=f"{frontend_url}?youtube_error=true")


async def refresh_youtube_token(refresh_token: str) -> str:
    """
    Refresh YouTube access token using stored refresh token.
    Returns new access token.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            YOUTUBE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )

        if response.status_code != 200:
            logger.error(f"[YOUTUBE] Token refresh failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh YouTube token. Please reconnect your YouTube account."
            )

        tokens = response.json()
        return tokens.get("access_token")


@router.post("/upload", response_model=YouTubeUploadResponse)
async def upload_to_youtube(
    request: YouTubeUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload video to YouTube.
    """
    logger.info(f"[YOUTUBE] Upload request from user {current_user.id}: {request.run_id}")

    # Check if user has YouTube connected
    if not current_user.youtube_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube 계정이 연결되지 않았습니다. 먼저 YouTube 연결을 해주세요."
        )

    # Get video file path
    video_path = settings.OUTPUT_DIR / request.run_id / "final_video.mp4"

    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"영상 파일을 찾을 수 없습니다: {request.run_id}"
        )

    try:
        # Refresh access token
        access_token = await refresh_youtube_token(current_user.youtube_refresh_token)

        # Create credentials object
        credentials = Credentials(
            token=access_token,
            refresh_token=current_user.youtube_refresh_token,
            token_uri=YOUTUBE_TOKEN_URL,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

        # Build YouTube API client
        youtube = build("youtube", "v3", credentials=credentials)

        # Prepare video metadata for YouTube Shorts
        # YouTube Shorts requirements:
        # - Vertical video (9:16 aspect ratio) - our videos are 1080x1920
        # - Under 60 seconds
        # - #Shorts in title or description helps algorithm recognize it
        shorts_title = request.title
        if "#Shorts" not in shorts_title and "#shorts" not in shorts_title:
            shorts_title = f"{request.title} #Shorts"

        default_description = (
            f"{request.description}\n\n" if request.description else ""
        ) + f"#Shorts #AI #Kurz\n\nCreated with Kurz AI Studio\n업로드 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        body = {
            "snippet": {
                "title": shorts_title,
                "description": default_description,
                "tags": ["Shorts", "shorts", "kurz", "AI", "숏츠", "쇼츠"],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "public",  # or "private", "unlisted"
                "selfDeclaredMadeForKids": False,
            }
        }

        # Handle scheduled upload
        if request.scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(request.scheduled_time.replace('Z', '+00:00'))
                body["status"]["privacyStatus"] = "private"
                body["status"]["publishAt"] = scheduled_dt.isoformat()
                logger.info(f"[YOUTUBE] Scheduling upload for: {scheduled_dt}")
            except ValueError as e:
                logger.warning(f"[YOUTUBE] Invalid scheduled_time format: {e}")

        # Create media upload object
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True
        )

        # Execute upload
        logger.info(f"[YOUTUBE] Starting upload: {request.title}")
        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status_upload, response = insert_request.next_chunk()
            if status_upload:
                logger.info(f"[YOUTUBE] Upload progress: {int(status_upload.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info(f"[YOUTUBE] Upload complete! Video ID: {video_id}")

        return YouTubeUploadResponse(
            success=True,
            message="YouTube 업로드가 완료되었습니다!",
            video_id=video_id,
            video_url=video_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[YOUTUBE] Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YouTube 업로드 실패: {str(e)}"
        )


@router.get("/status", response_model=YouTubeConnectionStatus)
async def youtube_connection_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has YouTube connected.
    """
    is_connected = bool(current_user.youtube_refresh_token)

    return YouTubeConnectionStatus(
        connected=is_connected,
        channel_name=current_user.youtube_channel_name if is_connected else None
    )


@router.post("/disconnect")
async def disconnect_youtube(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect YouTube account from user.
    """
    current_user.youtube_refresh_token = None
    current_user.youtube_channel_name = None
    await db.commit()

    logger.info(f"[YOUTUBE] Disconnected YouTube for user {current_user.id}")

    return {"success": True, "message": "YouTube 연결이 해제되었습니다."}
