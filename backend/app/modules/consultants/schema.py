"""
Consultants Module Schema

MongoDB collection schema for consultant_profiles.
"""

from pymongo.errors import PyMongoError
import logging
from app.core.schemas import CollectionSchema

logger = logging.getLogger(__name__)

class ConsultantsSchema(CollectionSchema):
    """
    Schema definition for the consultant_profiles collection.
    
    This is for consultant profiles (experience, tech stack, etc.), separate from consultant users.
    Consultant users are stored in the 'consultants' collection.
    
    Defines indexes for:
    - consultant_id: Unique index for fast lookups by consultant user ID (one-to-one relationship)
    """
    
    @staticmethod
    def get_collection_name() -> str:
        """Return the MongoDB collection name for consultant profiles"""
        return "consultant_profiles"
    
    @staticmethod
    async def create_indexes(db) -> None:
        """
        Create indexes for the consultant_profiles collection.
        
        Indexes:
        - consultant_id: Unique index for fast lookups by consultant user ID
        """
        collection_name = ConsultantsSchema.get_collection_name()
        logger.info(f"Creating indexes for collection: {collection_name}")
        
        try:
            # Create consultant_id index (unique) - one consultant profile per consultant user
            logger.debug(f"Creating consultant_id index (unique) for {collection_name}")
            try:
                result = await db.consultant_profiles.create_index("consultant_id", unique=True)
                logger.info(f"Consultant_id index created successfully for {collection_name}: {result}")
            except PyMongoError as e:
                # Index might already exist - check error
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.debug(f"Consultant_id index already exists for {collection_name} - skipping")
                else:
                    logger.error(f"Error creating consultant_id index for {collection_name}: {str(e)}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"Unexpected error creating consultant_id index for {collection_name}: {str(e)}", exc_info=True)
                raise
            
            logger.info(f"All indexes created successfully for {collection_name}")
            
        except Exception as e:
            logger.error(f"Error creating indexes for {collection_name}: {str(e)}", exc_info=True)
            raise

