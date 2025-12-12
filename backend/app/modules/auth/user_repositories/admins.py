from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError, DuplicateKeyError
import logging
from app.core.models import User, UserCreate, UserUpdate, UserRole
from app.core.auth import get_password_hash
from app.core.db import get_database

# Set up logger
logger = logging.getLogger(__name__)

class AdminRepository:
    def __init__(self):
        self.collection_name = "admins"
        logger.debug(f"AdminRepository initialized with collection: {self.collection_name}")

    async def create(self, user_data: UserCreate) -> User:
        """Create a new admin"""
        logger.info(f"Starting admin creation for email: {user_data.email}")
        
        try:
            # Step 1: Get database connection
            logger.debug("Step 1: Getting database connection")
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            # Step 2: Check if email already exists (across all user collections)
            logger.debug(f"Step 2: Checking if email already exists: {user_data.email}")
            try:
                # Check in all three collections
                existing_recruiter = await db.recruiters.find_one({"email": user_data.email})
                existing_consultant = await db.consultants.find_one({"email": user_data.email})
                existing_admin = await db.admins.find_one({"email": user_data.email})
                
                if existing_recruiter or existing_consultant or existing_admin:
                    logger.warning(f"Email already exists in database: {user_data.email}")
                    raise ValueError("Email already exists")
                logger.debug(f"Email check passed: {user_data.email} is available")
            except PyMongoError as e:
                logger.error(f"Database error while checking email existence: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while checking email: {str(e)}")
            
            # Step 3: Hash password
            logger.debug("Step 3: Starting password hashing process")
            password_bytes = user_data.password.encode('utf-8')
            password_byte_length = len(password_bytes)
            logger.debug(f"Password byte length: {password_byte_length} bytes")
            
            try:
                logger.debug("Calling get_password_hash function")
                hashed_password = get_password_hash(user_data.password)
                logger.debug("Password hashed successfully")
            except ValueError as e:
                logger.error(f"Password validation/hashing ValueError: {str(e)}")
                raise
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Unexpected error during password hashing: {error_msg}", exc_info=True)
                if "72 bytes" in error_msg or "password cannot be longer" in error_msg.lower():
                    if password_byte_length <= 72:
                        logger.error(f"Unexpected password hashing error. Password is {password_byte_length} bytes (should be valid)")
                        raise ValueError(
                            f"Unexpected password hashing error. "
                            f"Plain text password is {password_byte_length} bytes (should be valid). "
                            f"Original error: {error_msg}"
                        )
                    logger.error(f"Password too long: {password_byte_length} bytes")
                    raise ValueError("Password is too long. Maximum 72 bytes allowed (approximately 72 characters for ASCII passwords).")
                raise ValueError(f"Password hashing failed: {error_msg}")
            
            # Step 4: Create admin document
            logger.debug("Step 4: Creating admin document")
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
            admin_doc = {
                "email": user_data.email,
                "name": user_data.name,
                "role": UserRole.ADMIN,  # Always ADMIN for this collection
                "is_active": user_data.is_active,
                "hashed_password": hashed_password,
                "created_at": created_at,
                "updated_at": updated_at
            }
            logger.debug(f"Admin document created with fields: email={user_data.email}, name={user_data.name}, is_active={user_data.is_active}")
            
            # Step 5: Insert into database (both admins collection and users collection)
            logger.debug("Step 5: Inserting admin document into database")
            try:
                # Insert into admins collection
                result = await db.admins.insert_one(admin_doc)
                inserted_id = str(result.inserted_id)
                logger.info(f"Admin successfully inserted into admins collection with ID: {inserted_id}")
                
                # Also insert into users collection for unified view
                try:
                    await db.users.insert_one(admin_doc)
                    logger.debug(f"Admin also inserted into users collection")
                except Exception as e:
                    logger.warning(f"Failed to insert into users collection (non-critical): {str(e)}")
                    # Don't fail the operation if users collection insert fails
            except DuplicateKeyError as e:
                logger.error(f"Duplicate key error during admin insertion: {str(e)}", exc_info=True)
                raise ValueError("Email already exists (duplicate key constraint)")
            except PyMongoError as e:
                logger.error(f"MongoDB error during admin insertion: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while creating admin: {str(e)}")
            
            # Step 6: Prepare return value
            logger.debug("Step 6: Preparing user object for return")
            admin_doc["id"] = inserted_id
            user = User(**admin_doc)
            logger.info(f"Admin creation completed successfully for email: {user_data.email}, ID: {inserted_id}")
            return user
            
        except ValueError as e:
            logger.warning(f"Admin creation failed due to validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during admin creation: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create admin: {str(e)}")

    async def get_by_id(self, admin_id: str) -> Optional[User]:
        """Get admin by ID"""
        logger.debug(f"Getting admin by ID: {admin_id}")
        
        try:
            try:
                object_id = ObjectId(admin_id)
                logger.debug(f"Admin ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid admin ID format: {admin_id} - {str(e)}")
                return None
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                admin_data = await db.admins.find_one({"_id": object_id})
                if admin_data:
                    logger.debug(f"Admin found in database: {admin_id}")
                    admin_data["id"] = str(admin_data["_id"])
                    user = User(**admin_data)
                    logger.info(f"Successfully retrieved admin by ID: {admin_id}, email: {user.email}")
                    return user
                else:
                    logger.debug(f"Admin not found with ID: {admin_id}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting admin by ID: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving admin: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting admin by ID: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting admin by ID: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get admin by ID: {str(e)}")

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get admin by email"""
        logger.debug(f"Getting admin by email: {email}")
        
        try:
            if not email or not email.strip():
                logger.warning("Empty email provided")
                return None
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                admin_data = await db.admins.find_one({"email": email})
                if admin_data:
                    logger.debug(f"Admin found in database: {email}")
                    admin_data["id"] = str(admin_data["_id"])
                    user = User(**admin_data)
                    logger.info(f"Successfully retrieved admin by email: {email}, ID: {user.id}")
                    return user
                else:
                    logger.debug(f"Admin not found with email: {email}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting admin by email: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving admin: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting admin by email: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting admin by email: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get admin by email: {str(e)}")

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all admins"""
        logger.debug(f"Getting all admins with filters - skip: {skip}, limit: {limit}")
        
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                cursor = db.admins.find({}).skip(skip).limit(limit)
                admins = []
                count = 0
                
                async for admin_data in cursor:
                    admin_data["id"] = str(admin_data["_id"])
                    admins.append(User(**admin_data))
                    count += 1
                
                logger.info(f"Successfully retrieved {count} admins (skip={skip}, limit={limit})")
                return admins
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting all admins: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving admins: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting all admins: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting all admins: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get all admins: {str(e)}")

    async def update(self, admin_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update admin"""
        logger.info(f"Updating admin with ID: {admin_id}")
        
        try:
            try:
                object_id = ObjectId(admin_id)
                logger.debug(f"Admin ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid admin ID format: {admin_id} - {str(e)}")
                raise ValueError(f"Invalid admin ID format: {admin_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            update_data = {k: v for k, v in user_data.dict().items() if v is not None}
            logger.debug(f"Update data fields: {list(update_data.keys())}")
            
            if not update_data:
                logger.warning(f"No fields to update for admin ID: {admin_id}")
                return None
            
            update_data["updated_at"] = datetime.utcnow()
            logger.debug(f"Added updated_at timestamp to update data")
            
            try:
                # Update in admins collection
                result = await db.admins.update_one(
                    {"_id": object_id},
                    {"$set": update_data}
                )
                
                # Also update in users collection
                try:
                    await db.users.update_one(
                        {"_id": object_id},
                        {"$set": update_data}
                    )
                    logger.debug(f"Admin also updated in users collection")
                except Exception as e:
                    logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                logger.debug(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if result.modified_count > 0:
                    logger.info(f"Admin successfully updated: {admin_id}")
                    return await self.get_by_id(admin_id)
                elif result.matched_count > 0:
                    logger.debug(f"Admin found but no changes made: {admin_id}")
                    return await self.get_by_id(admin_id)
                else:
                    logger.warning(f"Admin not found for update: {admin_id}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while updating admin: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while updating admin: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error updating admin: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating admin: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to update admin: {str(e)}")

    async def delete(self, admin_id: str) -> bool:
        """Delete admin"""
        logger.info(f"Deleting admin with ID: {admin_id}")
        
        try:
            try:
                object_id = ObjectId(admin_id)
                logger.debug(f"Admin ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid admin ID format: {admin_id} - {str(e)}")
                raise ValueError(f"Invalid admin ID format: {admin_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                # Delete from admins collection
                result = await db.admins.delete_one({"_id": object_id})
                deleted = result.deleted_count > 0
                
                # Also delete from users collection
                if deleted:
                    try:
                        await db.users.delete_one({"_id": object_id})
                        logger.debug(f"Admin also deleted from users collection")
                    except Exception as e:
                        logger.warning(f"Failed to delete from users collection (non-critical): {str(e)}")
                
                if deleted:
                    logger.info(f"Admin successfully deleted: {admin_id}")
                else:
                    logger.warning(f"Admin not found for deletion: {admin_id}")
                
                return deleted
            except PyMongoError as e:
                logger.error(f"MongoDB error while deleting admin: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while deleting admin: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error deleting admin: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deleting admin: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to delete admin: {str(e)}")

    async def deactivate(self, admin_id: str) -> bool:
        """Deactivate admin (soft delete)"""
        logger.info(f"Deactivating admin with ID: {admin_id}")
        
        try:
            try:
                object_id = ObjectId(admin_id)
                logger.debug(f"Admin ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid admin ID format: {admin_id} - {str(e)}")
                raise ValueError(f"Invalid admin ID format: {admin_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                update_data = {"is_active": False, "updated_at": datetime.utcnow()}
                # Update in admins collection
                result = await db.admins.update_one(
                    {"_id": object_id},
                    {"$set": update_data}
                )
                
                # Also update in users collection
                if result.modified_count > 0:
                    try:
                        await db.users.update_one(
                            {"_id": object_id},
                            {"$set": update_data}
                        )
                        logger.debug(f"Admin also deactivated in users collection")
                    except Exception as e:
                        logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                deactivated = result.modified_count > 0
                logger.debug(f"Deactivation result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if deactivated:
                    logger.info(f"Admin successfully deactivated: {admin_id}")
                elif result.matched_count > 0:
                    logger.debug(f"Admin found but already deactivated: {admin_id}")
                else:
                    logger.warning(f"Admin not found for deactivation: {admin_id}")
                
                return deactivated
            except PyMongoError as e:
                logger.error(f"MongoDB error while deactivating admin: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while deactivating admin: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error deactivating admin: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deactivating admin: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to deactivate admin: {str(e)}")

    async def activate(self, admin_id: str) -> bool:
        """Activate admin"""
        logger.info(f"Activating admin with ID: {admin_id}")
        
        try:
            try:
                object_id = ObjectId(admin_id)
                logger.debug(f"Admin ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid admin ID format: {admin_id} - {str(e)}")
                raise ValueError(f"Invalid admin ID format: {admin_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                update_data = {"is_active": True, "updated_at": datetime.utcnow()}
                # Update in admins collection
                result = await db.admins.update_one(
                    {"_id": object_id},
                    {"$set": update_data}
                )
                
                # Also update in users collection
                if result.modified_count > 0:
                    try:
                        await db.users.update_one(
                            {"_id": object_id},
                            {"$set": update_data}
                        )
                        logger.debug(f"Admin also activated in users collection")
                    except Exception as e:
                        logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                activated = result.modified_count > 0
                logger.debug(f"Activation result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if activated:
                    logger.info(f"Admin successfully activated: {admin_id}")
                elif result.matched_count > 0:
                    logger.debug(f"Admin found but already activated: {admin_id}")
                else:
                    logger.warning(f"Admin not found for activation: {admin_id}")
                
                return activated
            except PyMongoError as e:
                logger.error(f"MongoDB error while activating admin: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while activating admin: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error activating admin: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while activating admin: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to activate admin: {str(e)}")

    async def count(self) -> int:
        """Count admins"""
        logger.debug(f"Counting admins")
        
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                count = await db.admins.count_documents({})
                logger.info(f"Admin count: {count}")
                return count
            except PyMongoError as e:
                logger.error(f"MongoDB error while counting admins: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while counting admins: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error counting admins: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while counting admins: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to count admins: {str(e)}")

