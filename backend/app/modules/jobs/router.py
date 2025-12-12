<<<<<<< HEAD:backend/app/routers/jobs.py
<<<<<<< Updated upstream:backend/app/routers/jobs.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models import User, UserRole, JobDescription, JobDescriptionCreate, JobDescriptionUpdate
from app.auth import get_current_user, require_recruiter_or_admin
from app.repositories.jobs import JobRepository
=======
"""
Jobs Router
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
import logging
import os
from pathlib import Path
from datetime import datetime

from app.core.models import User, UserRole
from app.core.auth import get_current_user, require_recruiter_or_admin
from app.core.ai_service import classify_job_description, is_ai_service_available
from app.core.config import settings
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.models import (
    JobDescription, 
    JobDescriptionCreate, 
    JobDescriptionUpdate,
    JobDescriptionTextInput
)

logger = logging.getLogger(__name__)
>>>>>>> Stashed changes:backend/app/modules/jobs/router.py
=======
"""
Jobs Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.core.models import User, UserRole
from app.core.auth import get_current_user, require_recruiter_or_admin
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.models import JobDescription, JobDescriptionCreate, JobDescriptionUpdate
>>>>>>> 165a09aafc044fb205820c09af4cee688e1d0c9d:backend/app/modules/jobs/router.py

router = APIRouter(prefix="/jobs", tags=["jobs"])
repo = JobRepository()

@router.get("/", response_model=List[JobDescription])
async def get_jobs(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all JDs. Consultants see only OPEN, Recruiters see all."""
    if current_user.role == UserRole.CONSULTANT:
        return await repo.get_all(status="OPEN")
    return await repo.get_all(status=status)

@router.post("/classify", response_model=JobDescriptionCreate)
async def classify_jd(
    jd_input: JobDescriptionTextInput,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """
    Classify JD text using AI and return structured data.
    
    This endpoint uses Google Gemini API to extract structured fields
    from raw job description text. The recruiter can then review and
    edit the classified data before creating the job.
    """
    if not is_ai_service_available():
        raise HTTPException(
            status_code=503,
            detail="AI classification service is not available. Please configure GEMINI_API_KEY."
        )
    
    try:
        logger.info(f"Classifying JD text for user: {current_user.email}")
        classified_data = classify_job_description(jd_input.text)
        
        # Convert to JobDescriptionCreate model
        # Handle date parsing if present
        start_date = None
        if classified_data.get("start_date"):
            try:
                from datetime import datetime
                start_date = datetime.fromisoformat(classified_data["start_date"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse start_date: {classified_data.get('start_date')}")
        
        # Handle job_type enum conversion
        job_type = None
        if classified_data.get("job_type"):
            from app.modules.jobs.models import JobType
            job_type_str = classified_data["job_type"]
            # Try to match enum values
            for jt in JobType:
                if jt.value.lower() == job_type_str.lower():
                    job_type = jt
                    break
        
        jd_create = JobDescriptionCreate(
            title=classified_data["title"],
            description=classified_data.get("description", jd_input.text),
            client_name=classified_data.get("client_name"),
            experience_required=classified_data.get("experience_required", 0),
            tech_required=classified_data.get("tech_required", []),
            location=classified_data.get("location"),
            visa_required=classified_data.get("visa_required"),
            start_date=start_date,
            job_type=job_type,
            jd_summary=classified_data.get("jd_summary"),
            additional_notes=classified_data.get("additional_notes"),
            status="OPEN"
        )
        
        logger.info(f"Successfully classified JD: {jd_create.title}")
        return jd_create
        
    except ValueError as e:
        logger.error(f"Error classifying JD: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to classify job description: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error classifying JD: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while classifying the job description. Please try again or enter the details manually."
        )

@router.post("/", response_model=JobDescription)
async def create_job(
    jd_data: JobDescriptionCreate,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """Create a new JD (Recruiter only)"""
    return await repo.create(jd_data, current_user.id)

@router.get("/{jd_id}", response_model=JobDescription)
async def get_job(
    jd_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get JD details"""
    jd = await repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    return jd

@router.put("/{jd_id}", response_model=JobDescription)
async def update_job(
    jd_id: str,
    jd_data: JobDescriptionUpdate,
    current_user: User = Depends(require_recruiter_or_admin)
):
    """Update JD (Recruiter only)"""
    try:
        updated_jd = await repo.update(jd_id, jd_data, current_user.id)
        if not updated_jd:
            raise HTTPException(status_code=404, detail="Job not found or unauthorized")
        return updated_jd
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
<<<<<<< HEAD:backend/app/routers/jobs.py
<<<<<<< Updated upstream:backend/app/routers/jobs.py
=======

@router.post("/{jd_id}/upload-jd-file")
async def upload_jd_file(
    jd_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_recruiter_or_admin)
):
    """
    Upload JD file (PDF/DOC) for a job description.
    
    The file will be saved to uploads/job_descriptions/ directory
    and the job description will be updated with the file URL.
    """
    # Verify job exists and user has permission
    jd = await repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if str(jd.recruiter_id) != str(current_user.id) and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You can only upload files for your own jobs")
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_JD_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_JD_FILE_EXTENSIONS)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {max_size_mb}MB"
            )
        
        # Create upload directory if it doesn't exist
        jd_upload_dir = Path(settings.UPLOAD_DIR) / "job_descriptions"
        jd_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{jd_id}_{timestamp}{file_ext}"
        file_path = jd_upload_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.info(f"JD file uploaded: {file_path} for job {jd_id}")
        
        # Get old file path if exists
        old_file_path = None
        if jd.jd_file_url:
            old_file_path = Path(jd.jd_file_url)
        
        # Update job with new file URL
        update_data = JobDescriptionUpdate(jd_file_url=str(file_path))
        updated_jd = await repo.update(jd_id, update_data, current_user.id)
        
        # Delete old file if it exists and is different
        if old_file_path and old_file_path.exists() and old_file_path != file_path:
            try:
                old_file_path.unlink()
                logger.info(f"Deleted old JD file: {old_file_path}")
            except Exception as e:
                logger.warning(f"Could not delete old JD file: {str(e)}")
        
        return {
            "message": "JD file uploaded successfully",
            "filename": filename,
            "jd_file_url": str(file_path),
            "job": updated_jd
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading JD file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading JD file: {str(e)}")

@router.get("/{jd_id}/download-jd-file")
async def download_jd_file(
    jd_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download JD file for a job description"""
    jd = await repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not jd.jd_file_url:
        raise HTTPException(status_code=404, detail="JD file not found for this job")
    
    file_path = Path(jd.jd_file_url)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="JD file not found on server")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/pdf" if file_path.suffix == ".pdf" else "application/octet-stream"
    )

>>>>>>> Stashed changes:backend/app/modules/jobs/router.py
=======

>>>>>>> 165a09aafc044fb205820c09af4cee688e1d0c9d:backend/app/modules/jobs/router.py
