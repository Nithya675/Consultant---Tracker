"""
Recruiters Repository
"""

from typing import Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import logging
from app.core.db import get_database
from app.modules.recruiters.models import RecruiterProfile, RecruiterProfileUpdate

logger = logging.getLogger(__name__)

class RecruiterRepository:
    def __init__(self):
        self.collection_name = "recruiter_profiles"
        logger.debug("RecruiterRepository initialized")

    async def get_profile_by_user_id(self, user_id: str) -> Optional[RecruiterProfile]:
        """Get recruiter profile by user ID"""
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            profile_data = await db.recruiter_profiles.find_one({"recruiter_id": user_id})
            if profile_data:
                profile_data["id"] = str(profile_data["_id"])
                if "recruiter_id" in profile_data:
                    profile_data["user_id"] = profile_data["recruiter_id"]
                
                # Merge user data
                try:
                    user_data = await db.recruiters.find_one({"_id": ObjectId(user_id)})
                    if user_data:
                        profile_data["email"] = user_data.get("email", "")
                        profile_data["name"] = user_data.get("name", "Unknown")
                except (InvalidId, TypeError):
                    pass
                except Exception:
                    pass
                
                return RecruiterProfile(**profile_data)
            return None
        except Exception as e:
            logger.error(f"Error getting recruiter profile: {str(e)}", exc_info=True)
            raise

    async def update_profile(self, user_id: str, profile_data: RecruiterProfileUpdate) -> RecruiterProfile:
        """Update recruiter profile"""
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            defaults = {
                "created_at": datetime.utcnow(),
                "recruiter_id": user_id
            }
            
            await db.recruiter_profiles.update_one(
                {"recruiter_id": user_id},
                {
                    "$set": update_data,
                    "$setOnInsert": defaults
                },
                upsert=True
            )
            
            return await self.get_profile_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Error updating recruiter profile: {str(e)}", exc_info=True)
            raise

