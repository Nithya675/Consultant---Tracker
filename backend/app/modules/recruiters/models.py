"""
Recruiters Module Models
"""

from pydantic import BaseModel, Field
from typing import Optional

class RecruiterProfileBase(BaseModel):
    company_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

class RecruiterProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

class RecruiterProfile(RecruiterProfileBase):
    id: str
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    
    class Config:
        from_attributes = True

__all__ = [
    "RecruiterProfileBase",
    "RecruiterProfileUpdate",
    "RecruiterProfile",
]

