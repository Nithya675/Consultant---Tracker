"""
Recruiters Router
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.models import User, UserRole
from app.core.auth import get_current_user
from app.modules.recruiters.repository import RecruiterRepository
from app.modules.recruiters.models import RecruiterProfile, RecruiterProfileUpdate

router = APIRouter(prefix="/recruiters", tags=["recruiters"])
repo = RecruiterRepository()

@router.get("/me", response_model=RecruiterProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current recruiter's profile"""
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=403, detail="Only recruiters have profiles")
    
    profile = await repo.get_profile_by_user_id(current_user.id)
    if not profile:
        return RecruiterProfile(
            id=current_user.id,
            user_id=current_user.id,
            email=current_user.email,
            name=current_user.name
        )
    return profile

@router.put("/me", response_model=RecruiterProfile)
async def update_my_profile(
    profile_data: RecruiterProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current recruiter's profile"""
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=403, detail="Only recruiters can update their profile")
    
    return await repo.update_profile(current_user.id, profile_data)

