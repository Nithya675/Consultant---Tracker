"""
Submissions Router
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import shutil
import logging
from pathlib import Path

from app.core.models import User, UserRole
from app.core.auth import get_current_user, require_recruiter_or_admin, require_role
from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.models import Submission, SubmissionCreate, SubmissionUpdate, SubmissionStatus
from app.modules.jobs.repository import JobRepository
from app.modules.consultants.repository import ConsultantRepository
from app.modules.consultants.models import ConsultantProfileUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["submissions"])
repo = SubmissionRepository()
job_repo = JobRepository()
consultant_repo = ConsultantRepository()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/", response_model=Submission)
async def create_submission(
    jd_id: str = Form(...),
    comments: Optional[str] = Form(None),
    resume: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.CONSULTANT))
):
    """Submit an application (Consultant only)"""
    jd = await job_repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if jd.status != "OPEN":
        raise HTTPException(status_code=400, detail="Job is not open for applications")

    try:
        profile = await consultant_repo.get_by_user_id(current_user.id)
        if not profile:
            await consultant_repo.create_or_update(
                current_user.id, 
                ConsultantProfileUpdate(experience_years=0.0)
            )
    except Exception as e:
        logger.warning(f"Could not ensure consultant profile exists: {str(e)}")
    
    try:
        import os
        file_ext = os.path.splitext(resume.filename)[1]
        filename = f"{current_user.id}_{jd_id}_{os.urandom(4).hex()}{file_ext}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
            
        submission_data = SubmissionCreate(jd_id=jd_id, comments=comments)
        return await repo.create(submission_data, current_user.id, jd.recruiter_id, str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing submission: {str(e)}")

@router.get("/me", response_model=List[Submission])
async def get_my_submissions(current_user: User = Depends(require_role(UserRole.CONSULTANT))):
    """Get my submissions (Consultant only)"""
    return await repo.get_by_consultant(current_user.id)

@router.get("/", response_model=List[Submission])
async def get_all_submissions(
    current_user: User = Depends(require_recruiter_or_admin)
):
    """Get all submissions (Recruiter only)"""
    if current_user.role == UserRole.RECRUITER:
        return await repo.get_all(recruiter_id=current_user.id)
    return await repo.get_all() 

@router.put("/{submission_id}/status", response_model=Submission)
async def update_submission_status(
    submission_id: str,
    status_update: SubmissionUpdate,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """Update submission status (Recruiter only)"""
    if not status_update.status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return await repo.update_status(submission_id, status_update.status, current_user.id)

