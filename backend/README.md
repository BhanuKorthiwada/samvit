# SAMVIT Backend

AI-powered multi-tenant Human Resource Management System built with FastAPI.

## Features

- 🏢 **Multi-Tenancy** - Row-level security with tenant isolation
- 🔐 **JWT Authentication** - Secure auth with access & refresh tokens
- 👥 **Employee Management** - Departments, positions, employee records
- ⏰ **Attendance Tracking** - Clock in/out, shifts, attendance reports
- 🏖️ **Leave Management** - Policies, requests, balances, holidays
- 💰 **Payroll Processing** - Salary structures, components, payslips
- 🤖 **AI Assistant** - Conversational HR assistant powered by LangGraph
- 📊 **Structured Logging** - JSON logging with request tracing
- 🔍 **Health Monitoring** - Database connectivity checks

## Architecture

**Modular Monolith** with Clean Architecture principles:

```
app/
├── core/           # Infrastructure (config, database, security, logging, middleware)
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

- **Python 3.13+** - Latest Python features
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Async ORM with type hints
- **Pydantic v2** - Fast data validation
- **Alembic** - Database migrations with autogenerate
- **PostgreSQL/SQLite** - Production/development databases
- **bcrypt** - Secure password hashing
- **python-jose** - JWT token handling
- **LangGraph / Pydantic AI** - AI agent frameworks

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

# Edit .env with your settings
```

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|--------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./samvit.db` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Required in production |
| `ENVIRONMENT` | `development`, `staging`, `production` | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FORMAT` | `json` or `text` | `text` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3010"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiry | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token expiry | `7` |
| `BCRYPT_ROUNDS` | Password hashing rounds | `12` |

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
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run with coverage report
uv run pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Linting
uv run ruff check .
uv run ruff check . --fix  # Auto-fix

# Formatting
uv run ruff format .

# Type checking
uv run mypy app/
```

### Create Migration

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Project Structure

Each module follows the same pattern:
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic schemas
- `service.py` - Business logic
- `repository.py` - Data access (optional)
- `routes.py` - API endpoints
- `__init__.py` - Module exports

## Health Check

The `/health` endpoint provides application and database status:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app": "SAMVIT",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 1.23
    }
  }
}
```

## Request Tracing

All requests are traced with `X-Request-ID` header. Pass your own or let the server generate one:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8000/api/v1/employees
```

The response will include:
- `X-Request-ID` - The trace ID
- `X-Response-Time` - Request duration in ms

## License

See [LICENSE](../LICENSE) in root directory.