# Consultant Tracker

A comprehensive **modular FastAPI application** for managing consultants, recruiters, job postings, and job submissions. Built with a clean, scalable architecture that supports role-based access control and dynamic module registration.

## 🚀 Features

### Core Features
- ✅ **User Authentication** - JWT-based authentication with role-based access control
- ✅ **Modular Architecture** - Self-contained modules for easy maintenance and extension
- ✅ **Role-Based Access Control** - Admin, Recruiter, and Consultant roles
- ✅ **Consultant Management** - Profile management, resume upload/download
- ✅ **Recruiter Management** - Recruiter profile management
- ✅ **Job Management** - Create, update, and manage job postings
- ✅ **Submission Management** - Track job applications and submissions
- ✅ **Comprehensive Logging** - Structured logging with file rotation
- ✅ **RESTful API** - Clean API design with OpenAPI documentation

### User Roles

1. **ADMIN** - Full system access, user management
2. **RECRUITER** - Manage jobs, view consultants, manage submissions
3. **CONSULTANT** - View jobs, create profile, submit applications

---

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation and settings
- **JWT** - Token-based authentication (python-jose)
- **Bcrypt** - Password hashing (passlib)
- **Python 3.8+** - Programming language

### Frontend
- **React 18** - UI library
- **Material-UI (MUI)** - Component library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework
- **Chart.js / Recharts** - Data visualization

---

## 📁 Project Structure

```
Consultant--Tracker/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point
│   │   │
│   │   ├── core/                      # Shared infrastructure
│   │   │   ├── config.py             # Application configuration
│   │   │   ├── db.py                 # Database connection
│   │   │   ├── auth.py               # Authentication utilities
│   │   │   ├── models.py             # Core Pydantic models
│   │   │   ├── schemas.py            # Base MongoDB schema class
│   │   │   ├── schema_registry.py    # Schema registration system
│   │   │   └── logging_config.py    # Logging configuration
│   │   │
│   │   └── modules/                   # Business logic modules
│   │       ├── __init__.py           # Module registry & BaseModule
│   │       │
│   │       ├── auth/                 # Authentication module
│   │       │   ├── router.py         # Auth endpoints
│   │       │   ├── repository.py    # Auth business logic
│   │       │   ├── models.py         # Auth models
│   │       │   ├── schema.py         # Auth schema
│   │       │   ├── user_repositories/ # User account repositories
│   │       │   └── user_schemas/     # User account schemas
│   │       │
│   │       ├── consultants/          # Consultant profiles module
│   │       ├── recruiters/           # Recruiter profiles module
│   │       ├── jobs/                 # Job descriptions module
│   │       └── submissions/          # Job submissions module
│   │
│   ├── logs/                          # Application logs
│   ├── uploads/                      # File uploads (resumes)
│   ├── tests/                        # Test files
│   └── requirements.txt              # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── api.js                    # API client
│   │   ├── App.js                    # Main app component
│   │   ├── config.js                 # Frontend configuration
│   │   ├── components/
│   │   │   ├── auth/                # Authentication components
│   │   │   ├── consultant/          # Consultant components
│   │   │   ├── recruiter/           # Recruiter components
│   │   │   └── ui/                  # UI components
│   │   └── contexts/
│   │       └── AuthContext.js        # Authentication context
│   └── package.json
│
├── CODEBASE_STRUCTURE.md             # Detailed architecture documentation
├── TEST_CASES.md                     # Test cases documentation
└── README.md                          # This file
```

---

## 🏗 Architecture

The application follows a **modular architecture** pattern:

- **Core Layer**: Shared infrastructure (config, database, auth, logging)
- **Modules Layer**: Self-contained business modules
- **Dynamic Registration**: Modules are automatically discovered and registered

Each module contains:
- `router.py` - API endpoints
- `repository.py` - Business logic & data access
- `models.py` - Pydantic models
- `schema.py` - MongoDB collection schema
- `module.py` - Module class implementing BaseModule

For detailed architecture documentation, see [CODEBASE_STRUCTURE.md](./CODEBASE_STRUCTURE.md).

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** and npm
- **MongoDB 4.4+** (running locally or accessible)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Or using `uv` (recommended):
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional):
   ```bash
   # Create .env file or set environment variables
   export MONGODB_URL="mongodb://localhost:27017"
   export DATABASE_NAME="consultant_tracker"
   export SECRET_KEY="your-secret-key-here"
   export ACCESS_TOKEN_EXPIRE_MINUTES=30
   export CORS_ORIGINS="http://localhost:3000,http://localhost:3001"
   ```

5. **Start MongoDB:**
   - Make sure MongoDB is running on `localhost:27017`
   - Or update `MONGODB_URL` to point to your MongoDB instance

6. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at:
   - API: `http://localhost:8000/api`
   - Docs: `http://localhost:8000/docs` (Swagger UI)
   - ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure API URL** (if needed):
   - Default: `http://localhost:8000/api`
   - Update in `src/config.js` or set `REACT_APP_API_URL` environment variable

4. **Start the frontend:**
   ```bash
   npm start
   ```

   The frontend will run on `http://localhost:3000` (or next available port).

---

## 📡 API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/login` | Login user | No |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/refresh` | Refresh access token | Yes |
| POST | `/api/auth/logout` | Logout user | Yes |
| GET | `/api/auth/users` | List all users | Admin |
| POST | `/api/auth/users` | Create user | Admin |
| PUT | `/api/auth/users/{id}` | Update user | Admin |
| DELETE | `/api/auth/users/{id}` | Delete user | Admin |

