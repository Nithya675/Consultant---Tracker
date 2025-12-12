"""
Consultants Module

Handles consultant profile management, resume uploads, and statistics.
"""

from app.modules.consultants.module import ConsultantsModule

# Auto-register module when this package is imported
from app.modules import register_module
register_module(ConsultantsModule)

__all__ = ["ConsultantsModule"]

