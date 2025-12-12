"""
Jobs Module Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    """Job type enumeration"""
    CONTRACT = "Contract"
    FULL_TIME = "Full-time"
    C2C = "C2C"
    W2 = "W2"

class JobDescriptionBase(BaseModel):
    # Core fields
    title: str = Field(..., min_length=1, description="Job Title")
    description: str = Field(..., description="Full job description text")
    
    # New required fields
    client_name: Optional[str] = Field(None, description="Client/Company Name")
    experience_required: float = Field(..., ge=0, description="Required Experience (Years)")
    tech_required: List[str] = Field(default_factory=list, description="Required Tech Stack/Skills")
    location: Optional[str] = Field(None, description="Location")
    visa_required: Optional[str] = Field(None, description="Visa Requirements")
    start_date: Optional[datetime] = Field(None, description="Start Date/Availability")
    job_type: Optional[JobType] = Field(None, description="Job Type (Contract/Full-time/C2C/W2)")
    jd_summary: Optional[str] = Field(None, description="JD Summary/Description")
    additional_notes: Optional[str] = Field(None, description="Additional Notes")
    jd_file_url: Optional[str] = Field(None, description="JD File Upload URL/path")
    
    # Legacy field (kept for backward compatibility)
    notes: Optional[str] = Field(None, description="Legacy notes field")
    
    # Status
    status: str = Field(default="OPEN", description="Job status: OPEN or CLOSED")

class JobDescriptionCreate(JobDescriptionBase):
    pass

class JobDescriptionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    experience_required: Optional[float] = None
    tech_required: Optional[List[str]] = None
    location: Optional[str] = None
    visa_required: Optional[str] = None
    start_date: Optional[datetime] = None
    job_type: Optional[JobType] = None
    jd_summary: Optional[str] = None
    additional_notes: Optional[str] = None
    jd_file_url: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class JobDescriptionTextInput(BaseModel):
    """Input model for JD text classification"""
    text: str = Field(..., min_length=10, description="Raw job description text to classify")

class JobDescription(JobDescriptionBase):
    id: str
    recruiter_id: str
    created_at: datetime
    updated_at: datetime
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    
    class Config:
        from_attributes = True

__all__ = [
    "JobType",
    "JobDescriptionBase",
    "JobDescriptionCreate",
    "JobDescriptionUpdate",
    "JobDescription",
    "JobDescriptionTextInput",
]