### Consultants (`/api/consultants`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/consultants` | List consultants | Yes |
| GET | `/api/consultants/{id}` | Get consultant profile | Yes |
| POST | `/api/consultants` | Create consultant profile | Consultant |
| PUT | `/api/consultants/{id}` | Update consultant profile | Consultant/Owner |
| DELETE | `/api/consultants/{id}` | Delete consultant profile | Consultant/Owner |
| POST | `/api/consultants/{id}/resume` | Upload resume | Consultant/Owner |
| GET | `/api/consultants/{id}/resume` | Download resume | Yes |
| GET | `/api/consultants/{id}/stats` | Get application statistics | Consultant/Owner |

### Recruiters (`/api/recruiters`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/recruiters` | List recruiters | Yes |
| GET | `/api/recruiters/{id}` | Get recruiter profile | Yes |
| POST | `/api/recruiters` | Create recruiter profile | Recruiter |
| PUT | `/api/recruiters/{id}` | Update recruiter profile | Recruiter/Owner |
| DELETE | `/api/recruiters/{id}` | Delete recruiter profile | Recruiter/Owner |

### Jobs (`/api/jobs`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/jobs` | List jobs | Yes |
| GET | `/api/jobs/{id}` | Get job details | Yes |
| POST | `/api/jobs` | Create job | Recruiter/Admin |
| PUT | `/api/jobs/{id}` | Update job | Recruiter/Admin |
| DELETE | `/api/jobs/{id}` | Delete job | Recruiter/Admin |

### Submissions (`/api/submissions`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/submissions` | List submissions | Yes |
| GET | `/api/submissions/{id}` | Get submission details | Yes |
| POST | `/api/submissions` | Create submission | Consultant |
| PUT | `/api/submissions/{id}` | Update submission | Consultant/Owner |
| DELETE | `/api/submissions/{id}` | Delete submission | Consultant/Owner |
| PUT | `/api/submissions/{id}/status` | Update submission status | Recruiter/Admin |

### Health & Info

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information | No |
| GET | `/health` | Health check | No |

---

## 🔐 Authentication

### Register a User

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "password123",
  "role": "CONSULTANT"
}
```

**Roles**: `ADMIN`, `RECRUITER`, `CONSULTANT`

### Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
Authorization: Bearer <access_token>
```

---

## ⚙️ Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `consultant_tracker` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-change-this-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration (minutes) | `30` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://localhost:3001` |
| `API_PREFIX` | API route prefix | `/api` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000/api` |

---

## 📊 Database Schema

### Collections

**User Collections:**
- `admins` - Admin user accounts
- `consultants` - Consultant user accounts
- `recruiters` - Recruiter user accounts

**Profile Collections:**
- `consultant_profiles` - Consultant professional profiles
- `recruiter_profiles` - Recruiter profiles

**Business Collections:**
- `job_descriptions` - Job postings
- `submissions` - Job applications

### Indexes

Each collection has optimized indexes:
- User collections: `email` (unique), `is_active`
- Profile collections: `user_id` (unique), `email`
- Business collections: Various indexes for query optimization

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Manual Testing

1. **Register a user:**
   - Navigate to `http://localhost:3000/register`
   - Fill in the form and select a role
   - Submit to create an account

2. **Login:**
   - Navigate to `http://localhost:3000/login`
   - Enter your email and password
   - You'll be redirected to the dashboard

3. **API Testing:**
   - Use Swagger UI at `http://localhost:8000/docs`
   - Or use tools like Postman/Insomnia

For detailed test cases, see [TEST_CASES.md](./TEST_CASES.md).

---

## 📝 Password Requirements

- **Minimum**: 6 characters
- **Maximum**: 72 bytes (bcrypt limitation)
- For ASCII characters, this is approximately 72 characters
- Special characters or emojis use multiple bytes per character

---

## 📚 Documentation

- **[CODEBASE_STRUCTURE.md](./CODEBASE_STRUCTURE.md)** - Detailed architecture documentation
- **[TEST_CASES.md](./TEST_CASES.md)** - Test cases and scenarios
- **API Documentation**: Available at `http://localhost:8000/docs` (Swagger UI)

---

## 🏗 Adding New Modules

The application uses a modular architecture. To add a new module:

1. Create module directory: `app/modules/my_module/`
2. Implement `BaseModule` interface
3. Create router, repository, models, and schema
4. Register module in `__init__.py`
5. Import module in `main.py`

For detailed instructions, see [CODEBASE_STRUCTURE.md](./CODEBASE_STRUCTURE.md#adding-new-modules).

---

## 🔧 Development

### Logging

Logs are stored in `backend/logs/`:
- `app.log` - General application logs
- `errors.log` - Error logs only
- `access.log` - API access logs

### File Uploads

Uploaded files (resumes) are stored in `backend/uploads/`.

### Code Structure

- **Core**: Shared infrastructure in `app/core/`
- **Modules**: Business logic in `app/modules/`
- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: FastAPI's dependency system

---

## 🚨 Troubleshooting

### Backend Issues

**Database Connection Error:**
- Ensure MongoDB is running
- Check `MONGODB_URL` environment variable
- Verify network connectivity

**Import Errors:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version (3.8+)

**Port Already in Use:**
- Change port: `uvicorn app.main:app --port 8001`
- Or stop the process using port 8000

### Frontend Issues

**API Connection Error:**
- Verify backend is running on port 8000
- Check `REACT_APP_API_URL` in `src/config.js`
- Check CORS configuration in backend

**Module Not Found:**
- Run `npm install` to install dependencies
- Clear cache: `npm start -- --reset-cache`

---

## 📄 License

This project is private and proprietary.

---

## 🤝 Contributing

This is a private project. For questions or issues, contact the development team.

---

## 📞 Support

For issues or questions:
1. Check the documentation in `CODEBASE_STRUCTURE.md`
2. Review test cases in `TEST_CASES.md`
3. Check API documentation at `/docs` endpoint

---

**Built with ❤️ using FastAPI and React**
