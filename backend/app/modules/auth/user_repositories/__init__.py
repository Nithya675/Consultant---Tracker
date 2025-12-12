"""
User Account Repositories

Repositories for managing user accounts (authentication).
These handle the user account collections: admins, consultants, recruiters.
"""

from app.modules.auth.user_repositories.admins import AdminRepository
from app.modules.auth.user_repositories.consultants_user import ConsultantUserRepository
from app.modules.auth.user_repositories.recruiters import RecruiterRepository

__all__ = [
    "AdminRepository",
    "ConsultantUserRepository",
    "RecruiterRepository",
]

