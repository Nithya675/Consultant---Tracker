"""
Consultants Module Models

Pydantic models for consultant profiles.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.core.models import UserRole

class ConsultantProfileBase(BaseModel):
    experience_years: float = Field(..., ge=0)
    tech_stack: List[str] = []
    available: bool = True
    location: Optional[str] = None
    visa_status: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None
    professional_summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    education: Optional[Dict] = None  # {degree, university, graduation_year}
    certifications: List[str] = []
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    tech_stack_proficiency: Optional[Dict[str, str]] = None  # {skill: proficiency_level}

class ConsultantProfileCreate(ConsultantProfileBase):
    pass

class ConsultantProfileUpdate(BaseModel):
    experience_years: Optional[float] = Field(None, ge=0)
    tech_stack: Optional[List[str]] = None
    available: Optional[bool] = None
    location: Optional[str] = None
    visa_status: Optional[str] = None
    notes: Optional[str] = None
    professional_summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    education: Optional[Dict] = None
    certifications: Optional[List[str]] = None
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    tech_stack_proficiency: Optional[Dict[str, str]] = None

class ConsultantProfile(ConsultantProfileBase):
    id: str
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        from_attributes = True

__all__ = [
    "ConsultantProfileBase",
    "ConsultantProfileCreate",
    "ConsultantProfileUpdate",
    "ConsultantProfile",
]

