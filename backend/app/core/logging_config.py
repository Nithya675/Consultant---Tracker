"""
Logging configuration for the Consultant Tracker application.

This module sets up file-based logging with rotation to handle concurrent requests
from multiple users safely. All log handlers are thread-safe and async-safe.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from app.core.config import settings

def setup_logging():
    """
    Configure application-wide logging with file handlers.
    
    Creates:
    - logs/app.log: All application logs (INFO and above)
    - logs/errors.log: Only errors and critical issues
    - logs/access.log: API access logs
    
    All handlers use rotation to prevent log files from growing too large.
    """
    # Create logs directory if it doesn't exist
    # Create in backend directory (where the app runs from)
    backend_dir = Path(__file__).parent.parent  # Go up from app/ to backend/
    log_dir = backend_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Format for log messages
    # Includes: timestamp, logger name, level, file:line, message
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simpler format for access logs
    access_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (for development - shows logs in terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(console_handler)
    
    # Main application log file (all logs)
    # Rotates when file reaches 10MB, keeps 5 backup files
    # RotatingFileHandler is thread-safe and handles concurrent writes
    app_file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_file_handler)
    
    # Error log file (only errors and critical issues)
    # Separate file for easier error tracking
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "errors.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Access log file (for API requests and user activities)
    # Useful for tracking user actions and API usage
    access_file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "access.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    access_file_handler.setLevel(logging.INFO)
    access_file_handler.setFormatter(access_formatter)
    
    # Create a separate logger for access logs
    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_file_handler)
    access_logger.propagate = False  # Don't propagate to root logger
    
    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Logging configuration initialized")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log directory: {log_dir.absolute()}")
    logger.info("Log files:")
    logger.info(f"  - {log_dir / 'app.log'} (all application logs)")
    logger.info(f"  - {log_dir / 'errors.log'} (errors only)")
    logger.info(f"  - {log_dir / 'access.log'} (API access logs)")
    logger.info("=" * 60)

