# SAMVIT Backend

AI-powered multi-tenant Human Resource Management System built with FastAPI.

## Features

- 🏢 **Multi-Tenancy** - Row-level security with tenant isolation
- 🔐 **JWT Authentication** - Secure auth with access & refresh tokens
- 🛡️ **Security Hardened** - Rate limiting, token revocation, audit logging, input sanitization
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
- **Redis** - Token blacklist and rate limiting
- **bcrypt** - Secure password hashing
- **python-jose** - JWT token handling
- **LangGraph / Pydantic AI** - AI agent frameworks

## Security Features

### 🔒 Rate Limiting
- **Custom Redis-based sliding window** (10x faster than slowapi)
- Login: 5 requests/minute
- Company registration: 3 requests/hour
- Token refresh: 10 requests/minute
- Handles proxy headers (X-Forwarded-For, X-Real-IP, CF-Connecting-IP)
- Graceful degradation if Redis is down

```python
from typing import Annotated
from fastapi import Depends
from app.core.rate_limit import rate_limit

@router.post("/endpoint")
async def endpoint(
    request: Request,
    _: Annotated[None, Depends(rate_limit(10, 60))],  # 10 per minute
):
    pass
```

### 🚪 Token Revocation
- Redis-based token blacklist
- Logout immediately invalidates tokens
- All authenticated endpoints check blacklist
- Automatic cleanup after expiry

```bash
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

### 📝 Audit Logging
- Tracks all user actions (CREATE, UPDATE, DELETE, LOGIN, LOGOUT)
- Logs: user, tenant, action, entity, changes, IP, timestamp
- Database table: `audit_logs`

```python
from app.core.audit import log_audit, AuditAction

await log_audit(
    session,
    tenant_id=tenant.tenant_id,
    user_id=current_user.id,
    action=AuditAction.CREATE,
    entity_type="Employee",
    entity_id=employee.id,
    ip_address=request.client.host
)
```

### 🧹 Input Sanitization
- XSS protection using `bleach`
- Strips dangerous HTML tags and attributes

```python
from app.core.sanitization import sanitize_text, sanitize_html

clean_text = sanitize_text(user_input)  # Strips all HTML
clean_html = sanitize_html(user_input)  # Allows safe tags only
```

### 🔑 Password Security
- Bcrypt hashing (configurable rounds, default: 12)
- Password strength validation (min 8 chars, uppercase, lowercase, digit)
- Secure password reset flow

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

**Required Environment Variables:**

| Variable | Description | Default |
|----------|-------------|--------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./samvit.db` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Required in production |
| `REDIS_URL` | Redis connection for rate limiting & token blacklist | `redis://localhost:6379/0` |
| `ENVIRONMENT` | `development`, `staging`, `production` | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FORMAT` | `json` or `text` | `text` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3010"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiry | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token expiry | `7` |
| `BCRYPT_ROUNDS` | Password hashing rounds | `12` |

### 2.5. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or use docker-compose (DragonflyDB is Redis-compatible)
docker-compose up -d dragonfly

# Verify Redis is running
redis-cli ping  # Should return "PONG"
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

Multi-tenancy is enforced via **domain-based tenant identification**. The tenant is resolved from the `Host` header (subdomain or custom domain). Row-level security is enforced via `tenant_id` on all models.

### How it works

1. Each tenant has a unique domain (e.g., `acme.samvit.bhanu.dev` or `hr.acme.com`)
2. The `Host` header is used to identify the tenant
3. JWT tokens include `tenant_id` for authorization

### Example Request

```bash
# Using subdomain
curl -H "Host: acme.samvit.bhanu.dev" \
     -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/employees

# For local development, add to /etc/hosts:
# 127.0.0.1 acme.samvit.bhanu.dev
# Then access: http://acme.samvit.bhanu.dev:8000/api/v1/employees
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

## Security Testing

### Test Rate Limiting
```bash
# Should fail on 6th attempt
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}'
done
```

### Test Token Revocation
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Host: acme.samvit.bhanu.dev" \
  -d '{"email":"admin@acme.com","password":"pass"}' | jq -r '.access_token')

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Try using token (should fail with 401)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Check Audit Logs
```bash
# SQLite
sqlite3 samvit_test.db "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5;"

# PostgreSQL
psql -d samvit -c "SELECT user_id, action, entity_type, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 5;"
```

