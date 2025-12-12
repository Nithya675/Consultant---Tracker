"""
Submissions Module Schema
"""

from pymongo.errors import PyMongoError
import logging
from app.core.schemas import CollectionSchema

logger = logging.getLogger(__name__)

class SubmissionsSchema(CollectionSchema):
    @staticmethod
    def get_collection_name() -> str:
        return "submissions"
    
    @staticmethod
    async def create_indexes(db) -> None:
        collection_name = SubmissionsSchema.get_collection_name()
        logger.info(f"Creating indexes for collection: {collection_name}")
        
        try:
            await db.submissions.create_index("consultant_id")
            await db.submissions.create_index("recruiter_id")
            await db.submissions.create_index("jd_id")
            await db.submissions.create_index("status")
            logger.info(f"All indexes created successfully for {collection_name}")
        except Exception as e:
            logger.error(f"Error creating indexes for {collection_name}: {str(e)}", exc_info=True)
            raise

