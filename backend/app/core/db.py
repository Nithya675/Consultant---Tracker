import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
import os
import logging
from typing import Optional
from app.core.config import settings
from app.core.schema_registry import get_all_schemas

# Set up logger
logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None
    
    def __init__(self):
        logger.debug("Database class instance created")
    
    def __repr__(self):
        client_status = "connected" if self.client else "not connected"
        database_status = "set" if self.database else "not set"
        return f"Database(client={client_status}, database={database_status})"

db = Database()
logger.debug("Global database instance created")

async def get_database():
    """Get the database instance"""
    logger.debug("Getting database instance")
    
    try:
        if db.database is None:
            logger.warning("Database instance is None - database may not be initialized")
            raise ValueError("Database not initialized. Call init_db() first.")
        
        logger.debug("Database instance retrieved successfully")
        return db.database
        
    except ValueError as e:
        logger.error(f"Database not available: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting database: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to get database: {str(e)}")

async def init_db():
    """Initialize database connection"""
    logger.info("Initializing database connection")
    
    try:
        # Step 1: Get MongoDB URL from environment
        logger.debug("Step 1: Getting MongoDB URL from configuration")
        mongodb_url = settings.MONGODB_URL
        logger.info(f"MongoDB URL: {mongodb_url.replace('://', '://***') if '://' in mongodb_url else '***'}")  # Mask password in URL
        
        # Step 2: Create MongoDB client
        logger.debug("Step 2: Creating MongoDB client")
        try:
            db.client = AsyncIOMotorClient(mongodb_url)
            logger.debug("MongoDB client created successfully")
        except Exception as e:
            logger.error(f"Error creating MongoDB client: {str(e)}", exc_info=True)
            raise ConnectionFailure(f"Failed to create MongoDB client: {str(e)}")
        
        # Step 3: Test connection
        logger.debug("Step 3: Testing MongoDB connection")
        try:
            # Ping the server to verify connection
            await db.client.admin.command('ping')
            logger.info("MongoDB connection test successful")
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB server selection timeout: {str(e)}", exc_info=True)
            raise ConnectionFailure(f"Cannot connect to MongoDB server: {str(e)}")
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failure: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error testing MongoDB connection: {str(e)}", exc_info=True)
            raise ConnectionFailure(f"Failed to connect to MongoDB: {str(e)}")
        
        # Step 4: Get database instance
        logger.debug("Step 4: Getting database instance")
        try:
            db.database = db.client[settings.DATABASE_NAME]
            logger.info(f"Database instance obtained: {settings.DATABASE_NAME}")
        except Exception as e:
            logger.error(f"Error getting database instance: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get database instance: {str(e)}")
        
        # Step 5: Create indexes
        logger.debug("Step 5: Creating database indexes")
        try:
            await create_indexes()
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}", exc_info=True)
            # Don't fail initialization if indexes fail - log and continue
            logger.warning("Database initialized but index creation failed - continuing anyway")
        
        logger.info("Database initialization completed successfully")
        
    except ConnectionFailure as e:
        logger.error(f"Database connection failure during initialization: {str(e)}", exc_info=True)
        raise
    except ValueError as e:
        logger.error(f"Database initialization validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}", exc_info=True)
        raise ConnectionFailure(f"Database initialization failed: {str(e)}")

async def create_indexes():
    """
    Create database indexes for all registered collections using the schema registry.
    
    This function automatically discovers all registered collection schemas and
    creates their indexes. To add indexes for a new collection, simply create
    a new schema file in app/schemas/ and import it in app/schemas/__init__.py
    """
    logger.info("Creating database indexes for all registered collections")
    
    try:
        # Step 1: Verify database is available
        logger.debug("Step 1: Verifying database is available")
        if db.database is None:
            logger.error("Database is None - cannot create indexes")
            raise ValueError("Database not initialized")
        logger.debug("Database verified")
        
        # Step 2: Get all registered schemas
        logger.debug("Step 2: Getting all registered schemas")
        schemas = get_all_schemas()
        logger.info(f"Found {len(schemas)} registered schema(s)")
        
        if not schemas:
            logger.warning("No schemas registered - no indexes will be created")
            return
        
        # Step 3: Create indexes for each schema
        logger.debug("Step 3: Creating indexes for each registered schema")
        successful_schemas = []
        failed_schemas = []
        
        for schema_class in schemas:
            collection_name = schema_class.get_collection_name()
            schema_name = schema_class.__name__
            
            try:
                logger.debug(f"Creating indexes for schema: {schema_name} (collection: {collection_name})")
                await schema_class.create_indexes(db.database)
                successful_schemas.append(schema_name)
                logger.info(f"Successfully created indexes for schema: {schema_name}")
            except Exception as e:
                failed_schemas.append((schema_name, str(e)))
                logger.error(f"Failed to create indexes for schema {schema_name}: {str(e)}", exc_info=True)
                # Continue with other schemas even if one fails
                continue
        
        # Step 4: Log summary
        logger.info(f"Index creation completed: {len(successful_schemas)} successful, {len(failed_schemas)} failed")
        
        if successful_schemas:
            logger.info(f"Successfully created indexes for: {', '.join(successful_schemas)}")
        
        if failed_schemas:
            logger.warning(f"Failed to create indexes for: {', '.join([name for name, _ in failed_schemas])}")
            # Raise an error if any schema failed, but include details about which ones succeeded
            error_details = "; ".join([f"{name}: {error}" for name, error in failed_schemas])
            raise ValueError(f"Index creation failed for some schemas: {error_details}")
        
        logger.info("All database indexes created successfully for all registered collections")
        
    except ValueError as e:
        logger.error(f"Index creation validation error: {str(e)}")
        raise
    except PyMongoError as e:
        logger.error(f"MongoDB error during index creation: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during index creation: {str(e)}", exc_info=True)
        raise ValueError(f"Index creation failed: {str(e)}")

async def close_db():
    """Close database connection"""
    logger.info("Closing database connection")
    
    try:
        # Step 1: Check if client exists
        logger.debug("Step 1: Checking if database client exists")
        if db.client is None:
            logger.warning("Database client is None - nothing to close")
            return
        
        logger.debug("Database client found")
        
        # Step 2: Close the client connection
        logger.debug("Step 2: Closing database client connection")
        try:
            db.client.close()
            logger.info("Database client closed successfully")
        except Exception as e:
            logger.error(f"Error closing database client: {str(e)}", exc_info=True)
            raise
        
        # Step 3: Reset database instance
        logger.debug("Step 3: Resetting database instance")
        db.client = None
        db.database = None
        logger.debug("Database instance reset")
        
        logger.info("Database connection closed successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error closing database: {str(e)}", exc_info=True)
        # Don't raise - try to clean up anyway
        try:
            db.client = None
            db.database = None
            logger.debug("Database instance reset after error")
        except:
            pass
