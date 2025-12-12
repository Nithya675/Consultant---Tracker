"""
Authentication Module Models

Module-specific models for authentication.
Shared models (User, Token, etc.) are in app.core.models
"""

# All models are in app.core.models for now
# This file is here for future module-specific models

from app.core.models import (
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    TokenData,
    UserRole,
)

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    "UserRole",
]

