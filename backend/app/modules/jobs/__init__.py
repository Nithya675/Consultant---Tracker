"""
Jobs Module
"""

from app.modules.jobs.module import JobsModule
from app.modules import register_module
register_module(JobsModule)

__all__ = ["JobsModule"]

