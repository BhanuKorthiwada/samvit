# SAMVIT Backend

AI-powered multi-tenant Human Resource Management System built with FastAPI.

## Architecture

**Modular Monolith** with Clean Architecture principles:

```
app/
├── core/           # Infrastructure (config, database, security, tenancy)
├── shared/         # Reusable base models, schemas, repositories
├── modules/        # Business domain modules
│   ├── tenants/    # Multi-tenant organization management
│   ├── auth/       # Authentication & RBAC
│   ├── employees/  # Employee management
│   ├── attendance/ # Time tracking
│   ├── leave/      # Leave management
│   └── payroll/    # Payroll processing
└── ai/
    └── agents/     # AI-powered conversational agents
```

## Tech Stack

- **Python 3.13+**
- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - Async ORM
- **Pydantic v2** - Data validation
- **Alembic** - Database migrations
- **PostgreSQL** - Database (via asyncpg)
- **JWT** - Authentication
- **LangGraph / Pydantic AI** - AI agents

## Quick Start

### 1. Setup Environment

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Required environment variables:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/samvit
SECRET_KEY=your-secret-key-here
```

### 3. Run Migrations

```bash
uv run alembic upgrade head
```

### 4. Start Development Server

```bash
# Development mode with auto-reload
uv run fastapi dev app/main.py

# Or using uvicorn directly
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

### Build Image

```bash
docker build -t samvit-backend .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/samvit \
  -e SECRET_KEY=your-secret-key \
  samvit-backend
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## API Endpoints

| Module | Prefix | Description |
|--------|--------|-------------|
| Auth | `/api/v1/auth` | Login, register, token refresh |
| Tenants | `/api/v1/tenants` | Organization management |
| Departments | `/api/v1/departments` | Department CRUD |
| Positions | `/api/v1/positions` | Position CRUD |
| Employees | `/api/v1/employees` | Employee CRUD, search |
| Attendance | `/api/v1/attendance` | Clock in/out, attendance reports |
| Leave | `/api/v1/leave` | Leave requests, policies, balances |
| Payroll | `/api/v1/payroll` | Salary structures, payslips |
| AI Chat | `/api/v1/ai/chat` | HR Assistant conversational interface |

## Multi-Tenancy

All requests require `X-Tenant-ID` header (except auth endpoints). Row-level security is enforced via `tenant_id` on all models.

```bash
curl -H "X-Tenant-ID: tenant-uuid" \
     -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/employees
```

## Development

### Run Tests

```bash
uv run pytest
uv run pytest --cov=app
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run mypy app/
```

### Create Migration

```bash
uv run alembic revision --autogenerate -m "description"
```

## Project Structure

Each module follows the same pattern:
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic schemas
- `service.py` - Business logic
- `repository.py` - Data access (optional)
- `routes.py` - API endpoints
- `__init__.py` - Module exports

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `ENVIRONMENT` | `development`, `staging`, `production` | `development` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |

## License

See [LICENSE](../LICENSE) in root directory.