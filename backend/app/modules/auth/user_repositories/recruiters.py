from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError, DuplicateKeyError
import logging
from app.core.models import User, UserCreate, UserUpdate, UserRole
from app.core.auth import get_password_hash
from app.core.db import get_database
from app.modules.recruiters.models import RecruiterProfile, RecruiterProfileUpdate

# Set up logger
logger = logging.getLogger(__name__)

class RecruiterRepository:
    def __init__(self):
        self.collection_name = "recruiters"
        logger.debug(f"RecruiterRepository initialized with collection: {self.collection_name}")

    async def create(self, user_data: UserCreate) -> User:
        """Create a new recruiter"""
        logger.info(f"Starting recruiter creation for email: {user_data.email}")
        
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
            
            # Step 4: Create recruiter document
            logger.debug("Step 4: Creating recruiter document")
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
            recruiter_doc = {
                "email": user_data.email,
                "name": user_data.name,
                "role": UserRole.RECRUITER,  # Always RECRUITER for this collection
                "is_active": user_data.is_active,
                "hashed_password": hashed_password,
                "created_at": created_at,
                "updated_at": updated_at
            }
            logger.debug(f"Recruiter document created with fields: email={user_data.email}, name={user_data.name}, is_active={user_data.is_active}")
            
            # Step 5: Insert into database (both recruiters collection and users collection)
            logger.debug("Step 5: Inserting recruiter document into database")
            try:
                # Insert into recruiters collection
                result = await db.recruiters.insert_one(recruiter_doc)
                inserted_id = str(result.inserted_id)
                logger.info(f"Recruiter successfully inserted into recruiters collection with ID: {inserted_id}")
                
                # Also insert into users collection for unified view
                try:
                    await db.users.insert_one(recruiter_doc)
                    logger.debug(f"Recruiter also inserted into users collection")
                except Exception as e:
                    logger.warning(f"Failed to insert into users collection (non-critical): {str(e)}")
                    # Don't fail the operation if users collection insert fails
            except DuplicateKeyError as e:
                logger.error(f"Duplicate key error during recruiter insertion: {str(e)}", exc_info=True)
                raise ValueError("Email already exists (duplicate key constraint)")
            except PyMongoError as e:
                logger.error(f"MongoDB error during recruiter insertion: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while creating recruiter: {str(e)}")
            
            # Step 6: Prepare return value
            logger.debug("Step 6: Preparing user object for return")
            recruiter_doc["id"] = inserted_id
            user = User(**recruiter_doc)
            logger.info(f"Recruiter creation completed successfully for email: {user_data.email}, ID: {inserted_id}")
            return user
            
        except ValueError as e:
            logger.warning(f"Recruiter creation failed due to validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during recruiter creation: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create recruiter: {str(e)}")

    async def get_by_id(self, recruiter_id: str) -> Optional[User]:
        """Get recruiter by ID"""
        logger.debug(f"Getting recruiter by ID: {recruiter_id}")
        
        try:
            try:
                object_id = ObjectId(recruiter_id)
                logger.debug(f"Recruiter ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid recruiter ID format: {recruiter_id} - {str(e)}")
                return None
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                recruiter_data = await db.recruiters.find_one({"_id": object_id})
                if recruiter_data:
                    logger.debug(f"Recruiter found in database: {recruiter_id}")
                    recruiter_data["id"] = str(recruiter_data["_id"])
                    user = User(**recruiter_data)
                    logger.info(f"Successfully retrieved recruiter by ID: {recruiter_id}, email: {user.email}")
                    return user
                else:
                    logger.debug(f"Recruiter not found with ID: {recruiter_id}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting recruiter by ID: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving recruiter: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting recruiter by ID: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting recruiter by ID: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get recruiter by ID: {str(e)}")

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get recruiter by email"""
        logger.debug(f"Getting recruiter by email: {email}")
        
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
                recruiter_data = await db.recruiters.find_one({"email": email})
                if recruiter_data:
                    logger.debug(f"Recruiter found in database: {email}")
                    recruiter_data["id"] = str(recruiter_data["_id"])
                    user = User(**recruiter_data)
                    logger.info(f"Successfully retrieved recruiter by email: {email}, ID: {user.id}")
                    return user
                else:
                    logger.debug(f"Recruiter not found with email: {email}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting recruiter by email: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving recruiter: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting recruiter by email: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting recruiter by email: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get recruiter by email: {str(e)}")

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all recruiters"""
        logger.debug(f"Getting all recruiters with filters - skip: {skip}, limit: {limit}")
        
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                cursor = db.recruiters.find({}).skip(skip).limit(limit)
                recruiters = []
                count = 0
                
                async for recruiter_data in cursor:
                    recruiter_data["id"] = str(recruiter_data["_id"])
                    recruiters.append(User(**recruiter_data))
                    count += 1
                
                logger.info(f"Successfully retrieved {count} recruiters (skip={skip}, limit={limit})")
                return recruiters
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting all recruiters: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving recruiters: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting all recruiters: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting all recruiters: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get all recruiters: {str(e)}")

    async def update(self, recruiter_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update recruiter"""
        logger.info(f"Updating recruiter with ID: {recruiter_id}")
        
        try:
            try:
                object_id = ObjectId(recruiter_id)
                logger.debug(f"Recruiter ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid recruiter ID format: {recruiter_id} - {str(e)}")
                raise ValueError(f"Invalid recruiter ID format: {recruiter_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            update_data = {k: v for k, v in user_data.dict().items() if v is not None}
            logger.debug(f"Update data fields: {list(update_data.keys())}")
            
            if not update_data:
                logger.warning(f"No fields to update for recruiter ID: {recruiter_id}")
                return None
            
            update_data["updated_at"] = datetime.utcnow()
            logger.debug(f"Added updated_at timestamp to update data")
            
            try:
                # Update in recruiters collection
                result = await db.recruiters.update_one(
                    {"_id": object_id},
                    {"$set": update_data}
                )
                
                # Also update in users collection
                try:
                    await db.users.update_one(
                        {"_id": object_id},
                        {"$set": update_data}
                    )
                    logger.debug(f"Recruiter also updated in users collection")
                except Exception as e:
                    logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                logger.debug(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if result.modified_count > 0:
                    logger.info(f"Recruiter successfully updated: {recruiter_id}")
                    return await self.get_by_id(recruiter_id)
                elif result.matched_count > 0:
                    logger.debug(f"Recruiter found but no changes made: {recruiter_id}")
                    return await self.get_by_id(recruiter_id)
                else:
                    logger.warning(f"Recruiter not found for update: {recruiter_id}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while updating recruiter: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while updating recruiter: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error updating recruiter: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating recruiter: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to update recruiter: {str(e)}")

    async def delete(self, recruiter_id: str) -> bool:
        """Delete recruiter"""
        logger.info(f"Deleting recruiter with ID: {recruiter_id}")
        
        try:
            try:
                object_id = ObjectId(recruiter_id)
                logger.debug(f"Recruiter ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid recruiter ID format: {recruiter_id} - {str(e)}")
                raise ValueError(f"Invalid recruiter ID format: {recruiter_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                # Delete from recruiters collection
                result = await db.recruiters.delete_one({"_id": object_id})
                deleted = result.deleted_count > 0
                
                # Also delete from users collection
                if deleted:
                    try:
                        await db.users.delete_one({"_id": object_id})
                        logger.debug(f"Recruiter also deleted from users collection")
                    except Exception as e:
                        logger.warning(f"Failed to delete from users collection (non-critical): {str(e)}")
                
                if deleted:
                    logger.info(f"Recruiter successfully deleted: {recruiter_id}")
                else:
                    logger.warning(f"Recruiter not found for deletion: {recruiter_id}")
                
                return deleted
            except PyMongoError as e:
                logger.error(f"MongoDB error while deleting recruiter: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while deleting recruiter: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error deleting recruiter: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deleting recruiter: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to delete recruiter: {str(e)}")

    async def deactivate(self, recruiter_id: str) -> bool:
        """Deactivate recruiter (soft delete)"""
        logger.info(f"Deactivating recruiter with ID: {recruiter_id}")
        
        try:
            try:
                object_id = ObjectId(recruiter_id)
                logger.debug(f"Recruiter ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid recruiter ID format: {recruiter_id} - {str(e)}")
                raise ValueError(f"Invalid recruiter ID format: {recruiter_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                update_data = {"is_active": False, "updated_at": datetime.utcnow()}
                # Update in recruiters collection
                result = await db.recruiters.update_one(
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
                        logger.debug(f"Recruiter also deactivated in users collection")
                    except Exception as e:
                        logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                deactivated = result.modified_count > 0
                logger.debug(f"Deactivation result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if deactivated:
                    logger.info(f"Recruiter successfully deactivated: {recruiter_id}")
                elif result.matched_count > 0:
                    logger.debug(f"Recruiter found but already deactivated: {recruiter_id}")
                else:
                    logger.warning(f"Recruiter not found for deactivation: {recruiter_id}")
                
                return deactivated
            except PyMongoError as e:
                logger.error(f"MongoDB error while deactivating recruiter: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while deactivating recruiter: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error deactivating recruiter: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deactivating recruiter: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to deactivate recruiter: {str(e)}")

    async def activate(self, recruiter_id: str) -> bool:
        """Activate recruiter"""
        logger.info(f"Activating recruiter with ID: {recruiter_id}")
        
        try:
            try:
                object_id = ObjectId(recruiter_id)
                logger.debug(f"Recruiter ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid recruiter ID format: {recruiter_id} - {str(e)}")
                raise ValueError(f"Invalid recruiter ID format: {recruiter_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                update_data = {"is_active": True, "updated_at": datetime.utcnow()}
                # Update in recruiters collection
                result = await db.recruiters.update_one(
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
                        logger.debug(f"Recruiter also activated in users collection")
                    except Exception as e:
                        logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                activated = result.modified_count > 0
                logger.debug(f"Activation result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if activated:
                    logger.info(f"Recruiter successfully activated: {recruiter_id}")
                elif result.matched_count > 0:
                    logger.debug(f"Recruiter found but already activated: {recruiter_id}")
                else:
                    logger.warning(f"Recruiter not found for activation: {recruiter_id}")
                
                return activated
            except PyMongoError as e:
                logger.error(f"MongoDB error while activating recruiter: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while activating recruiter: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error activating recruiter: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while activating recruiter: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to activate recruiter: {str(e)}")

    async def count(self) -> int:
        """Count recruiters"""
        logger.debug(f"Counting recruiters")
        
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                count = await db.recruiters.count_documents({})
                logger.info(f"Recruiter count: {count}")
                return count
            except PyMongoError as e:
                logger.error(f"MongoDB error while counting recruiters: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while counting recruiters: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error counting recruiters: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while counting recruiters: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to count recruiters: {str(e)}")

    async def get_profile_by_user_id(self, user_id: str) -> Optional[RecruiterProfile]:
        """Get recruiter profile by user ID"""
        logger.debug(f"Getting recruiter profile for user ID: {user_id}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")

            recruiter_data = await db.recruiters.find_one({"_id": ObjectId(user_id)})

            if recruiter_data:
                recruiter_data["id"] = str(recruiter_data["_id"])
                recruiter_data["user_id"] = user_id
                return RecruiterProfile(**recruiter_data)

            return None
        except (InvalidId, TypeError) as e:
            logger.error(f"Invalid user_id format: {user_id}")
            raise ValueError(f"Invalid user ID format: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting recruiter profile: {str(e)}", exc_info=True)
            raise

    async def update_profile(self, user_id: str, profile_data: RecruiterProfileUpdate) -> RecruiterProfile:
        """Update recruiter profile"""
        logger.info(f"Updating recruiter profile for user ID: {user_id}")
        try:
            db = await get_database()
            if db is None:
                raise ValueError("Database connection not available")

            update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()

            await db.recruiters.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )

            return await self.get_profile_by_user_id(user_id)
        except (InvalidId, TypeError) as e:
            logger.error(f"Invalid user_id format: {user_id}")
            raise ValueError(f"Invalid user ID format: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating recruiter profile: {str(e)}", exc_info=True)
            raise

