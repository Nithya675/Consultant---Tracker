"""
Consultants Repository

Database operations for consultant profiles.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import logging
from app.core.db import get_database
from app.modules.consultants.models import ConsultantProfile, ConsultantProfileUpdate

logger = logging.getLogger(__name__)

class ConsultantRepository:
    """Repository for consultant profile operations"""
    
    def __init__(self):
        self.collection_name = "consultant_profiles"
        logger.debug("ConsultantRepository initialized")

    async def _merge_user_data(self, profile_doc, db):
        """Helper to fetch and merge user details into profile, handling data integrity"""
        try:
            if "tech_stack" not in profile_doc or profile_doc["tech_stack"] is None:
                profile_doc["tech_stack"] = []
            if "experience_years" not in profile_doc or profile_doc["experience_years"] is None:
                profile_doc["experience_years"] = 0.0

            consultant_id = profile_doc.get("consultant_id")
            if not consultant_id:
                logger.warning(f"Profile {profile_doc.get('_id')} has no consultant_id")
                profile_doc["name"] = "Unknown User"
                profile_doc["email"] = "N/A"
                return profile_doc

            try:
                oid = ObjectId(consultant_id)
            except (InvalidId, TypeError):
                logger.error(f"Invalid consultant_id format: {consultant_id}")
                profile_doc["name"] = "Invalid ID"
                return profile_doc

            # Look up consultant user in consultants collection
            user_data = await db.consultants.find_one({"_id": oid})

            if user_data:
                profile_doc["email"] = user_data.get("email", "")
                profile_doc["name"] = user_data.get("name", "Unknown")
                profile_doc["phone"] = user_data.get("phone", "")
            else:
                logger.warning(f"User not found for profile: {consultant_id}")
                profile_doc["name"] = "Unknown User"
                profile_doc["email"] = "N/A"

        except Exception as e:
            logger.error(f"Error merging user data: {e}")
            profile_doc["name"] = "Error Loading User"

        return profile_doc

    async def get_by_user_id(self, user_id: str) -> Optional[ConsultantProfile]:
        """Get consultant profile by consultant user ID"""
        logger.debug(f"Getting consultant profile for consultant ID: {user_id}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")

            profile_data = await db.consultant_profiles.find_one({"consultant_id": user_id})

            if profile_data:
                profile_data["id"] = str(profile_data["_id"])
                if "consultant_id" in profile_data:
                    profile_data["user_id"] = profile_data["consultant_id"]
                profile_data = await self._merge_user_data(profile_data, db)
                return ConsultantProfile(**profile_data)

            return None
        except Exception as e:
            logger.error(f"Error getting consultant profile: {str(e)}", exc_info=True)
            raise

    async def create_or_update(self, user_id: str, profile_data: ConsultantProfileUpdate) -> ConsultantProfile:
        """Create or update consultant profile"""
        logger.info(f"Updating consultant profile for consultant ID: {user_id}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")

            update_data = {k: v for k, v in profile_data.dict().items() if v is not None}

            # Handle phone update - also update in consultants user collection
            phone = update_data.pop("phone", None)
            if phone is not None:
                try:
                    oid = ObjectId(user_id)
                    await db.consultants.update_one(
                        {"_id": oid},
                        {"$set": {"phone": phone, "updated_at": datetime.utcnow()}}
                    )
                    logger.debug(f"Updated phone in consultants collection for user: {user_id}")
                except (InvalidId, TypeError) as e:
                    logger.warning(f"Could not update phone in consultants collection: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error updating phone in consultants collection: {str(e)}")

            update_data.pop("email", None)
            update_data["updated_at"] = datetime.utcnow()

            defaults = {
                "created_at": datetime.utcnow(),
                "consultant_id": user_id,
                "tech_stack": [],
                "experience_years": 0.0
            }

            if "experience_years" in update_data:
                defaults.pop("experience_years", None)
            
            if "tech_stack" in update_data:
                defaults.pop("tech_stack", None)

            await db.consultant_profiles.update_one(
                {"consultant_id": user_id},
                {
                    "$set": update_data,
                    "$setOnInsert": defaults
                },
                upsert=True
            )

            return await self.get_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Error updating consultant profile: {str(e)}", exc_info=True)
            raise

    async def get_all(self, skip: int = 0, limit: int = 100, user_ids: Optional[List[str]] = None) -> List[ConsultantProfile]:
        """Get all consultants (optionally filtered by specific user_ids)"""
        logger.debug(f"Getting consultants. Filter by IDs: {user_ids is not None}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            query = {}
            if user_ids is not None:
                query["consultant_id"] = {"$in": user_ids}
            
            cursor = db.consultant_profiles.find(query).skip(skip).limit(limit)
            profiles = []
            
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                if "consultant_id" in doc:
                    doc["user_id"] = doc["consultant_id"]
                doc = await self._merge_user_data(doc, db)
                profiles.append(ConsultantProfile(**doc))
                
            return profiles
        except Exception as e:
            logger.error(f"Error getting consultants: {str(e)}", exc_info=True)
            raise

