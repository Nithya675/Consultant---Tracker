"""
Authentication Repository

Database operations for user management.
Handles users across different collections (admins, recruiters, consultants).
"""

from typing import List, Optional
import logging
from app.core.db import get_database
from app.core.models import User, UserCreate, UserRole, UserResponse
from app.core.auth import get_password_hash
from app.modules.auth.user_repositories import (
    RecruiterRepository,
    ConsultantUserRepository,
    AdminRepository
)

logger = logging.getLogger(__name__)

class AuthRepository:
    """Repository for authentication and user management"""
    
    def __init__(self):
        self.recruiter_repo = RecruiterRepository()
        self.consultant_repo = ConsultantUserRepository()
        self.admin_repo = AdminRepository()
        logger.debug("AuthRepository initialized")
    
    def _get_repository_by_role(self, role: UserRole):
        """Get the appropriate repository based on role"""
        if role == UserRole.RECRUITER:
            return self.recruiter_repo
        elif role == UserRole.CONSULTANT:
            return self.consultant_repo
        elif role == UserRole.ADMIN:
            return self.admin_repo
        else:
            raise ValueError(f"Unknown role: {role}")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user in the appropriate collection"""
        logger.debug(f"Creating user: {user_data.email}, role: {user_data.role}")
        
        repo = self._get_repository_by_role(user_data.role)
        user = await repo.create(user_data)
        
        logger.info(f"User created successfully: {user.email}, ID: {user.id}")
        return user
    
    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None
    ) -> List[User]:
        """Get all users, optionally filtered by role"""
        logger.debug(f"Getting all users - skip: {skip}, limit: {limit}, role: {role}")
        
        if role:
            # Get users from specific role repository
            repo = self._get_repository_by_role(role)
            users = await repo.get_all(skip=skip, limit=limit)
        else:
            # Get users from all repositories
            all_users = []
            for user_role in [UserRole.RECRUITER, UserRole.CONSULTANT, UserRole.ADMIN]:
                repo = self._get_repository_by_role(user_role)
                role_users = await repo.get_all(skip=0, limit=1000)  # Get all, then paginate
                all_users.extend(role_users)
            # Simple pagination
            users = all_users[skip:skip+limit]
        
        logger.info(f"Retrieved {len(users)} users")
        return users