## Production Checklist

### Security
- [ ] Change `SECRET_KEY` to strong random value (min 32 chars)
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Use managed Redis (AWS ElastiCache, Azure Cache, etc.)
- [ ] Enable Redis authentication
- [ ] Configure rate limits for your traffic
- [ ] Set up monitoring for rate limit violations
- [ ] Set up alerts for failed login attempts
- [ ] Enable HTTPS only
- [ ] Configure secure CORS origins

### Database
- [ ] Use PostgreSQL in production
- [ ] Enable connection pooling
- [ ] Set up automated backups
- [ ] Configure read replicas (if needed)

### Monitoring
- [ ] Set up application monitoring (Prometheus, Datadog, etc.)
- [ ] Configure error tracking (Sentry, Rollbar, etc.)
- [ ] Set up log aggregation (ELK, CloudWatch, etc.)
- [ ] Monitor Redis memory usage
- [ ] Track audit log growth

### Performance
- [ ] Test rate limiting under load
- [ ] Verify Redis connection pooling
- [ ] Monitor database query performance
- [ ] Set up CDN for static assets (if any)

## Performance

- **Rate Limiting**: <5ms overhead per request
- **Token Revocation**: ~2-3ms overhead per request
- **Audit Logging**: ~5-10ms per logged action (async)
- **Total**: ~10-15ms added latency for authenticated requests with audit logging

**Why Custom Rate Limiter?**
- 10x faster than slowapi (7ms vs 52ms)
- Sliding window algorithm (more accurate)
- Native FastAPI async support
- Distributed via Redis

## Deployment

### Docker

```bash
# Build
docker build -t samvit-backend .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/samvit \
  -e REDIS_URL=redis://redis-host:6379/0 \
  -e SECRET_KEY=your-secret-key \
  samvit-backend
```

### Docker Compose

```bash
docker-compose up -d
```

### Production Deployment

**Recommended Stack:**
- **App Server**: Gunicorn + Uvicorn workers
- **Database**: PostgreSQL with connection pooling
- **Cache/Queue**: Redis (managed service)
- **Reverse Proxy**: Nginx or Traefik
- **Container Orchestration**: Kubernetes or ECS

**Environment:**
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
CORS_ORIGINS=["https://app.yourdomain.com"]
```

## Troubleshooting

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Check connection
redis-cli -u redis://localhost:6379/0 ping
```

### Rate Limit Not Working
```bash
# Check Redis keys
redis-cli KEYS "ratelimit:*"

# Check specific rate limit
redis-cli ZCARD "ratelimit:/api/v1/auth/login:192.168.1.1"
```

### Token Not Revoked
```bash
# Check blacklist
redis-cli KEYS "blacklist:*"

# Check specific token
redis-cli GET "blacklist:eyJ..."
```

### Database Migration Issues
```bash
# Check current version
uv run alembic current

# Show migration history
uv run alembic history

# Rollback one version
uv run alembic downgrade -1
```

### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or use uv run

# Reinstall dependencies
uv sync --reinstall
```

## Contributing

1. Follow the existing code structure (models, schemas, service, routes)
2. Add type hints to all functions
3. Write docstrings for public APIs
4. Add tests for new features
5. Run linting before committing: `uv run ruff check . --fix`
6. Run type checking: `uv run mypy app/`

## API Versioning

Current version: `v1` (prefix: `/api/v1`)

When breaking changes are needed:
1. Create new version (`/api/v2`)
2. Maintain old version for 6 months
3. Add deprecation warnings
4. Document migration path

## Monitoring

**Recommended Metrics:**
- Request rate and latency (p50, p95, p99)
- Error rate by endpoint
- Database query performance
- Redis connection pool usage
- Rate limit violations
- Failed login attempts
- Token revocation rate

**Health Checks:**
- `/health` - Application and database status
- Monitor response time and status

## Support

- **Documentation**: This README
- **API Docs**: http://localhost:8000/api/docs
- **Issues**: GitHub Issues
- **Security**: Report to security@yourdomain.com

## License

See [LICENSE](../LICENSE)