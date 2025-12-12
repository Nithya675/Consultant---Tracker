from pymongo.errors import PyMongoError
import logging
from app.core.schemas import CollectionSchema

logger = logging.getLogger(__name__)


class AdminsSchema(CollectionSchema):
    """
    Schema definition for the admins collection.
    
    Defines indexes for:
    - email (unique) - for fast lookups and uniqueness constraint
    - is_active - for filtering active/inactive admins
    """
    
    @staticmethod
    def get_collection_name() -> str:
        """Return the MongoDB collection name for admins"""
        return "admins"
    
    @staticmethod
    async def create_indexes(db) -> None:
        """
        Create indexes for the admins collection.
        
        Indexes:
        - email: Unique index for email lookups and uniqueness constraint
        - is_active: Index for filtering active/inactive admins
        """
        collection_name = AdminsSchema.get_collection_name()
        logger.info(f"Creating indexes for collection: {collection_name}")
        
        try:
            # Create email index (unique)
            logger.debug(f"Creating email index (unique) for {collection_name}")
            try:
                result = await db.admins.create_index("email", unique=True)
                logger.info(f"Email index created successfully for {collection_name}: {result}")
            except PyMongoError as e:
                # Index might already exist - check error
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.debug(f"Email index already exists for {collection_name} - skipping")
                else:
                    logger.error(f"Error creating email index for {collection_name}: {str(e)}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"Unexpected error creating email index for {collection_name}: {str(e)}", exc_info=True)
                raise
            
            # Create is_active index
            logger.debug(f"Creating is_active index for {collection_name}")
            try:
                result = await db.admins.create_index("is_active")
                logger.info(f"Is_active index created successfully for {collection_name}: {result}")
            except PyMongoError as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.debug(f"Is_active index already exists for {collection_name} - skipping")
                else:
                    logger.error(f"Error creating is_active index for {collection_name}: {str(e)}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"Unexpected error creating is_active index for {collection_name}: {str(e)}", exc_info=True)
                raise
            
            logger.info(f"All indexes created successfully for {collection_name}")
            
        except Exception as e:
            logger.error(f"Error creating indexes for {collection_name}: {str(e)}", exc_info=True)
            raise

