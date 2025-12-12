"""
Schema Registry Module

Centralized registry for all MongoDB collection schemas.
Automatically discovers and registers schemas from all modules.
"""

from typing import List, Type
import logging
from app.core.schemas import CollectionSchema

logger = logging.getLogger(__name__)

# Registry to store all schema classes
_registry: List[Type[CollectionSchema]] = []


def _register_schema(schema_class: Type[CollectionSchema]) -> None:
    """
    Register a schema class in the registry.
    
    Args:
        schema_class: The schema class to register
    """
    if schema_class not in _registry:
        _registry.append(schema_class)
        logger.debug(f"Registered schema: {schema_class.__name__} for collection: {schema_class.get_collection_name()}")




def get_schema_by_collection_name(collection_name: str) -> Type[CollectionSchema] | None:
    """
    Get a schema class by collection name.
    
    Args:
        collection_name: The name of the MongoDB collection
        
    Returns:
        Type[CollectionSchema] | None: The schema class if found, None otherwise
    """
    _register_all_schemas()  # Ensure schemas are registered
    for schema_class in _registry:
        if schema_class.get_collection_name() == collection_name:
            return schema_class
    return None


# Lazy import and registration of schemas to avoid circular imports
def _register_all_schemas():
    """Register all schemas from modules. Called after modules are loaded."""
    if _registry:  # Already registered
        return
    
    # Import and register all schemas from modules
    # Profile collection schemas (from business modules)
    from app.modules.consultants.schema import ConsultantsSchema as ConsultantProfilesSchema
    from app.modules.recruiters.schema import RecruitersSchema as RecruiterProfilesSchema
    from app.modules.jobs.schema import JobsSchema
    from app.modules.submissions.schema import SubmissionsSchema

    # User account collection schemas (from auth module)
    from app.modules.auth.user_schemas.admins import AdminsSchema
    from app.modules.auth.user_schemas.consultants_user import ConsultantsUserSchema
    from app.modules.auth.user_schemas.recruiters import RecruitersSchema

    # Auto-register all imported schemas
    _register_schema(ConsultantProfilesSchema)  # consultant_profiles collection
    _register_schema(RecruiterProfilesSchema)  # recruiter_profiles collection
    _register_schema(JobsSchema)  # job_descriptions collection
    _register_schema(SubmissionsSchema)  # submissions collection
    _register_schema(RecruitersSchema)  # recruiters user collection
    _register_schema(ConsultantsUserSchema)  # consultants user collection
    _register_schema(AdminsSchema)  # admins user collection

    logger.info(f"Schema registry initialized with {len(_registry)} schemas: {[s.get_collection_name() for s in _registry]}")


def get_all_schemas() -> List[Type[CollectionSchema]]:
    """
    Get all registered schema classes.
    
    Returns:
        List[Type[CollectionSchema]]: List of all registered schema classes
    """
    _register_all_schemas()  # Ensure schemas are registered
    return _registry.copy()

__all__ = [
    'CollectionSchema',
    'RecruitersSchema',  # User collection
    'ConsultantsUserSchema',  # User collection
    'AdminsSchema',  # User collection
    'ConsultantProfilesSchema',  # Profile collection
    'RecruiterProfilesSchema',  # Profile collection
    'JobsSchema',
    'SubmissionsSchema',
    'get_all_schemas',
    'get_schema_by_collection_name',
]

