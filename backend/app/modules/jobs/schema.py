"""
Jobs Module Schema
"""

from pymongo.errors import PyMongoError
import logging
from app.core.schemas import CollectionSchema

logger = logging.getLogger(__name__)

class JobsSchema(CollectionSchema):
    @staticmethod
    def get_collection_name() -> str:
        return "job_descriptions"
    
    @staticmethod
    async def create_indexes(db) -> None:
        collection_name = JobsSchema.get_collection_name()
        logger.info(f"Creating indexes for collection: {collection_name}")
        
        try:
<<<<<<< HEAD
            # Existing indexes
            await db.job_descriptions.create_index("recruiter_id")
            await db.job_descriptions.create_index("status")
            
            # New indexes for filtering and sorting
            await db.job_descriptions.create_index("client_name")
            await db.job_descriptions.create_index("job_type")
            await db.job_descriptions.create_index("start_date")
            
            # Compound index for common queries
            await db.job_descriptions.create_index([("status", 1), ("job_type", 1)])
            
=======
            await db.job_descriptions.create_index("recruiter_id")
            await db.job_descriptions.create_index("status")
>>>>>>> 165a09aafc044fb205820c09af4cee688e1d0c9d
            logger.info(f"All indexes created successfully for {collection_name}")
        except Exception as e:
            logger.error(f"Error creating indexes for {collection_name}: {str(e)}", exc_info=True)
            raise

