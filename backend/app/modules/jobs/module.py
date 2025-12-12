"""
Jobs Module
"""

from app.modules import BaseModule
from app.modules.jobs.router import router
from typing import List

class JobsModule(BaseModule):
    def get_router(self):
        return router
    
    def get_module_name(self) -> str:
        return "jobs"
    
    def get_prefix(self) -> str:
        return "/jobs"
    
    def get_tags(self) -> List[str]:
        return ["jobs"]

