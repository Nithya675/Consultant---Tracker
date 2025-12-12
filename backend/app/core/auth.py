from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.db import get_database
from app.core.models import User, TokenData, UserRole
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Import configuration from centralized config
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Log configuration on module load
logger.debug(f"Auth module initialized - ALGORITHM: {ALGORITHM}, TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")

# Password hashing
pwd_context = CryptContext(schemes=settings.PASSWORD_HASH_SCHEMES, deprecated="auto")
logger.debug(f"Password hashing context initialized with {settings.PASSWORD_HASH_SCHEMES}")

# JWT token scheme
security = HTTPBearer()
logger.debug("HTTPBearer security scheme initialized")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    logger.debug("Starting password verification")
    
    try:
        # Truncate password to 72 bytes if necessary (bcrypt limitation)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > settings.PASSWORD_MAX_BYTES:
            logger.debug(f"Password exceeds {settings.PASSWORD_MAX_BYTES} bytes ({len(password_bytes)} bytes), truncating")
            truncated = password_bytes[:settings.PASSWORD_MAX_BYTES]
            # Remove incomplete UTF-8 sequences
            while truncated and (truncated[-1] & 0x80) and not (truncated[-1] & 0x40):
                truncated = truncated[:-1]
            plain_password = truncated.decode('utf-8', errors='ignore')

        
        is_valid = pwd_context.verify(plain_password, hashed_password)
        if is_valid:
            logger.debug("Password verification successful")
        else:
            logger.debug("Password verification failed - password does not match")
        return is_valid
    except Exception as e:
        logger.error(f"Error during password verification: {str(e)}", exc_info=True)
        return False

