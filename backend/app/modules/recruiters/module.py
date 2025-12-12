"""
Recruiters Module
"""

from app.modules import BaseModule
from app.modules.recruiters.router import router
from typing import List

class RecruitersModule(BaseModule):
    def get_router(self):
        return router
    
    def get_module_name(self) -> str:
        return "recruiters"
    
    def get_prefix(self) -> str:
        return "/recruiters"
    
    def get_tags(self) -> List[str]:
        return ["recruiters"]

