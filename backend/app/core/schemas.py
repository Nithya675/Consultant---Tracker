"""
Base Schema Class

Abstract base class for MongoDB collection schemas.
Used by all modules to define collection indexes.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CollectionSchema(ABC):
    """
    Abstract base class for MongoDB collection schemas.
    
    Each collection schema defines:
    - Collection name
    - Index definitions
    - Collection-specific configuration
    
    To create a new collection schema, inherit from this class and implement
    the required methods.
    """
    
    @staticmethod
    @abstractmethod
    def get_collection_name() -> str:
        """
        Return the MongoDB collection name.
        
        Returns:
            str: The name of the MongoDB collection
        """
        raise NotImplementedError("Subclasses must implement get_collection_name()")
    
    @staticmethod
    @abstractmethod
    async def create_indexes(db) -> None:
        """
        Create indexes for this collection.
        
        This method should define all indexes needed for the collection,
        including unique indexes, compound indexes, and text indexes.
        
        Args:
            db: The MongoDB database instance
            
        Raises:
            Exception: If index creation fails
        """
        raise NotImplementedError("Subclasses must implement create_indexes()")
    
    @staticmethod
    def get_collection_config() -> Optional[dict]:
        """
        Return optional collection configuration.
        
        This can include validation rules, default options, etc.
        Override this method if your collection needs special configuration.
        
        Returns:
            Optional[dict]: Collection configuration dictionary or None
        """
        return None

