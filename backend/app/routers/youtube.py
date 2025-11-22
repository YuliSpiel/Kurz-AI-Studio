"""
YouTube API endpoints: OAuth authorization and video upload.
"""
import logging
import httpx
from urllib.parse import urlencode
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/youtube", tags=["youtube"])

# YouTube OAuth URLs
YOUTUBE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# YouTube API scopes needed for uploading
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


class YouTubeUploadRequest(BaseModel):
    run_id: str
    title: str
    scheduled_time: Optional[str] = None
    platforms: List[str] = ["youtube"]


class YouTubeUploadResponse(BaseModel):
    success: bool
    message: str
    video_id: Optional[str] = None


@router.get("/auth")
async def youtube_auth():
    """
    Initiate YouTube OAuth flow - redirects to Google authorization page.
    Requires additional YouTube upload scopes beyond basic login.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI.replace("/auth/google/callback", "/youtube/callback"),
        "response_type": "code",
        "scope": " ".join(["openid", "email", "profile"] + YOUTUBE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{YOUTUBE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def youtube_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    YouTube OAuth callback - exchange code for tokens with YouTube upload scope.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    try:
        redirect_uri = settings.GOOGLE_REDIRECT_URI.replace("/auth/google/callback", "/youtube/callback")

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

            # TODO: Store youtube_refresh_token in User model for persistent access
            # For now, just redirect back with success indicator

        frontend_url = settings.FRONTEND_ORIGIN
        redirect_url = f"{frontend_url}/auth/callback?youtube=connected"

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[YOUTUBE] OAuth error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YouTube OAuth failed: {str(e)}"
        )


@router.post("/upload", response_model=YouTubeUploadResponse)
async def upload_to_youtube(
    request: YouTubeUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload video to YouTube.

    This is a placeholder implementation. Full implementation requires:
    1. Storing user's YouTube refresh token in database
    2. Using google-api-python-client to upload video
    3. Handling resumable uploads for large files
    """
    logger.info(f"[YOUTUBE] Upload request from user {current_user.id}: {request.run_id}")

    # TODO: Implement actual YouTube upload
    # For now, return a placeholder response

    # Check if user has YouTube connected
    # if not current_user.youtube_refresh_token:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="YouTube account not connected. Please authorize first."
    #     )

    # Full implementation would:
    # 1. Get video file path from run_id
    # 2. Refresh YouTube access token using stored refresh_token
    # 3. Use YouTube Data API v3 to upload video
    # 4. Return the uploaded video ID

    return YouTubeUploadResponse(
        success=False,
        message="YouTube upload not yet implemented. Please connect your YouTube account first.",
        video_id=None
    )


@router.get("/status")
async def youtube_connection_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has YouTube connected.
    """
    # TODO: Add youtube_refresh_token field to User model
    # is_connected = bool(current_user.youtube_refresh_token)

    return {
        "connected": False,  # Placeholder
        "message": "YouTube connection status check"
    }
