"""
Authentication Module

This module handles:
- User registration (Admin, Recruiter, Consultant)
- User authentication (login)
- Token management (refresh, logout)
- User management (admin endpoints)
"""

from app.modules import BaseModule
from app.modules.auth.router import router
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import AuthSchema
from typing import List

class AuthModule(BaseModule):
    """Authentication module implementation"""
    
    def __init__(self):
        self._repository = AuthRepository()
        self._schema = AuthSchema()
    
    def get_router(self):
        """Return the FastAPI router for authentication endpoints"""
        return router
    
    def get_module_name(self) -> str:
        """Return the module name"""
        return "auth"
    
    def get_prefix(self) -> str:
        """Return the API prefix"""
        return "/auth"
    
    def get_tags(self) -> List[str]:
        """Return OpenAPI tags"""
        return ["authentication"]
    
    @property
    def repository(self):
        """Return the repository instance"""
        return self._repository
    
    @property
    def schema(self):
        """Return the schema instance"""
        return self._schema

