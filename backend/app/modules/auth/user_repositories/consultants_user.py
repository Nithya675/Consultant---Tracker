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

class ConsultantUserRepository:
    def __init__(self):
        self.collection_name = "consultants"
        logger.debug(f"ConsultantUserRepository initialized with collection: {self.collection_name}")

    async def create(self, user_data: UserCreate) -> User:
        """Create a new consultant user"""
        logger.info(f"Starting consultant creation for email: {user_data.email}")
        
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
            
            # Step 4: Create consultant document
            logger.debug("Step 4: Creating consultant document")
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
            consultant_doc = {
                "email": user_data.email,
                "name": user_data.name,
                "role": UserRole.CONSULTANT,  # Always CONSULTANT for this collection
                "is_active": user_data.is_active,
                "hashed_password": hashed_password,
                "created_at": created_at,
                "updated_at": updated_at
            }
            logger.debug(f"Consultant document created with fields: email={user_data.email}, name={user_data.name}, is_active={user_data.is_active}")
            
            # Step 5: Insert into database (both consultants collection and users collection)
            logger.debug("Step 5: Inserting consultant document into database")
            try:
                # Insert into consultants collection
                result = await db.consultants.insert_one(consultant_doc)
                inserted_id = str(result.inserted_id)
                logger.info(f"Consultant successfully inserted into consultants collection with ID: {inserted_id}")
                
                # Also insert into users collection for unified view
                try:
                    await db.users.insert_one(consultant_doc)
                    logger.debug(f"Consultant also inserted into users collection")
                except Exception as e:
                    logger.warning(f"Failed to insert into users collection (non-critical): {str(e)}")
                    # Don't fail the operation if users collection insert fails
            except DuplicateKeyError as e:
                logger.error(f"Duplicate key error during consultant insertion: {str(e)}", exc_info=True)
                raise ValueError("Email already exists (duplicate key constraint)")
            except PyMongoError as e:
                logger.error(f"MongoDB error during consultant insertion: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while creating consultant: {str(e)}")
            
            # Step 6: Prepare return value
            logger.debug("Step 6: Preparing user object for return")
            consultant_doc["id"] = inserted_id
            user = User(**consultant_doc)
            logger.info(f"Consultant creation completed successfully for email: {user_data.email}, ID: {inserted_id}")
            return user
            
        except ValueError as e:
            logger.warning(f"Consultant creation failed due to validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during consultant creation: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create consultant: {str(e)}")

    async def get_by_id(self, consultant_id: str) -> Optional[User]:
        """Get consultant by ID"""
        logger.debug(f"Getting consultant by ID: {consultant_id}")
        
        try:
            try:
                object_id = ObjectId(consultant_id)
                logger.debug(f"Consultant ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid consultant ID format: {consultant_id} - {str(e)}")
                return None
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                consultant_data = await db.consultants.find_one({"_id": object_id})
                if consultant_data:
                    logger.debug(f"Consultant found in database: {consultant_id}")
                    consultant_data["id"] = str(consultant_data["_id"])
                    user = User(**consultant_data)
                    logger.info(f"Successfully retrieved consultant by ID: {consultant_id}, email: {user.email}")
                    return user
                else:
                    logger.debug(f"Consultant not found with ID: {consultant_id}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting consultant by ID: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving consultant: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting consultant by ID: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting consultant by ID: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get consultant by ID: {str(e)}")

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get consultant by email"""
        logger.debug(f"Getting consultant by email: {email}")
        
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
                consultant_data = await db.consultants.find_one({"email": email})
                if consultant_data:
                    logger.debug(f"Consultant found in database: {email}")
                    consultant_data["id"] = str(consultant_data["_id"])
                    user = User(**consultant_data)
                    logger.info(f"Successfully retrieved consultant by email: {email}, ID: {user.id}")
                    return user
                else:
                    logger.debug(f"Consultant not found with email: {email}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting consultant by email: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving consultant: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting consultant by email: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting consultant by email: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get consultant by email: {str(e)}")

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all consultants"""
        logger.debug(f"Getting all consultants with filters - skip: {skip}, limit: {limit}")
        
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                cursor = db.consultants.find({}).skip(skip).limit(limit)
                consultants = []
                count = 0
                
                async for consultant_data in cursor:
                    consultant_data["id"] = str(consultant_data["_id"])
                    consultants.append(User(**consultant_data))
                    count += 1
                
                logger.info(f"Successfully retrieved {count} consultants (skip={skip}, limit={limit})")
                return consultants
            except PyMongoError as e:
                logger.error(f"MongoDB error while getting all consultants: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while retrieving consultants: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error getting all consultants: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting all consultants: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get all consultants: {str(e)}")

    async def update(self, consultant_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update consultant"""
        logger.info(f"Updating consultant with ID: {consultant_id}")
        
        try:
            try:
                object_id = ObjectId(consultant_id)
                logger.debug(f"Consultant ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid consultant ID format: {consultant_id} - {str(e)}")
                raise ValueError(f"Invalid consultant ID format: {consultant_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            update_data = {k: v for k, v in user_data.dict().items() if v is not None}
            logger.debug(f"Update data fields: {list(update_data.keys())}")
            
            if not update_data:
                logger.warning(f"No fields to update for consultant ID: {consultant_id}")
                return None
            
            update_data["updated_at"] = datetime.utcnow()
            logger.debug(f"Added updated_at timestamp to update data")
            
            try:
                # Update in consultants collection
                result = await db.consultants.update_one(
                    {"_id": object_id},
                    {"$set": update_data}
                )
                
                # Also update in users collection
                try:
                    await db.users.update_one(
                        {"_id": object_id},
                        {"$set": update_data}
                    )
                    logger.debug(f"Consultant also updated in users collection")
                except Exception as e:
                    logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                logger.debug(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if result.modified_count > 0:
                    logger.info(f"Consultant successfully updated: {consultant_id}")
                    return await self.get_by_id(consultant_id)
                elif result.matched_count > 0:
                    logger.debug(f"Consultant found but no changes made: {consultant_id}")
                    return await self.get_by_id(consultant_id)
                else:
                    logger.warning(f"Consultant not found for update: {consultant_id}")
                    return None
            except PyMongoError as e:
                logger.error(f"MongoDB error while updating consultant: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while updating consultant: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error updating consultant: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating consultant: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to update consultant: {str(e)}")

    async def delete(self, consultant_id: str) -> bool:
        """Delete consultant"""
        logger.info(f"Deleting consultant with ID: {consultant_id}")
        
        try:
            try:
                object_id = ObjectId(consultant_id)
                logger.debug(f"Consultant ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid consultant ID format: {consultant_id} - {str(e)}")
                raise ValueError(f"Invalid consultant ID format: {consultant_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                # Delete from consultants collection
                result = await db.consultants.delete_one({"_id": object_id})
                deleted = result.deleted_count > 0
                
                # Also delete from users collection
                if deleted:
                    try:
                        await db.users.delete_one({"_id": object_id})
                        logger.debug(f"Consultant also deleted from users collection")
                    except Exception as e:
                        logger.warning(f"Failed to delete from users collection (non-critical): {str(e)}")
                
                if deleted:
                    logger.info(f"Consultant successfully deleted: {consultant_id}")
                else:
                    logger.warning(f"Consultant not found for deletion: {consultant_id}")
                
                return deleted
            except PyMongoError as e:
                logger.error(f"MongoDB error while deleting consultant: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while deleting consultant: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error deleting consultant: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deleting consultant: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to delete consultant: {str(e)}")

    async def deactivate(self, consultant_id: str) -> bool:
        """Deactivate consultant (soft delete)"""
        logger.info(f"Deactivating consultant with ID: {consultant_id}")
        
        try:
            try:
                object_id = ObjectId(consultant_id)
                logger.debug(f"Consultant ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid consultant ID format: {consultant_id} - {str(e)}")
                raise ValueError(f"Invalid consultant ID format: {consultant_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                update_data = {"is_active": False, "updated_at": datetime.utcnow()}
                # Update in consultants collection
                result = await db.consultants.update_one(
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
                        logger.debug(f"Consultant also deactivated in users collection")
                    except Exception as e:
                        logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                deactivated = result.modified_count > 0
                logger.debug(f"Deactivation result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if deactivated:
                    logger.info(f"Consultant successfully deactivated: {consultant_id}")
                elif result.matched_count > 0:
                    logger.debug(f"Consultant found but already deactivated: {consultant_id}")
                else:
                    logger.warning(f"Consultant not found for deactivation: {consultant_id}")
                
                return deactivated
            except PyMongoError as e:
                logger.error(f"MongoDB error while deactivating consultant: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while deactivating consultant: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error deactivating consultant: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deactivating consultant: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to deactivate consultant: {str(e)}")

    async def activate(self, consultant_id: str) -> bool:
        """Activate consultant"""
        logger.info(f"Activating consultant with ID: {consultant_id}")
        
        try:
            try:
                object_id = ObjectId(consultant_id)
                logger.debug(f"Consultant ID converted to ObjectId successfully")
            except InvalidId as e:
                logger.warning(f"Invalid consultant ID format: {consultant_id} - {str(e)}")
                raise ValueError(f"Invalid consultant ID format: {consultant_id}")
            
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                update_data = {"is_active": True, "updated_at": datetime.utcnow()}
                # Update in consultants collection
                result = await db.consultants.update_one(
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
                        logger.debug(f"Consultant also activated in users collection")
                    except Exception as e:
                        logger.warning(f"Failed to update users collection (non-critical): {str(e)}")
                
                activated = result.modified_count > 0
                logger.debug(f"Activation result - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if activated:
                    logger.info(f"Consultant successfully activated: {consultant_id}")
                elif result.matched_count > 0:
                    logger.debug(f"Consultant found but already activated: {consultant_id}")
                else:
                    logger.warning(f"Consultant not found for activation: {consultant_id}")
                
                return activated
            except PyMongoError as e:
                logger.error(f"MongoDB error while activating consultant: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while activating consultant: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error activating consultant: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while activating consultant: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to activate consultant: {str(e)}")

    async def count(self) -> int:
        """Count consultants"""
        logger.debug(f"Counting consultants")
        
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                raise ValueError("Database connection not available")
            logger.debug("Database connection obtained successfully")
            
            try:
                count = await db.consultants.count_documents({})
                logger.info(f"Consultant count: {count}")
                return count
            except PyMongoError as e:
                logger.error(f"MongoDB error while counting consultants: {str(e)}", exc_info=True)
                raise ValueError(f"Database error while counting consultants: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error counting consultants: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while counting consultants: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to count consultants: {str(e)}")

