"""
Submissions Module
"""

from app.modules.submissions.module import SubmissionsModule
from app.modules import register_module
register_module(SubmissionsModule)

__all__ = ["SubmissionsModule"]

