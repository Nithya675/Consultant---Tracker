"""
Submissions Module
"""

from app.modules import BaseModule
from app.modules.submissions.router import router
from typing import List

class SubmissionsModule(BaseModule):
    def get_router(self):
        return router
    
    def get_module_name(self) -> str:
        return "submissions"
    
    def get_prefix(self) -> str:
        return "/submissions"
    
    def get_tags(self) -> List[str]:
        return ["submissions"]

