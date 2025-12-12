"""
Modules package - Individual business modules.

Each module is self-contained with its own:
- router.py: API endpoints
- repository.py: Database operations
- models.py: Pydantic models
- schema.py: MongoDB collection schema

Modules are automatically discovered and registered.
"""

from typing import List, Type, Optional
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseModule(ABC):
    """
    Base class for all modules.
    
    Each module should inherit from this class and implement:
    - get_router(): Return the FastAPI router
    - get_module_name(): Return the module name
    - get_prefix(): Return the API prefix (e.g., "/auth", "/consultants")
    """
    
    @abstractmethod
    def get_router(self):
        """Return the FastAPI router for this module"""
        raise NotImplementedError
    
    @abstractmethod
    def get_module_name(self) -> str:
        """Return the module name"""
        raise NotImplementedError
    
    @abstractmethod
    def get_prefix(self) -> str:
        """Return the API prefix for this module"""
        raise NotImplementedError
    
    def get_tags(self) -> List[str]:
        """Return OpenAPI tags for this module"""
        return [self.get_module_name().lower()]

# Module registry
_module_registry: List[Type[BaseModule]] = []

def register_module(module_class: Type[BaseModule]):
    """Register a module class"""
    if module_class not in _module_registry:
        _module_registry.append(module_class)
        logger.info(f"Registered module: {module_class.__name__}")

def get_all_modules() -> List[Type[BaseModule]]:
    """Get all registered modules"""
    return _module_registry.copy()

def get_module_by_name(name: str) -> Optional[Type[BaseModule]]:
    """Get a module by name"""
    for module_class in _module_registry:
        if module_class().get_module_name().lower() == name.lower():
            return module_class
    return None

__all__ = [
    "BaseModule",
    "register_module",
    "get_all_modules",
    "get_module_by_name",
]

