"""
JWT token creation and verification.
"""
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.user import User

# HTTPBearer scheme for extracting JWT from Authorization header
security = HTTPBearer()


def create_access_token(user_id: str, username: str) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User UUID as string
        username: Username for display

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,  # Subject (user ID)
        "username": username,
        "exp": expire  # Expiration time
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current authenticated user from JWT.

    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))
) -> User | None:
    """
    FastAPI dependency to get current user if authenticated, None otherwise.
    This allows endpoints to work both with and without authentication.

    Args:
        credentials: HTTP Authorization header with Bearer token (optional)
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    return user
