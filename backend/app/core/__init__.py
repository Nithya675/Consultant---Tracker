"""
Core module - Shared utilities and infrastructure.

This module contains all shared functionality used across different modules:
- Configuration
- Database connection
- Authentication utilities
- Logging
- Common dependencies
"""

from app.core.config import settings
from app.core.db import get_database, init_db, close_db
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
    require_admin,
    require_recruiter_or_admin,
    require_consultant_or_admin,
    authenticate_user,
    get_user_by_email,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    security,
)
from app.core.logging_config import setup_logging
from app.core.schemas import CollectionSchema

# Schema registry imports are deferred to avoid circular imports
# Import directly from app.core.schema_registry when needed

__all__ = [
    "settings",
    "get_database",
    "init_db",
    "close_db",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "get_current_user",
    "require_role",
    "require_admin",
    "require_recruiter_or_admin",
    "require_consultant_or_admin",
    "authenticate_user",
    "get_user_by_email",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "security",
    "setup_logging",
    "CollectionSchema",
]

