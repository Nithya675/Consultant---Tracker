"""
Authentication Router

API endpoints for user authentication and management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
import logging

from app.core.models import User, UserCreate, UserLogin, Token, UserRole, UserResponse
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.modules.auth.repository import AuthRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
repo = AuthRepository()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    logger.info(f"Registration request received for email: {user_data.email}, role: {user_data.role}")
    
    try:
        user = await repo.create_user(user_data)
        logger.info(f"User created successfully: {user.email}, ID: {user.id}")
        
        # Remove password from response
        user_dict = user.dict()
        if "hashed_password" in user_dict:
            del user_dict["hashed_password"]
        
        return UserResponse(**user_dict)
    except ValueError as e:
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected registration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user and return access token"""
    logger.info(f"Login attempt for email: {user_credentials.email}")
    
    try:
        user = await authenticate_user(user_credentials.email, user_credentials.password)
        if not user:
            logger.warning(f"Authentication failed: Invalid email or password for {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for deactivated account: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"Login successful for email: {user_credentials.email}, role: {user.role}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    logger.info(f"Get current user info request for: {current_user.email}")
    
    try:
        user_dict = current_user.dict()
        if "hashed_password" in user_dict:
            del user_dict["hashed_password"]
        
        return UserResponse(**user_dict)
    except Exception as e:
        logger.error(f"Error preparing user info response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    logger.info(f"Token refresh request for user: {current_user.email}")
    
    try:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"Token refreshed successfully for user: {current_user.email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout():
    """Logout user (client should discard token)"""
    logger.info("Logout request received")
    return {"message": "Successfully logged out"}

# Admin-only endpoints
@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    current_user: User = Depends(get_current_user)
):
    """Get all users (Admin only)"""
    logger.info(f"Get all users request from: {current_user.email}")
    
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Unauthorized access attempt: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        users = await repo.get_all_users(skip=skip, limit=limit, role=role)
        
        # Remove passwords from response
        response_users = []
        for user in users:
            user_dict = user.dict()
            if "hashed_password" in user_dict:
                del user_dict["hashed_password"]
            response_users.append(UserResponse(**user_dict))
        
        logger.info(f"Successfully retrieved {len(response_users)} users")
        return response_users
    except Exception as e:
        logger.error(f"Unexpected error getting all users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new user (Admin only)"""
    logger.info(f"Create user request from admin: {current_user.email}")
    
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Unauthorized access attempt: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        user = await repo.create_user(user_data)
        
        user_dict = user.dict()
        if "hashed_password" in user_dict:
            del user_dict["hashed_password"]
        
        logger.info(f"User created successfully by admin {current_user.email}")
        return UserResponse(**user_dict)
    except ValueError as e:
        logger.warning(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

