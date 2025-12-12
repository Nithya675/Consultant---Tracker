from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
import os
import logging
import time
from app.core.db import init_db, close_db
from app.core.logging_config import setup_logging
from app.core.config import settings
from app.modules import get_all_modules

# IMPORTANT: Setup logging FIRST before any other logging
setup_logging()

# Set up logger (after logging is configured)
logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    logger.info("=" * 60)
    logger.info("Application startup initiated")
    logger.info("=" * 60)
    
    # Startup
    try:
        logger.debug("Step 1: Validating configuration settings")
        try:
            settings.validate_settings()
            logger.info("Configuration validation completed successfully")
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}", exc_info=True)
            # Continue anyway - validation is informational
        
        logger.debug("Step 2: Initializing database connection")
        try:
            await init_db()
            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.critical(f"CRITICAL: Database initialization failed: {str(e)}", exc_info=True)
            # Re-raise to prevent app from starting without database
            raise
    
    except Exception as e:
        logger.critical(f"CRITICAL: Application startup failed: {str(e)}", exc_info=True)
        raise
    
    logger.info("Application startup completed successfully")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Application shutdown initiated")
    logger.info("=" * 60)
    
    try:
        logger.debug("Step 1: Closing database connection")
        try:
            await close_db()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}", exc_info=True)
            # Don't raise - try to continue shutdown
    
    except Exception as e:
        logger.error(f"Error during application shutdown: {str(e)}", exc_info=True)
    
    logger.info("Application shutdown completed")
    logger.info("=" * 60)

# Create FastAPI application
logger.info("Creating FastAPI application instance")
try:
    fastapi_app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        lifespan=lifespan
    )
    logger.info(f"FastAPI application created: {fastapi_app.title} v{fastapi_app.version}")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to create FastAPI application: {str(e)}", exc_info=True)
    raise

# CORS middleware - Configure for development
logger.info("Configuring CORS middleware")
try:
    # Get allowed origins from configuration
    logger.debug("Getting allowed CORS origins from configuration")
    allowed_origins = settings.get_cors_origins()
    
    logger.info(f"Total allowed CORS origins: {len(allowed_origins)}")
    logger.debug(f"Allowed origins: {allowed_origins}")
    
    # Add CORS middleware
    logger.debug("Adding CORS middleware to application")
    try:
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )
        logger.info("CORS middleware configured successfully")
    except Exception as e:
        logger.error(f"Error adding CORS middleware: {str(e)}", exc_info=True)
        raise

except Exception as e:
    logger.error(f"Error configuring CORS: {str(e)}", exc_info=True)
    raise

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for access logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Start time
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        access_logger.info(
            f"{request.method} {request.url.path} - "
            f"Client: {client_ip} - "
            f"Query: {dict(request.query_params)}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            access_logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - "
                f"Client: {client_ip}"
            )
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            access_logger.error(
                f"{request.method} {request.url.path} - "
                f"ERROR: {str(e)} - "
                f"Duration: {duration:.3f}s - "
                f"Client: {client_ip}"
            )
            raise

# Add request logging middleware
logger.info("Adding request logging middleware")
try:
    fastapi_app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware configured successfully")
except Exception as e:
    logger.error(f"Error adding request logging middleware: {str(e)}", exc_info=True)
    raise

# Import all modules to trigger auto-registration
# This ensures all modules are registered in the module registry
try:
    logger.debug("Importing modules to trigger auto-registration")
    import app.modules.auth
    import app.modules.consultants
    import app.modules.recruiters
    import app.modules.jobs
    import app.modules.submissions
    logger.info("All modules imported successfully")
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}", exc_info=True)
    raise

# Register all modules dynamically
logger.info("Registering application modules")
try:
    logger.debug("Getting all registered modules")
    modules = get_all_modules()
    logger.info(f"Found {len(modules)} module(s) to register")
    
    for module_class in modules:
        try:
            module = module_class()
            module_name = module.get_module_name()
            prefix = module.get_prefix()
            tags = module.get_tags()
            
            logger.debug(f"Registering module: {module_name} at {settings.API_PREFIX}{prefix}")
            fastapi_app.include_router(
                module.get_router(),
                prefix=settings.API_PREFIX,
                tags=tags
            )
            logger.info(f"Module '{module_name}' registered successfully")
        except Exception as e:
            logger.error(f"Error registering module {module_class.__name__}: {str(e)}", exc_info=True)
            raise
    
    logger.info(f"All {len(modules)} module(s) registered successfully at {settings.API_PREFIX}")
except Exception as e:
    logger.error(f"Error registering modules: {str(e)}", exc_info=True)
    raise

@fastapi_app.get("/")
async def root():
    """Root endpoint - API information"""
    logger.debug("Root endpoint accessed")
    
    try:
        response = {
            "message": "Consultant Tracker API - Authentication Service",
            "version": "1.0.0"
        }
        logger.debug(f"Root endpoint response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving API information"
        )

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint accessed")
    
    try:
        # You could add more health checks here (database, external services, etc.)
        logger.debug("Performing health check")
        
        response = {"status": "healthy"}
        logger.debug(f"Health check response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in health check endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

# Export app for uvicorn
app = fastapi_app

