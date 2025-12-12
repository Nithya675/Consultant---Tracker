"""
User Account Schemas

MongoDB schemas for user account collections.
These define indexes for: admins, consultants, recruiters.
"""

from app.modules.auth.user_schemas.admins import AdminsSchema
from app.modules.auth.user_schemas.consultants_user import ConsultantsUserSchema
from app.modules.auth.user_schemas.recruiters import RecruitersSchema

__all__ = [
    "AdminsSchema",
    "ConsultantsUserSchema",
    "RecruitersSchema",
]