def get_password_hash(password: str) -> str:
    """Hash a password - bcrypt has a 72-byte limit"""
    logger.debug("Starting password hashing")
    
    try:
        # Truncate password to 72 bytes if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > settings.PASSWORD_MAX_BYTES:
            logger.debug(f"Password exceeds {settings.PASSWORD_MAX_BYTES} bytes ({len(password_bytes)} bytes), truncating")
            truncated = password_bytes[:settings.PASSWORD_MAX_BYTES]
            # Remove incomplete UTF-8 sequences
            while truncated and (truncated[-1] & 0x80) and not (truncated[-1] & 0x40):
                truncated = truncated[:-1]
            password = truncated.decode('utf-8', errors='ignore')

        
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error during password hashing: {str(e)}", exc_info=True)
        raise ValueError(f"Password hashing failed: {str(e)}")

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password"""
    logger.debug(f"Authenticating user with email: {email}")
    
    try:
        user = await get_user_by_email(email)
        if not user:
            logger.warning(f"Authentication failed: User not found with email: {email}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for email: {email}")
            return None
        
        logger.info(f"User authenticated successfully: {email}, ID: {user.id}, role: {user.role}")
        return user
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}", exc_info=True)
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    logger.debug("Creating JWT access token")
    
    try:
        # Step 1: Copy data to avoid modifying original
        logger.debug("Step 1: Copying token data")
        to_encode = data.copy()
        logger.debug(f"Token data copied - contains keys: {list(to_encode.keys())}")
        
        # Step 2: Calculate expiration time
        logger.debug("Step 2: Calculating token expiration time")
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
            logger.debug(f"Using provided expiration delta: {expires_delta}")
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            logger.debug(f"Using default expiration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        
        logger.debug(f"Token will expire at: {expire}")
        
        # Step 3: Add expiration to token data
        logger.debug("Step 3: Adding expiration to token data")
        to_encode.update({"exp": expire})
        logger.debug("Expiration added to token data")
        
        # Step 4: Encode JWT token
        logger.debug(f"Step 4: Encoding JWT token with algorithm: {ALGORITHM}")
        try:
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            logger.debug("JWT token encoded successfully")
            logger.info(f"Access token created successfully - expires at: {expire}")
            return encoded_jwt
        except JWTError as e:
            logger.error(f"JWT encoding error: {str(e)}", exc_info=True)
            raise ValueError(f"Token encoding failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during JWT encoding: {str(e)}", exc_info=True)
            raise ValueError(f"Token creation failed: {str(e)}")
            
    except ValueError as e:
        logger.error(f"Token creation validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token creation: {str(e)}", exc_info=True)
        raise ValueError(f"Token creation failed: {str(e)}")

async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email from database"""
    logger.debug(f"Getting user by email: {email}")
    
    try:
        # Step 1: Validate email
        logger.debug(f"Step 1: Validating email format: {email}")
        if not email or not email.strip():
            logger.warning("Empty email provided to get_user_by_email")
            return None
        
        # Step 2: Get database connection
        logger.debug("Step 2: Getting database connection")
        try:
            db = await get_database()
            if db is None:
                logger.error("Database connection not available")
                return None
            logger.debug("Database connection obtained successfully")
        except Exception as e:
            logger.error(f"Error getting database connection: {str(e)}", exc_info=True)
            return None
        
        # Step 3: Query database for user across all user collections
        logger.debug(f"Step 3: Querying database for user with email: {email}")
        try:
            # Check in all three user collections
            user_data = await db.recruiters.find_one({"email": email})
            if not user_data:
                user_data = await db.consultants.find_one({"email": email})
            if not user_data:
                user_data = await db.admins.find_one({"email": email})
            
            if user_data:
                logger.debug(f"User found in database: {email}")
                
                # Step 4: Convert MongoDB _id to id (required by User model)
                logger.debug("Step 4: Converting MongoDB _id to id")
                user_data["id"] = str(user_data["_id"])
                logger.debug(f"User ID converted: {user_data['id']}")
                
                # Step 5: Create User object
                logger.debug("Step 5: Creating User object from database data")
                try:
                    user = User(**user_data)
                    logger.info(f"User retrieved successfully: {email}, ID: {user.id}, role: {user.role}")
                    return user
                except Exception as e:
                    logger.error(f"Error creating User object: {str(e)}", exc_info=True)
                    return None
            else:
                logger.debug(f"User not found with email: {email}")
                return None
        except Exception as e:
            logger.error(f"Database error while getting user by email: {str(e)}", exc_info=True)
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error getting user by email: {str(e)}", exc_info=True)
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token"""
    logger.debug("Getting current user from JWT token")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Step 1: Extract token from credentials
        logger.debug("Step 1: Extracting token from credentials")
        try:
            token = credentials.credentials
            logger.debug("Token extracted from credentials")
        except AttributeError as e:
            logger.error(f"Error extracting token from credentials: {str(e)}", exc_info=True)
            raise credentials_exception
        except Exception as e:
            logger.error(f"Unexpected error extracting token: {str(e)}", exc_info=True)
            raise credentials_exception
        
        # Step 2: Decode JWT token
        logger.debug("Step 2: Decoding JWT token")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.debug("JWT token decoded successfully")
        except JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"Unexpected error decoding JWT: {str(e)}", exc_info=True)
            raise credentials_exception
        
        # Step 3: Extract email from token payload
        logger.debug("Step 3: Extracting email from token payload")
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' (email) field")
            raise credentials_exception
        logger.debug(f"Email extracted from token: {email}")
        
        # Step 4: Create TokenData object
        logger.debug("Step 4: Creating TokenData object")
        try:
            token_data = TokenData(email=email)
            logger.debug("TokenData object created")
        except Exception as e:
            logger.error(f"Error creating TokenData: {str(e)}", exc_info=True)
            raise credentials_exception
        
        # Step 5: Get user from database
        logger.debug(f"Step 5: Retrieving user from database: {email}")
        user = await get_user_by_email(email=token_data.email)
        if user is None:
            logger.warning(f"User not found for token email: {email}")
            raise credentials_exception
        
        logger.info(f"Current user retrieved successfully: {email}, ID: {user.id}, role: {user.role}")
        return user
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting current user: {str(e)}", exc_info=True)
        raise credentials_exception

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    logger.debug(f"Creating role requirement decorator for role: {required_role}")
    
    def role_checker(current_user: User = Depends(get_current_user)):
        logger.debug(f"Checking role requirement - required: {required_role}, user role: {current_user.role}, user email: {current_user.email}")
        
        try:
            if current_user.role != required_role and current_user.role != UserRole.ADMIN:
                logger.warning(f"Role check failed - user {current_user.email} (role: {current_user.role}) does not have required role: {required_role}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            logger.debug(f"Role check passed - user {current_user.email} has required role or is admin")
            return current_user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in role checker: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error checking user role"
            )
    return role_checker

def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    logger.debug(f"Checking admin requirement for user: {current_user.email}, role: {current_user.role}")
    
    try:
        if current_user.role != UserRole.ADMIN:
            logger.warning(f"Admin check failed - user {current_user.email} (role: {current_user.role}) is not admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        logger.debug(f"Admin check passed - user {current_user.email} is admin")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin check: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking admin access"
        )

def require_recruiter_or_admin(current_user: User = Depends(get_current_user)):
    """Require recruiter or admin role"""
    logger.debug(f"Checking recruiter/admin requirement for user: {current_user.email}, role: {current_user.role}")
    
    try:
        allowed_roles = [UserRole.RECRUITER, UserRole.ADMIN]
        if current_user.role not in allowed_roles:
            logger.warning(f"Recruiter/admin check failed - user {current_user.email} (role: {current_user.role}) is not recruiter or admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Recruiter or admin access required"
            )
        logger.debug(f"Recruiter/admin check passed - user {current_user.email} has required role")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in recruiter/admin check: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking recruiter/admin access"
        )

def require_consultant_or_admin(current_user: User = Depends(get_current_user)):
    """Require consultant or admin role"""
    logger.debug(f"Checking consultant/admin requirement for user: {current_user.email}, role: {current_user.role}")
    
    try:
        allowed_roles = [UserRole.CONSULTANT, UserRole.ADMIN]
        if current_user.role not in allowed_roles:
            logger.warning(f"Consultant/admin check failed - user {current_user.email} (role: {current_user.role}) is not consultant or admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consultant or admin access required"
            )
        logger.debug(f"Consultant/admin check passed - user {current_user.email} has required role")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in consultant/admin check: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking consultant/admin access"
        )
