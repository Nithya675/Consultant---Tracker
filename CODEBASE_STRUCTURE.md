# Consultant Tracker - Codebase Structure Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Core Infrastructure](#core-infrastructure)
5. [Module System](#module-system)
6. [Individual Modules](#individual-modules)
7. [Data Flow](#data-flow)
8. [Design Patterns](#design-patterns)
9. [Adding New Modules](#adding-new-modules)
10. [Configuration](#configuration)
11. [Database Schema](#database-schema)

---

## Overview

The Consultant Tracker is a **modular FastAPI application** designed for managing consultants, recruiters, jobs, and job submissions. The application follows a **clean architecture** pattern with clear separation of concerns.

### Key Features
- **Modular Architecture**: Each feature is a self-contained module
- **Dynamic Module Registration**: Modules are automatically discovered and registered
- **Centralized Configuration**: All settings in one place
- **MongoDB Database**: NoSQL database for flexible data storage
- **JWT Authentication**: Token-based authentication system
- **Role-Based Access Control**: Admin, Recruiter, and Consultant roles
- **Comprehensive Logging**: Structured logging with file rotation

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
│                         (main.py)                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐            ┌─────────▼──────────┐
│  Core Layer    │            │   Modules Layer    │
│                │            │                    │
│ - Config       │            │ - Auth             │
│ - Database     │            │ - Consultants      │
│ - Auth         │            │ - Recruiters       │
│ - Logging      │            │ - Jobs             │
│ - Models       │            │ - Submissions      │
│ - Schemas      │            │                    │
└───────┬────────┘            └─────────┬──────────┘
        │                               │
        └───────────────┬───────────────┘
                        │
                ┌───────▼────────┐
                │    MongoDB      │
                │   Database      │
                └─────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Core infrastructure is separate from business logic
2. **Modularity**: Each module is independent and self-contained
3. **Dependency Injection**: FastAPI's dependency system for clean code
4. **Repository Pattern**: Data access abstraction
5. **Schema Registry**: Centralized MongoDB collection management

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   │
│   ├── core/                      # Shared infrastructure
│   │   ├── __init__.py           # Core package exports
│   │   ├── config.py             # Application configuration
│   │   ├── db.py                 # Database connection & initialization
│   │   ├── auth.py               # Authentication & authorization
│   │   ├── models.py             # Core Pydantic models
│   │   ├── schemas.py            # Base MongoDB schema class
│   │   ├── schema_registry.py    # Schema registration system
│   │   └── logging_config.py    # Logging configuration
│   │
│   └── modules/                   # Business logic modules
│       ├── __init__.py           # Module registry & BaseModule
│       │
│       ├── auth/                 # Authentication module
│       │   ├── __init__.py       # Module registration
│       │   ├── module.py         # AuthModule class
│       │   ├── router.py         # API endpoints
│       │   ├── repository.py    # Business logic repository
│       │   ├── models.py         # Auth-specific models
│       │   ├── schema.py         # Auth schema (placeholder)
│       │   ├── user_repositories/ # User account repositories
│       │   │   ├── __init__.py
│       │   │   ├── admins.py
│       │   │   ├── consultants_user.py
│       │   │   └── recruiters.py
│       │   └── user_schemas/     # User account schemas
│       │       ├── __init__.py
│       │       ├── admins.py
│       │       ├── consultants_user.py
│       │       └── recruiters.py
│       │
│       ├── consultants/          # Consultant profiles module
│       │   ├── __init__.py
│       │   ├── module.py
│       │   ├── router.py
│       │   ├── repository.py
│       │   ├── models.py
│       │   └── schema.py
│       │
│       ├── recruiters/           # Recruiter profiles module
│       │   ├── __init__.py
│       │   ├── module.py
│       │   ├── router.py
│       │   ├── repository.py
│       │   ├── models.py
│       │   └── schema.py
│       │
│       ├── jobs/                 # Job descriptions module
│       │   ├── __init__.py
│       │   ├── module.py
│       │   ├── router.py
│       │   ├── repository.py
│       │   ├── models.py
│       │   └── schema.py
│       │
│       └── submissions/           # Job submissions module
│           ├── __init__.py
│           ├── module.py
│           ├── router.py
│           ├── repository.py
│           ├── models.py
│           └── schema.py
│
├── logs/                         # Application logs
├── uploads/                      # File uploads (resumes)
└── tests/                        # Test files
```

---

## Core Infrastructure

### 1. `core/config.py` - Configuration Management

**Purpose**: Centralized configuration using Pydantic Settings.

**Key Features**:
- Environment variable support
- Type validation
- Default values
- CORS configuration
- Database settings
- JWT settings

**Example**:
```python
from app.core.config import settings

# Access configuration
db_url = settings.MONGODB_URL
secret_key = settings.SECRET_KEY
```

**Configuration Categories**:
- **Database**: MongoDB URL, database name
- **Security**: JWT secret, algorithm, token expiration
- **CORS**: Allowed origins, methods, headers
- **API**: Title, description, version, prefix

---

### 2. `core/db.py` - Database Management

**Purpose**: MongoDB connection and initialization.

**Key Functions**:
- `get_database()`: Get MongoDB database instance
- `init_db()`: Initialize database and create indexes
- `close_db()`: Close database connection

**Features**:
- Async MongoDB driver (motor)
- Automatic index creation from schemas
- Connection pooling
- Error handling

**Index Creation**:
- Automatically discovers all registered schemas
- Creates indexes on application startup
- Handles duplicate index errors gracefully

---

### 3. `core/auth.py` - Authentication & Authorization

**Purpose**: User authentication and authorization utilities.

**Key Functions**:
- `get_password_hash()`: Hash passwords using bcrypt
- `verify_password()`: Verify password against hash
- `create_access_token()`: Generate JWT tokens
- `get_current_user()`: Get authenticated user from token
- `require_role()`: Role-based access control decorator
- `authenticate_user()`: Authenticate user credentials

**Security Features**:
- Bcrypt password hashing (72-byte limit handling)
- JWT token generation and validation
- Role-based access control (Admin, Recruiter, Consultant)
- Token expiration management

**Dependencies**:
- `Depends(get_current_user)`: FastAPI dependency for protected routes
- `require_admin`: Admin-only endpoints
- `require_recruiter_or_admin`: Recruiter/Admin endpoints

---

### 4. `core/models.py` - Core Data Models

**Purpose**: Shared Pydantic models used across modules.

**Key Models**:
- `User`: User account model
- `UserCreate`: User creation model
- `UserUpdate`: User update model
- `UserResponse`: User response model
- `UserRole`: Enum for user roles (ADMIN, RECRUITER, CONSULTANT)
- `Token`: Token response model
- `TokenData`: Token payload model

**Usage**:
```python
from app.core.models import User, UserRole, UserCreate

# Create user
user_data = UserCreate(
    email="user@example.com",
    password="password123",
    name="John Doe",
    role=UserRole.CONSULTANT
)
```

---

### 5. `core/schemas.py` - Base Schema Class

**Purpose**: Abstract base class for MongoDB collection schemas.

**Key Methods**:
- `get_collection_name()`: Return collection name (abstract)
- `create_indexes(db)`: Create indexes (abstract)
- `get_collection_config()`: Optional collection configuration

**Usage**:
```python
from app.core.schemas import CollectionSchema

class MySchema(CollectionSchema):
    @staticmethod
    def get_collection_name() -> str:
        return "my_collection"
    
    @staticmethod
    async def create_indexes(db):
        await db.my_collection.create_index("field", unique=True)
```

---

### 6. `core/schema_registry.py` - Schema Registry

**Purpose**: Centralized registration and management of MongoDB schemas.

**Key Features**:
- Lazy schema registration (avoids circular imports)
- Automatic schema discovery
- Schema lookup by collection name

**Registered Schemas**:
- User collections: `admins`, `consultants`, `recruiters`
- Profile collections: `consultant_profiles`, `recruiter_profiles`
- Business collections: `job_descriptions`, `submissions`

**Usage**:
```python
from app.core.schema_registry import get_all_schemas

# Get all registered schemas
schemas = get_all_schemas()
for schema in schemas:
    print(schema.get_collection_name())
```

---

### 7. `core/logging_config.py` - Logging Configuration

**Purpose**: Centralized logging setup.

**Features**:
- File rotation (RotatingFileHandler)
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Separate log files (app.log, errors.log, access.log)
- Console output
- Structured logging format

**Log Files**:
- `logs/app.log`: General application logs
- `logs/errors.log`: Error logs only
- `logs/access.log`: API access logs

---

## Module System

### BaseModule Interface

All modules must implement the `BaseModule` abstract class:

```python
class BaseModule(ABC):
    @abstractmethod
    def get_router(self):
        """Return FastAPI router"""
    
    @abstractmethod
    def get_module_name(self) -> str:
        """Return module name"""
    
    @abstractmethod
    def get_prefix(self) -> str:
        """Return API prefix"""
    
    def get_tags(self) -> List[str]:
        """Return OpenAPI tags"""
```

### Module Registration

Modules are automatically registered when imported:

```python
# In modules/auth/__init__.py
from .module import AuthModule
from app.modules import register_module

register_module(AuthModule)
```

### Module Discovery

`main.py` imports all modules and registers their routers:

```python
# Import modules (triggers registration)
import app.modules.auth
import app.modules.consultants
# ...

# Register routers
modules = get_all_modules()
for module_class in modules:
    module = module_class()
    app.include_router(
        module.get_router(),
        prefix=settings.API_PREFIX + module.get_prefix(),
        tags=module.get_tags()
    )
```

### Module Structure

Each module follows this structure:

```
module_name/
├── __init__.py      # Module registration
├── module.py        # Module class (implements BaseModule)
├── router.py        # API endpoints
├── repository.py    # Business logic & data access
├── models.py        # Pydantic models
└── schema.py        # MongoDB collection schema
```

---

## Individual Modules

### 1. Auth Module (`modules/auth/`)

**Purpose**: User authentication and account management.

**Components**:
- **Router** (`router.py`): Authentication endpoints
  - `POST /auth/register`: User registration
  - `POST /auth/login`: User login
  - `GET /auth/me`: Get current user
  - `POST /auth/refresh`: Refresh token
  - `POST /auth/logout`: Logout
  - `GET /auth/users`: List users (admin only)
  - `POST /auth/users`: Create user (admin only)
  - `PUT /auth/users/{id}`: Update user (admin only)
  - `DELETE /auth/users/{id}`: Delete user (admin only)

- **Repository** (`repository.py`): Business logic
  - `create_user()`: Create user account
  - `get_all_users()`: List all users
  - Delegates to user-specific repositories

- **User Repositories** (`user_repositories/`):
  - `AdminRepository`: Admin account operations
  - `ConsultantUserRepository`: Consultant account operations
  - `RecruiterRepository`: Recruiter account operations

- **User Schemas** (`user_schemas/`):
  - `AdminsSchema`: Admin collection indexes
  - `ConsultantsUserSchema`: Consultant collection indexes
  - `RecruitersSchema`: Recruiter collection indexes

**Collections**:
- `admins`: Admin user accounts
- `consultants`: Consultant user accounts
- `recruiters`: Recruiter user accounts
- `users`: Unified user view (optional)

---

### 2. Consultants Module (`modules/consultants/`)

**Purpose**: Consultant profile management.

**Components**:
- **Router** (`router.py`): Consultant endpoints
  - `GET /consultants`: List consultants
  - `GET /consultants/{id}`: Get consultant profile
  - `POST /consultants`: Create consultant profile
  - `PUT /consultants/{id}`: Update consultant profile
  - `DELETE /consultants/{id}`: Delete consultant profile
  - `POST /consultants/{id}/resume`: Upload resume
  - `GET /consultants/{id}/resume`: Download resume
  - `GET /consultants/{id}/stats`: Get application statistics

- **Repository** (`repository.py`): Data access
  - CRUD operations for consultant profiles
  - Resume file management
  - Statistics aggregation

- **Models** (`models.py`): Pydantic models
  - `ConsultantProfile`: Full profile model
  - `ConsultantProfileCreate`: Creation model
  - `ConsultantProfileUpdate`: Update model

- **Schema** (`schema.py`): MongoDB schema
  - Collection: `consultant_profiles`
  - Indexes: `user_id` (unique), `email`, `skills`, etc.

**Collection**: `consultant_profiles`

---

### 3. Recruiters Module (`modules/recruiters/`)

**Purpose**: Recruiter profile management.

**Components**:
- **Router** (`router.py`): Recruiter endpoints
  - `GET /recruiters`: List recruiters
  - `GET /recruiters/{id}`: Get recruiter profile
  - `POST /recruiters`: Create recruiter profile
  - `PUT /recruiters/{id}`: Update recruiter profile
  - `DELETE /recruiters/{id}`: Delete recruiter profile

- **Repository** (`repository.py`): Data access
  - CRUD operations for recruiter profiles

- **Models** (`models.py`): Pydantic models
  - `RecruiterProfile`: Full profile model
  - `RecruiterProfileCreate`: Creation model
  - `RecruiterProfileUpdate`: Update model

- **Schema** (`schema.py`): MongoDB schema
  - Collection: `recruiter_profiles`
  - Indexes: `user_id` (unique), `email`, etc.

**Collection**: `recruiter_profiles`

---

### 4. Jobs Module (`modules/jobs/`)

**Purpose**: Job description management.

**Components**:
- **Router** (`router.py`): Job endpoints
  - `GET /jobs`: List jobs
  - `GET /jobs/{id}`: Get job details
  - `POST /jobs`: Create job (recruiter/admin)
  - `PUT /jobs/{id}`: Update job (recruiter/admin)
  - `DELETE /jobs/{id}`: Delete job (recruiter/admin)

- **Repository** (`repository.py`): Data access
  - CRUD operations for job descriptions

- **Models** (`models.py`): Pydantic models
  - `JobDescription`: Full job model
  - `JobDescriptionCreate`: Creation model
  - `JobDescriptionUpdate`: Update model

- **Schema** (`schema.py`): MongoDB schema
  - Collection: `job_descriptions`
  - Indexes: `recruiter_id`, `title`, `status`, etc.

**Collection**: `job_descriptions`

---

### 5. Submissions Module (`modules/submissions/`)

**Purpose**: Job application/submission management.

**Components**:
- **Router** (`router.py`): Submission endpoints
  - `GET /submissions`: List submissions
  - `GET /submissions/{id}`: Get submission details
  - `POST /submissions`: Create submission
  - `PUT /submissions/{id}`: Update submission
  - `DELETE /submissions/{id}`: Delete submission
  - `PUT /submissions/{id}/status`: Update submission status

- **Repository** (`repository.py`): Data access
  - CRUD operations for submissions
  - Status management

- **Models** (`models.py`): Pydantic models
  - `Submission`: Full submission model
  - `SubmissionCreate`: Creation model
  - `SubmissionUpdate`: Update model
  - `SubmissionStatus`: Status enum

- **Schema** (`schema.py`): MongoDB schema
  - Collection: `submissions`
  - Indexes: `consultant_id`, `job_id`, `status`, etc.

**Collection**: `submissions`

---

## Data Flow

### Request Flow

```
1. Client Request
   ↓
2. FastAPI Middleware (CORS, Logging)
   ↓
3. Router (module/router.py)
   ↓
4. Authentication (if protected)
   ↓
5. Repository (module/repository.py)
   ↓
6. Database (MongoDB)
   ↓
7. Response (Pydantic models)
   ↓
8. Client Response
```

### Example: Creating a Consultant Profile

```
1. POST /api/consultants
   ↓
2. Router validates request (Pydantic model)
   ↓
3. Authentication check (get_current_user)
   ↓
4. Repository.create() called
   ↓
5. Database insert operation
   ↓
6. Return ConsultantProfile model
```

### Authentication Flow

```
1. POST /api/auth/login
   ↓
2. Router receives credentials
   ↓
3. authenticate_user() called
   ↓
4. get_user_by_email() queries database
   ↓
5. verify_password() checks password
   ↓
6. create_access_token() generates JWT
   ↓
7. Return token to client
```

---

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data access layer.

**Implementation**:
```python
class ConsultantRepository:
    async def create(self, data: ConsultantProfileCreate) -> ConsultantProfile:
        # Database operations
        pass
    
    async def get_by_id(self, id: str) -> Optional[ConsultantProfile]:
        # Database query
        pass
```

**Benefits**:
- Separation of concerns
- Easy testing (mock repositories)
- Database-agnostic business logic

---

### 2. Dependency Injection

**Purpose**: FastAPI's dependency system for clean code.

**Implementation**:
```python
@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user
```

**Benefits**:
- Automatic dependency resolution
- Reusable dependencies
- Easy testing

---

### 3. Module Registry Pattern

**Purpose**: Dynamic module discovery and registration.

**Implementation**:
```python
# Registry
_module_registry: List[Type[BaseModule]] = []

def register_module(module_class: Type[BaseModule]):
    _module_registry.append(module_class)

# Usage
register_module(AuthModule)
```

**Benefits**:
- Loose coupling
- Easy module addition
- Automatic discovery

---

### 4. Schema Registry Pattern

**Purpose**: Centralized MongoDB schema management.

**Implementation**:
```python
# Lazy registration
def _register_all_schemas():
    from app.modules.consultants.schema import ConsultantsSchema
    _register_schema(ConsultantsSchema)
```

**Benefits**:
- Avoids circular imports
- Centralized index management
- Easy schema discovery

---

## Adding New Modules

### Step-by-Step Guide

#### 1. Create Module Directory

```bash
mkdir -p app/modules/my_module
```

#### 2. Create Module Files

**`__init__.py`**:
```python
from .module import MyModule
from app.modules import register_module

register_module(MyModule)
```

**`module.py`**:
```python
from app.modules import BaseModule
from app.modules.my_module.router import router
from typing import List

class MyModule(BaseModule):
    def get_router(self):
        return router
    
    def get_module_name(self) -> str:
        return "my_module"
    
    def get_prefix(self) -> str:
        return "/my-module"
    
    def get_tags(self) -> List[str]:
        return ["my-module"]
```

**`router.py`**:
```python
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.core.models import User

router = APIRouter()

@router.get("/")
async def list_items(current_user: User = Depends(get_current_user)):
    return {"items": []}
```

**`repository.py`**:
```python
from app.core.db import get_database

class MyRepository:
    async def create(self, data):
        db = await get_database()
        # Database operations
        pass
```

**`models.py`**:
```python
from pydantic import BaseModel

class MyModel(BaseModel):
    id: str
    name: str
```

**`schema.py`**:
```python
from app.core.schemas import CollectionSchema

class MySchema(CollectionSchema):
    @staticmethod
    def get_collection_name() -> str:
        return "my_collection"
    
    @staticmethod
    async def create_indexes(db):
        await db.my_collection.create_index("name", unique=True)
```

#### 3. Register Schema

**`core/schema_registry.py`**:
```python
from app.modules.my_module.schema import MySchema

_register_schema(MySchema)
```

#### 4. Import Module

**`main.py`**:
```python
import app.modules.my_module
```

---

## Configuration

### Environment Variables

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=consultant_tracker

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Configuration File

All configuration is in `core/config.py`:

```python
class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "consultant_tracker")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret")
    # ...
```

---

## Database Schema

### Collections

1. **User Collections**:
   - `admins`: Admin user accounts
   - `consultants`: Consultant user accounts
   - `recruiters`: Recruiter user accounts
   - `users`: Unified user view (optional)

2. **Profile Collections**:
   - `consultant_profiles`: Consultant professional profiles
   - `recruiter_profiles`: Recruiter profiles

3. **Business Collections**:
   - `job_descriptions`: Job postings
   - `submissions`: Job applications

### Indexes

Each collection has indexes defined in its schema:

- **User Collections**: `email` (unique), `is_active`
- **Profile Collections**: `user_id` (unique), `email`
- **Business Collections**: Various indexes for query optimization

### Relationships

- `consultant_profiles.user_id` → `consultants._id`
- `recruiter_profiles.user_id` → `recruiters._id`
- `submissions.consultant_id` → `consultant_profiles._id`
- `submissions.job_id` → `job_descriptions._id`
- `job_descriptions.recruiter_id` → `recruiter_profiles._id`

---

## Key Files Reference

### Entry Point
- **`main.py`**: FastAPI application, middleware, module registration

### Core Infrastructure
- **`core/config.py`**: Configuration management
- **`core/db.py`**: Database connection
- **`core/auth.py`**: Authentication utilities
- **`core/models.py`**: Shared models
- **`core/schemas.py`**: Base schema class
- **`core/schema_registry.py`**: Schema registry
- **`core/logging_config.py`**: Logging setup

### Module System
- **`modules/__init__.py`**: BaseModule and registry
- **`modules/*/module.py`**: Module implementation
- **`modules/*/router.py`**: API endpoints
- **`modules/*/repository.py`**: Data access
- **`modules/*/models.py`**: Pydantic models
- **`modules/*/schema.py`**: MongoDB schema

---

## Best Practices

1. **Module Independence**: Each module should be self-contained
2. **Use Core Utilities**: Import from `app.core.*` for shared functionality
3. **Repository Pattern**: Always use repositories for data access
4. **Pydantic Models**: Use models for request/response validation
5. **Error Handling**: Use FastAPI's HTTPException for errors
6. **Logging**: Use structured logging throughout
7. **Type Hints**: Use type hints for better code clarity
8. **Async/Await**: Use async functions for database operations

---

## Testing

Test files are in the `tests/` directory:

- `test_consultants.py`: Consultant module tests
- `test_submissions.py`: Submission module tests

---

## Summary

This codebase follows a **clean, modular architecture** with:

- ✅ **Separation of Concerns**: Core vs. Business Logic
- ✅ **Modularity**: Independent, self-contained modules
- ✅ **Scalability**: Easy to add new modules
- ✅ **Maintainability**: Clear structure and patterns
- ✅ **Type Safety**: Pydantic models and type hints
- ✅ **Security**: JWT authentication and role-based access
- ✅ **Logging**: Comprehensive logging system

The architecture supports easy extension and maintenance, making it ideal for growing applications.

