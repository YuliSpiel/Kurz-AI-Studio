"""
Pydantic schemas for User-related requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserRegister(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """로그인 응답 (JWT 토큰)"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: UUID
    email: str
    username: str
    credits: int
    subscription_tier: str
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
