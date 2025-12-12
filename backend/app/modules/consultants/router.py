"""
Consultants Router

API endpoints for consultant profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

from app.core.models import User, UserRole
from app.core.auth import get_current_user, require_recruiter_or_admin
from app.core.config import settings
from app.modules.consultants.repository import ConsultantRepository
from app.modules.consultants.models import ConsultantProfile, ConsultantProfileUpdate
from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.models import SubmissionStatus

router = APIRouter(prefix="/consultants", tags=["consultants"])
repo = ConsultantRepository()
submission_repo = SubmissionRepository()
logger = logging.getLogger(__name__)

RESUME_UPLOAD_DIR = Path("uploads/resumes")
RESUME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/me", response_model=ConsultantProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current consultant's profile"""
    if current_user.role != UserRole.CONSULTANT:
        raise HTTPException(status_code=403, detail="Only consultants have profiles")
        
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return await repo.create_or_update(current_user.id, ConsultantProfileUpdate(experience_years=0))
    return profile

@router.put("/me", response_model=ConsultantProfile)
async def update_my_profile(
    profile_data: ConsultantProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current consultant's profile"""
    if current_user.role != UserRole.CONSULTANT:
        raise HTTPException(status_code=403, detail="Only consultants can update their profile")
        
    return await repo.create_or_update(current_user.id, profile_data)

@router.get("/", response_model=List[ConsultantProfile])
async def get_all_consultants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """
    Get consultants.
    - If ADMIN: Returns all consultants.
    - If RECRUITER: Returns ALL consultants (not filtered by applications).
    - Submissions tab shows only consultants who have applied to recruiter's jobs.
    """
    return await repo.get_all(skip, limit, user_ids=None)

@router.get("/{user_id}/resume")
async def download_consultant_resume(
    user_id: str,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """Download consultant's resume (Recruiter/Admin only)"""
    profile = await repo.get_by_user_id(user_id)
    if not profile or not profile.resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_path = Path(profile.resume_path)
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found on server")
    
    return FileResponse(
        path=str(resume_path),
        filename=resume_path.name,
        media_type="application/pdf" if resume_path.suffix == ".pdf" else "application/octet-stream"
    )

@router.get("/{user_id}", response_model=ConsultantProfile)
async def get_consultant_profile(
    user_id: str,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """Get specific consultant profile (Recruiter only)"""
    profile = await repo.get_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Consultant profile not found")
    return profile

@router.post("/me/resume")
async def upload_resume(
    resume: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload resume for consultant profile"""
    if current_user.role != UserRole.CONSULTANT:
        raise HTTPException(status_code=403, detail="Only consultants can upload resumes")
    
    # Validate file extension
    file_ext = os.path.splitext(resume.filename)[1].lower()
    if file_ext not in settings.ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_RESUME_EXTENSIONS)}"
        )
    
    # Validate file size
    file_content = await resume.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {max_size_mb}MB"
        )
    
    try:
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user.id}_resume_{timestamp}{file_ext}"
        file_path = RESUME_UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Get existing profile to check for old resume
        profile = await repo.get_by_user_id(current_user.id)
        old_resume_path = None
        if profile and profile.resume_path:
            old_resume_path = Path(profile.resume_path)
        
        # Update profile with new resume path
        update_data = ConsultantProfileUpdate(resume_path=str(file_path))
        updated_profile = await repo.create_or_update(current_user.id, update_data)
        
        # Delete old resume if it exists and is different
        if old_resume_path and old_resume_path.exists() and old_resume_path != file_path:
            try:
                old_resume_path.unlink()
                logger.info(f"Deleted old resume: {old_resume_path}")
            except Exception as e:
                logger.warning(f"Could not delete old resume: {str(e)}")
        
        return {
            "message": "Resume uploaded successfully",
            "filename": filename,
            "resume_path": str(file_path)
        }
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")

@router.get("/me/resume")
async def download_resume(
    current_user: User = Depends(get_current_user)
):
    """Download consultant's resume"""
    if current_user.role != UserRole.CONSULTANT:
        raise HTTPException(status_code=403, detail="Only consultants can download their resumes")
    
    profile = await repo.get_by_user_id(current_user.id)
    if not profile or not profile.resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_path = Path(profile.resume_path)
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found on server")
    
    return FileResponse(
        path=str(resume_path),
        filename=resume_path.name,
        media_type="application/pdf" if resume_path.suffix == ".pdf" else "application/octet-stream"
    )

@router.get("/me/stats")
async def get_application_stats(
    current_user: User = Depends(get_current_user)
):
    """Get application statistics for consultant"""
    if current_user.role != UserRole.CONSULTANT:
        raise HTTPException(status_code=403, detail="Only consultants can view their statistics")
    
    try:
        # Get all submissions for this consultant
        submissions = await submission_repo.get_by_consultant(current_user.id)
        
        # Calculate statistics
        total = len(submissions)
        stats_by_status = {}
        for status in SubmissionStatus:
            stats_by_status[status.value] = sum(1 for s in submissions if s.status == status)
        
        pending = stats_by_status.get(SubmissionStatus.SUBMITTED.value, 0) + stats_by_status.get(SubmissionStatus.ON_HOLD.value, 0)
        interviews = stats_by_status.get(SubmissionStatus.INTERVIEW.value, 0)
        offers = stats_by_status.get(SubmissionStatus.OFFER.value, 0)
        joined = stats_by_status.get(SubmissionStatus.JOINED.value, 0)
        rejected = stats_by_status.get(SubmissionStatus.REJECTED.value, 0)
        withdrawn = stats_by_status.get(SubmissionStatus.WITHDRAWN.value, 0)
        
        # Calculate success rate
        success_count = joined + offers
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_submissions = []
        for s in submissions:
            if s.created_at:
                if isinstance(s.created_at, datetime):
                    created_dt = s.created_at
                else:
                    try:
                        created_dt = datetime.fromisoformat(str(s.created_at).replace('Z', '+00:00'))
                    except:
                        continue
                if created_dt >= thirty_days_ago:
                    recent_submissions.append(s)
        recent_count = len(recent_submissions)
        
        return {
            "total": total,
            "pending": pending,
            "interviews": interviews,
            "offers": offers,
            "joined": joined,
            "rejected": rejected,
            "withdrawn": withdrawn,
            "success_rate": round(success_rate, 2),
            "recent_30_days": recent_count,
            "by_status": stats_by_status
        }
    except Exception as e:
        logger.error(f"Error getting application stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

