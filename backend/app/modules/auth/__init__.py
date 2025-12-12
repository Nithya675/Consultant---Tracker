"""
Authentication Module

Handles user authentication, registration, and token management.
Supports multiple user types: Admin, Recruiter, Consultant.
"""

from app.modules.auth.module import AuthModule

# Auto-register module when this package is imported
from app.modules import register_module
register_module(AuthModule)

__all__ = ["AuthModule"]

