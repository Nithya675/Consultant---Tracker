"""
Centralized configuration for the Consultant Tracker backend application.

All configuration variables are defined here and can be overridden via environment variables.
"""
import os
from typing import List
import logging

# Set up logger
logger = logging.getLogger(__name__)

class Settings:
    """Application settings - all configuration in one place"""
    
    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "consultant_tracker")
    
    # ============================================================================
    # SECURITY & AUTHENTICATION
    # ============================================================================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Password hashing configuration
    PASSWORD_HASH_SCHEMES: List[str] = ["bcrypt"]
    PASSWORD_MAX_BYTES: int = 72  # bcrypt limitation
    
    # ============================================================================
    # CORS CONFIGURATION
    # ============================================================================
    # Default allowed origins for CORS
    DEFAULT_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://frontend:3000",
    ]
    
    # Additional origins from environment (comma-separated)
    CORS_ORIGINS_ENV: str = os.getenv("CORS_ORIGINS", "")
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get all allowed CORS origins (default + environment)"""
        origins = cls.DEFAULT_CORS_ORIGINS.copy()
        
        if cls.CORS_ORIGINS_ENV:
            try:
                additional_origins = [
                    origin.strip() 
                    for origin in cls.CORS_ORIGINS_ENV.split(",") 
                    if origin.strip()
                ]
                origins.extend(additional_origins)
                logger.info(f"Added {len(additional_origins)} additional CORS origins from environment")
            except Exception as e:
                logger.error(f"Error parsing CORS_ORIGINS environment variable: {str(e)}")
        
        return origins
    
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_EXPOSE_HEADERS: List[str] = ["*"]
    
    # ============================================================================
    # API CONFIGURATION
    # ============================================================================
    API_TITLE: str = "Consultant Tracker API"
    API_DESCRIPTION: str = "API for consultant and recruiter management"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # ============================================================================
    # FILE UPLOAD CONFIGURATION
    # ============================================================================
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))  # 10MB default
    ALLOWED_RESUME_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx"]
    ALLOWED_JD_FILE_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx"]
    
    # ============================================================================
    # AI SERVICE CONFIGURATION (Google Gemini)
    # ============================================================================
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-pro")
    GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "30"))  # seconds
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ============================================================================
    # APPLICATION ENVIRONMENT
    # ============================================================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def validate_settings(cls) -> None:
        """Validate critical settings and log warnings"""
        logger.info("=" * 60)
        logger.info("Configuration Settings Validation")
        logger.info("=" * 60)
        
        # Check SECRET_KEY
        if cls.SECRET_KEY == "your-secret-key-change-this-in-production":
            logger.warning("⚠️  Using default SECRET_KEY - CHANGE THIS IN PRODUCTION!")
        else:
            logger.info("✓ SECRET_KEY is set (custom value)")
        
        # Check environment
        logger.info(f"✓ Environment: {cls.ENVIRONMENT}")
        logger.info(f"✓ Debug mode: {cls.DEBUG}")
        
        # Check database
        # Mask password in URL for logging
        masked_url = cls.MONGODB_URL.replace('://', '://***') if '://' in cls.MONGODB_URL else '***'
        logger.info(f"✓ MongoDB URL: {masked_url}")
        logger.info(f"✓ Database name: {cls.DATABASE_NAME}")
        
        # Check CORS
        cors_origins = cls.get_cors_origins()
        logger.info(f"✓ CORS origins configured: {len(cors_origins)} origins")
        
        # Check token expiration
        logger.info(f"✓ Access token expiration: {cls.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        
        # Production-specific checks
        if cls.is_production():
            logger.info("=" * 60)
            logger.info("PRODUCTION MODE - Additional Checks")
            logger.info("=" * 60)
            
            if cls.SECRET_KEY == "your-secret-key-change-this-in-production":
                logger.critical("🚨 CRITICAL: Using default SECRET_KEY in production!")
            
            if cls.DEBUG:
                logger.warning("⚠️  Debug mode is enabled in production!")
        
        logger.info("=" * 60)


# Create a singleton instance
settings = Settings()

# Log configuration on module load
logger.debug(f"Configuration module loaded - Environment: {settings.ENVIRONMENT}")
