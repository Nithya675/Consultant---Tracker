"""
Recruiters Module
"""

from app.modules.recruiters.module import RecruitersModule
from app.modules import register_module
register_module(RecruitersModule)

__all__ = ["RecruitersModule"]

