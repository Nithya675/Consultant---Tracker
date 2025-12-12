"""
Consultants Module

This module handles consultant profile management.
"""

from app.modules import BaseModule
from app.modules.consultants.router import router
from typing import List

class ConsultantsModule(BaseModule):
    """Consultants module implementation"""
    
    def get_router(self):
        """Return the FastAPI router for consultant endpoints"""
        return router
    
    def get_module_name(self) -> str:
        """Return the module name"""
        return "consultants"
    
    def get_prefix(self) -> str:
        """Return the API prefix"""
        return "/consultants"
    
    def get_tags(self) -> List[str]:
        """Return OpenAPI tags"""
        return ["consultants"]

