"""
Submissions Module Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SubmissionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    JOINED = "JOINED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"
    WITHDRAWN = "WITHDRAWN"

class SubmissionBase(BaseModel):
    jd_id: str
    comments: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionUpdate(BaseModel):
    status: Optional[SubmissionStatus] = None
    comments: Optional[str] = None
    recruiter_read: Optional[bool] = None

class Submission(SubmissionBase):
    id: str
    consultant_id: str
    recruiter_id: str
    resume_path: str
    status: SubmissionStatus
    recruiter_read: bool = False
    created_at: datetime
    updated_at: datetime
    consultant_name: Optional[str] = None
    consultant_email: Optional[str] = None
    jd_title: Optional[str] = None
    jd_location: Optional[str] = None
    jd_experience_required: Optional[float] = None
    jd_tech_required: Optional[List[str]] = None
    jd_description: Optional[str] = None
    jd_recruiter_name: Optional[str] = None
    jd_recruiter_email: Optional[str] = None
    
    class Config:
        from_attributes = True

__all__ = [
    "SubmissionStatus",
    "SubmissionBase",
    "SubmissionCreate",
    "SubmissionUpdate",
    "Submission",
]

