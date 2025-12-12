"""
Submissions Repository
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import logging
from app.core.db import get_database
from app.modules.submissions.models import Submission, SubmissionCreate, SubmissionStatus

logger = logging.getLogger(__name__)

class SubmissionRepository:
    def __init__(self):
        self.collection_name = "submissions"
        logger.debug("SubmissionRepository initialized")

    async def create(self, submission_data: SubmissionCreate, consultant_id: str, recruiter_id: str, resume_path: str) -> Submission:
        """Create a new submission"""
        logger.info(f"Creating new submission for JD: {submission_data.jd_id}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            doc = submission_data.dict()
            doc["consultant_id"] = consultant_id
            doc["recruiter_id"] = str(recruiter_id)
            doc["resume_path"] = resume_path
            doc["status"] = SubmissionStatus.SUBMITTED
            doc["recruiter_read"] = False
            doc["created_at"] = datetime.utcnow()
            doc["updated_at"] = datetime.utcnow()
            
            result = await db.submissions.insert_one(doc)
            doc["id"] = str(result.inserted_id)
            
            return Submission(**doc)
        except Exception as e:
            logger.error(f"Error creating submission: {str(e)}", exc_info=True)
            raise

    async def get_by_consultant(self, consultant_id: str) -> List[Submission]:
        """Get all submissions for a consultant"""
        logger.debug(f"Getting submissions for consultant: {consultant_id}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            cursor = db.submissions.find({"consultant_id": consultant_id}).sort("created_at", -1)
            submissions = []
            
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                try:
                    jd = await db.job_descriptions.find_one({"_id": ObjectId(doc["jd_id"])})
                    if jd:
                        doc["jd_title"] = jd.get("title", "Unknown Job")
                except (InvalidId, TypeError):
                    doc["jd_title"] = "Unknown Job"
                except Exception:
                    doc["jd_title"] = "Unknown Job"
                submissions.append(Submission(**doc))
                
            return submissions
        except Exception as e:
            logger.error(f"Error getting consultant submissions: {str(e)}", exc_info=True)
            raise

    async def get_all(self, recruiter_id: Optional[str] = None) -> List[Submission]:
        """Get all submissions"""
        logger.debug(f"Getting all submissions (recruiter_id: {recruiter_id})")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            query = {}
            if recruiter_id:
                query["recruiter_id"] = str(recruiter_id)
                
            cursor = db.submissions.find(query).sort("created_at", -1)
            submissions = []
            
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                try:
                    consultant_user = await db.consultants.find_one({"_id": ObjectId(doc["consultant_id"])})
                    if consultant_user:
                        doc["consultant_name"] = consultant_user.get("name", "Unknown")
                        doc["consultant_email"] = consultant_user.get("email", "")
                    else:
                        doc["consultant_name"] = "Unknown"
                        doc["consultant_email"] = ""
                except (InvalidId, TypeError):
                    doc["consultant_name"] = "Unknown"
                    doc["consultant_email"] = ""
                except Exception:
                    doc["consultant_name"] = "Unknown"
                    doc["consultant_email"] = ""
                
                try:
                    jd = await db.job_descriptions.find_one({"_id": ObjectId(doc["jd_id"])})
                    if jd:
                        doc["jd_title"] = jd.get("title", "Unknown")
                        doc["jd_location"] = jd.get("location")
                        doc["jd_experience_required"] = jd.get("experience_required")
                        doc["jd_tech_required"] = jd.get("tech_required", [])
                        doc["jd_description"] = jd.get("description")
                    else:
                        doc["jd_title"] = "Unknown"
                except (InvalidId, TypeError):
                    doc["jd_title"] = "Unknown"
                except Exception:
                    doc["jd_title"] = "Unknown"
                
                submissions.append(Submission(**doc))
                
            return submissions
        except Exception as e:
            logger.error(f"Error getting all submissions: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, submission_id: str) -> Optional[Submission]:
        """Get submission by ID"""
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            doc = await db.submissions.find_one({"_id": ObjectId(submission_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                return Submission(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting submission: {str(e)}", exc_info=True)
            raise

    async def update_status(self, submission_id: str, status: SubmissionStatus, recruiter_id: str) -> Submission:
        """Update submission status"""
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            
            await db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return await self.get_by_id(submission_id)
        except Exception as e:
            logger.error(f"Error updating submission status: {str(e)}", exc_info=True)
            raise

