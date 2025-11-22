"""
Authentication endpoints: register, login, and Google OAuth.
"""
import logging
import httpx
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.utils.security import hash_password, verify_password
from app.utils.auth import create_access_token, get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    회원가입

    - **email**: 이메일 (중복 불가)
    - **username**: 사용자명 (중복 불가)
    - **password**: 비밀번호 (6자 이상)
    """
    # 1. 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2. 사용자명 중복 확인
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # 3. 사용자 생성
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        credits=0,  # 초기 크레딧 0
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    로그인

    - **email**: 이메일
    - **password**: 비밀번호

    Returns JWT access token.
    """
    # 1. 사용자 조회
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()

    # 2. 사용자 없거나 비밀번호 틀림
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. JWT 토큰 발급
    access_token = create_access_token(str(user.id), user.username)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


# =============================================================================
# Google OAuth Endpoints
# =============================================================================

@router.get("/google/login")
async def google_login():
    """
    Google OAuth 로그인 시작 - Google 인증 페이지로 리다이렉트
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Google OAuth 콜백 - 인증 코드를 받아 토큰 교환 후 로그인/회원가입 처리
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    try:
        # 1. Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }
            )

            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            # 2. Get user info from Google
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if userinfo_response.status_code != 200:
                logger.error(f"Failed to get user info: {userinfo_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Google"
                )

            google_user = userinfo_response.json()

        google_id = google_user.get("id")
        email = google_user.get("email")
        name = google_user.get("name", email.split("@")[0])
        picture = google_user.get("picture")

        logger.info(f"[OAUTH] Google user: {email} (id: {google_id})")

        # 3. Find or create user
        # Check by google_id first
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalars().first()

        if not user:
            # Check by email (existing user linking)
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()

            if user:
                # Link existing account with Google
                user.google_id = google_id
                user.profile_image = picture
                await db.commit()
                await db.refresh(user)
                logger.info(f"[OAUTH] Linked Google to existing user: {email}")
            else:
                # Create new user
                # Generate unique username from email
                base_username = email.split("@")[0]
                username = base_username
                counter = 1

                while True:
                    result = await db.execute(select(User).where(User.username == username))
                    if not result.scalars().first():
                        break
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User(
                    email=email,
                    username=username,
                    google_id=google_id,
                    profile_image=picture,
                    hashed_password=None,  # OAuth user, no password
                    credits=3,  # Welcome credits for new users
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"[OAUTH] Created new user via Google: {email}")

        # 4. Generate JWT token
        jwt_token = create_access_token(str(user.id), user.username)

        # 5. Redirect to frontend with token
        frontend_url = settings.FRONTEND_ORIGIN
        redirect_url = f"{frontend_url}/auth/callback?token={jwt_token}"

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OAUTH] Google OAuth error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return current_user
