"""
Recruiters Module Schema
"""

from pymongo.errors import PyMongoError
import logging
from app.core.schemas import CollectionSchema

logger = logging.getLogger(__name__)

class RecruitersSchema(CollectionSchema):
    @staticmethod
    def get_collection_name() -> str:
        return "recruiter_profiles"
    
    @staticmethod
    async def create_indexes(db) -> None:
        collection_name = RecruitersSchema.get_collection_name()
        logger.info(f"Creating indexes for collection: {collection_name}")
        
        try:
            await db.recruiter_profiles.create_index("recruiter_id", unique=True)
            logger.info(f"All indexes created successfully for {collection_name}")
        except Exception as e:
            logger.error(f"Error creating indexes for {collection_name}: {str(e)}", exc_info=True)
            raise

