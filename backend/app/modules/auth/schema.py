"""
Authentication Module Schema

MongoDB collection schemas for user collections.
User account schemas are defined in user_schemas/ subdirectory.
This schema acts as a placeholder for the auth module.
"""

from app.core.schemas import CollectionSchema
from typing import Optional

# Note: User collections (admins, recruiters, consultants) have their schemas
# in app.modules.auth.user_schemas/ subdirectory.
# The actual schemas are:
# - app.modules.auth.user_schemas.admins.AdminsSchema
# - app.modules.auth.user_schemas.recruiters.RecruitersSchema
# - app.modules.auth.user_schemas.consultants_user.ConsultantsUserSchema

class AuthSchema(CollectionSchema):
    """
    Placeholder schema for the auth module.
    
    Actual user collection schemas are registered separately in schema_registry.
    This schema exists to satisfy the BaseModule interface.
    """
    
    @staticmethod
    def get_collection_name():
        """Return a placeholder collection name"""
        return "auth_users"  # Not actually used
    
    @staticmethod
    async def create_indexes(db):
        """
        Indexes are created by role-specific schemas in user_schemas/.
        This method does nothing as indexes are handled by individual user schemas.
        """
        pass

