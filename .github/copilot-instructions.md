# SAMVIT HRMS - GitHub Copilot Instructions

This document provides comprehensive instructions for AI assistants (GitHub Copilot, Claude, etc.) working on the SAMVIT HRMS codebase.

## Core Principles

### KISS (Keep It Simple, Stupid)
- Prefer clear, maintainable solutions over unnecessarily complex ones
- Smart is good, convoluted is not
- If a solution requires extensive explanation, consider simplifying

### YAGNI (You Aren't Gonna Need It)
- Don't build features until they're actually needed
- Avoid speculative generalization
- Delete code that's not being used

### Self-Documenting Code
- Write code that explains itself through clear naming and structure
- **Avoid comments** unless absolutely necessary (e.g., explaining *why*, not *what*)
- Good variable/function names > comments
- If you need a comment to explain code, refactor the code instead

```python
# ❌ BAD - Comment explains what code does
# Check if employee is active and not on leave
if emp.status == "active" and emp.leave_status != "on_leave":
    ...

# ✅ GOOD - Self-explanatory
if employee.is_available_for_assignment():
    ...
```

---

## Project Overview

**SAMVIT** is an AI-powered multi-tenant Human Resource Management System built with:
- **Backend**: Python 3.13+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend**: React, TypeScript, Vite, TanStack Router
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache/Queue**: Redis (DragonflyDB compatible)
- **AI Agents**: Pydantic AI, LangGraph (optional)

---

## Architectural Decisions

### 1. Modular Monolith Architecture

The backend follows a **modular monolith** pattern with clean architecture principles:

```
backend/
├── app/
│   ├── core/           # Infrastructure layer (shared by all modules)
│   │   ├── config.py       # Settings via pydantic-settings
│   │   ├── database.py     # SQLAlchemy async engine, session factory
│   │   ├── security.py     # Password hashing, JWT tokens
│   │   ├── tenancy.py      # Multi-tenant middleware and context
│   │   ├── exceptions.py   # Custom exception hierarchy
│   │   ├── rate_limit.py   # Redis-based rate limiting
│   │   ├── token_blacklist.py  # JWT revocation
│   │   ├── cache.py        # Redis caching layer
│   │   ├── audit.py        # Audit logging
│   │   └── middleware.py   # Request ID, logging middleware
│   │
│   ├── shared/         # Reusable base classes (no business logic)
│   │   ├── models.py       # BaseModel, TenantBaseModel, mixins
│   │   ├── schemas.py      # BaseSchema, PaginatedResponse, etc.
│   │   └── repository.py   # BaseRepository, TenantRepository
│   │
│   ├── modules/        # Business domain modules
│   │   ├── tenants/        # Tenant/organization management
│   │   ├── auth/           # Authentication & RBAC
│   │   ├── employees/      # Employee, Department, Position
│   │   ├── attendance/     # Time tracking, shifts
│   │   ├── leave/          # Leave policies, requests, balances
│   │   ├── payroll/        # Salary structures, payslips
│   │   └── audit/          # Audit log queries
│   │
│   └── ai/
│       └── agents/         # AI-powered assistants
│           ├── base.py         # Agent interface
│           ├── router.py       # AI API routes
│           └── pydantic_ai/    # Pydantic AI implementation
│
└── tests/              # Integration and unit tests
```

### 2. Module Structure Convention

Each module follows this **consistent structure**:

```
modules/{module_name}/
├── __init__.py         # Keep minimal - just docstring
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas (Create, Update, Response)
├── service.py          # Business logic layer
├── repository.py       # Data access layer (optional, for complex queries)
└── routes.py           # FastAPI router endpoints
```

**Key Principle**: Prefer explicit imports over convenience exports in `__init__.py`.

```python
# ✅ CORRECT - Explicit import from specific module
from app.modules.employees.models import Employee
from app.modules.employees.service import EmployeeService

# ❌ AVOID - Convenience re-exports in __init__.py
from app.modules.employees import Employee  # Don't do this
```

---

## Multi-Tenancy Design

### Domain-Based Tenant Identification

Tenants are identified by **domain** (from `Host` header):
- Subdomain: `acme.samvit.bhanu.dev`
- Custom domain: `hr.acme.com`

### Tenant-Scoped Models

All tenant-specific data inherits from `TenantBaseModel`:

```python
from app.shared.models import TenantBaseModel

class Employee(TenantBaseModel):
    """Employee model - automatically scoped to tenant."""

    __tablename__ = "employees"

    # tenant_id is inherited and auto-set
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # ... other fields
```

### Tenant Context

The tenant context is available via:

```python
from app.core.tenancy import TenantDep  # In routes
from app.core.database import current_tenant_id  # Context variable

# In route handler
async def create_employee(
    tenant: TenantDep,  # Automatically resolved from Host header
    session: DbSession,
):
    service = EmployeeService(session, tenant.tenant_id)
```

### Repository Pattern for Tenant Isolation

Use `TenantRepository` for automatic tenant filtering:

```python
from app.shared.repository import TenantRepository
from app.modules.employees.models import Employee

class EmployeeRepository(TenantRepository[Employee]):
    model = Employee

    async def get_by_email(self, email: str) -> Employee | None:
        result = await self.session.execute(
            self._apply_tenant_filter(  # ← Automatically filters by tenant_id
                select(Employee).where(Employee.email == email)
            )
        )
        return result.scalar_one_or_none()
```

---

## Code Conventions

### 1. Type Hints (Required Everywhere)

```python
# ✅ CORRECT - Full type hints
async def get_employee(
    self,
    employee_id: str,
) -> Employee:
    """Get employee by ID."""
    ...

# ✅ CORRECT - Use modern Python 3.10+ syntax
def process(items: list[str] | None = None) -> dict[str, Any]:
    ...
```

### 2. SQLAlchemy Models

```python
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.models import TenantBaseModel

class Department(TenantBaseModel):
    """Department model."""

    __tablename__ = "departments"

    # Use Mapped[] for all columns
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Optional fields use Mapped[X | None]
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign keys
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id"),
        nullable=True,
    )

    # Relationships
    parent: Mapped["Department | None"] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children",
    )
```

### 3. Pydantic Schemas

```python
from pydantic import Field, EmailStr
from app.shared.schemas import BaseSchema, TenantEntitySchema

class EmployeeCreate(BaseSchema):
    """Schema for creating an employee."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)


class EmployeeUpdate(BaseSchema):
    """Schema for updating - all fields optional."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    # ... other optional fields


class EmployeeResponse(TenantEntitySchema):
    """Response schema - includes id, tenant_id, timestamps."""

    first_name: str
    last_name: str
    email: str
    # ... other fields
```

### 4. Service Layer Pattern

Services contain business logic and use repositories for data access:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EntityNotFoundError, EntityAlreadyExistsError

class EmployeeService:
    """Service for employee operations."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = EmployeeRepository(session, tenant_id)

    async def create_employee(self, data: EmployeeCreate) -> Employee:
        """Create a new employee."""
        # Business rule: Check for duplicate email
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise EntityAlreadyExistsError("Employee", data.email)

        employee = Employee(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        return await self.repo.create(employee)

    async def get_employee(self, employee_id: str) -> Employee:
        """Get employee by ID or raise."""
        return await self.repo.get_by_id_or_raise(employee_id)
```

### 5. Route Handlers

```python
from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.core.database import DbSession
from app.core.tenancy import TenantDep
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/employees", tags=["Employees"])


def get_service(tenant: TenantDep, session: DbSession) -> EmployeeService:
    """Dependency to create service with tenant context."""
    return EmployeeService(session, tenant.tenant_id)


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
)
async def create_employee(
    data: EmployeeCreate,
    service: EmployeeService = Depends(get_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20/minute
) -> EmployeeResponse:
    """Create a new employee."""
    employee = await service.create_employee(data)
    return EmployeeResponse.model_validate(employee)


@router.get(
    "",
    response_model=PaginatedResponse[EmployeeSummary],
    summary="List employees",
)
async def list_employees(
    page: int = 1,
    page_size: int = 20,
    service: EmployeeService = Depends(get_service),
) -> PaginatedResponse[EmployeeSummary]:
    """List employees with pagination."""
    offset = (page - 1) * page_size
    employees, total = await service.list_employees(offset=offset, limit=page_size)
    items = [EmployeeSummary.model_validate(e) for e in employees]
    return PaginatedResponse.create(items, total, page, page_size)
```

---

## Exception Handling

Use the custom exception hierarchy in `app/core/exceptions.py`:

```python
from app.core.exceptions import (
    EntityNotFoundError,      # 404 - Resource not found
    EntityAlreadyExistsError, # 409 - Conflict/duplicate
    ValidationError,          # 422 - Validation failed
    AuthenticationError,      # 401 - Auth failed
    AuthorizationError,       # 403 - Not authorized
    BusinessRuleViolationError,  # 400 - Business rule violated
    TenantMismatchError,      # 403 - Cross-tenant access attempt
)

# Usage in service
async def create_employee(self, data: EmployeeCreate) -> Employee:
    existing = await self.repo.get_by_email(data.email)
    if existing:
        raise EntityAlreadyExistsError("Employee", data.email)
    # ...
```

Exception handlers in `main.py` automatically convert these to appropriate HTTP responses.

---

## Database & Migrations

### Alembic Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "add_employee_skills"

# Apply migrations
uv run alembic upgrade head

# Rollback one step
uv run alembic downgrade -1
```

### Migration File Pattern

```python
"""Add employee skills table.

Revision ID: 003_employee_skills
Revises: 002_tenant_settings
Create Date: 2025-11-29
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "003_employee_skills"
down_revision: Union[str, None] = "002_tenant_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("proficiency", sa.Integer(), default=1),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("employee_skills")
```

---

## Security Features

### Rate Limiting

```python
from app.core.rate_limit import rate_limit

# Apply to routes - (requests, window_seconds)
@router.post("/login")
async def login(
    _: Annotated[None, Depends(rate_limit(5, 60))],  # 5 per minute
):
    pass
```

### Token Blacklist (Logout)

Tokens are blacklisted on logout and checked on every authenticated request.

### Audit Logging

```python
from app.core.audit import log_audit, AuditAction

await log_audit(
    session,
    tenant_id=tenant.tenant_id,
    user_id=current_user.id,
    action=AuditAction.CREATE,
    entity_type="Employee",
    entity_id=employee.id,
    changes={"created": data.model_dump()},
    ip_address=request.client.host,
)
```

---

## Testing Patterns

### Test File Location

```
tests/
├── conftest.py              # Shared fixtures
├── test_api_functional.py   # API functional tests
├── test_auth_integration.py # Auth module tests
├── test_employees_integration.py
├── test_rate_limit.py
├── test_cache.py
└── test_token_blacklist.py
```

### Key Fixtures (from conftest.py)

```python
@pytest_asyncio.fixture
async def client(test_engine, session_maker, monkeypatch):
    """Test client with database override."""
    # Patches both FastAPI dependency and TenantMiddleware session maker
    ...

@pytest_asyncio.fixture
async def test_tenant(test_session) -> Tenant:
    """Create test tenant."""
    ...

@pytest_asyncio.fixture
async def test_user(test_session, test_tenant) -> User:
    """Create test user."""
    ...

def get_auth_headers(user: User, tenant: Tenant) -> dict[str, str]:
    """Generate auth headers for requests."""
    token = create_access_token(data={"sub": user.id, "tenant_id": tenant.id})
    return {"Authorization": f"Bearer {token}", "Host": tenant.domain}
```

### Test Pattern

```python
import pytest
from httpx import AsyncClient

class TestEmployees:
    async def test_create_employee_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test creating an employee."""
        response = await client.post(
            "/api/v1/employees",
            json={"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["tenant_id"] == test_tenant.id
```

---

## AI Agent Development

### Pydantic AI Agent Pattern

```python
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from functools import cache

@dataclass
class AgentDeps:
    """Dependencies injected into agent."""
    session: AsyncSession
    tenant_id: str
    employee_id: str

class AgentResponse(BaseModel):
    """Structured response."""
    message: str
    data: dict | None = None

@cache
def get_agent() -> Agent[AgentDeps, AgentResponse]:
    """Lazy singleton agent initialization."""
    agent = Agent(
        model=settings.ai_model,
        system_prompt="...",
        deps_type=AgentDeps,
        result_type=AgentResponse,
    )
    _register_tools(agent)
    return agent

def _register_tools(agent: Agent) -> None:
    @agent.tool
    async def get_leave_balance(ctx: RunContext[AgentDeps]) -> LeaveBalanceResponse:
        """Tool implementation with database access."""
        # Use ctx.deps.session for database queries
        ...
```

---

## Do's and Don'ts

### ✅ DO

1. **Keep it clean (KISS)** - Smart solutions, not convoluted ones
2. **Use type hints everywhere** - Functions, parameters, return types
3. **Use `Mapped[]` for SQLAlchemy columns** - Required in SQLAlchemy 2.0
4. **Use explicit imports** - `from app.modules.x.y import Z`
5. **Use TenantRepository for tenant-scoped queries** - Automatic isolation
6. **Use custom exceptions** - `EntityNotFoundError`, `EntityAlreadyExistsError`
7. **Add rate limiting to write operations** - Protect against abuse
8. **Write docstrings for public functions** - Clear API documentation
9. **Use `model_dump(exclude_unset=True)` for updates** - Partial updates
10. **Use `model_validate()` for responses** - Proper serialization
11. **Use descriptive names** - Code should be self-explanatory

### ❌ DON'T

1. **Don't over-engineer (YAGNI)** - Build only what's needed now
2. **Don't add comments for obvious code** - Refactor to be self-explanatory instead
3. **Don't add convenience exports to `__init__.py`** - Keep them minimal
4. **Don't use `Base` from SQLAlchemy directly** - Use `TenantBaseModel` or `BaseModel`
5. **Don't access `tenant_id` from request directly** - Use `TenantDep`
6. **Don't write raw SQL without tenant filter** - Use repository pattern
7. **Don't catch exceptions silently** - Let them propagate to handlers
8. **Don't hardcode configuration** - Use `settings` from config
9. **Don't use blocking I/O** - Use async/await throughout
10. **Don't skip validation** - Use Pydantic schemas for all input

---

## Common Patterns Reference

### Pagination

```python
from app.shared.schemas import PaginatedResponse

@router.get("", response_model=PaginatedResponse[ItemSummary])
async def list_items(page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    items, total = await service.list_items(offset, page_size)
    return PaginatedResponse.create(items, total, page, page_size)
```

### Partial Updates

```python
async def update_employee(self, id: str, data: EmployeeUpdate) -> Employee:
    employee = await self.repo.get_by_id_or_raise(id)
    update_data = data.model_dump(exclude_unset=True)  # Only changed fields
    for field, value in update_data.items():
        setattr(employee, field, value)
    return await self.repo.update(employee)
```

### Flexible Settings (JSON column)

```python
class TenantSettings(TenantBaseModel):
    __tablename__ = "tenant_settings"

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
```

---

## Quick Reference Commands

```bash
# Start development server
uv run fastapi dev app/main.py

# Run tests
uv run pytest
uv run pytest tests/test_auth_integration.py -v

# Linting & formatting
uv run ruff check . --fix
uv run ruff format .

# Type checking
uv run mypy app/

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | `sqlite+aiosqlite:///./samvit_test.db` |
| `SECRET_KEY` | JWT signing key (32+ chars) | Required in production |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `ENVIRONMENT` | `development`/`staging`/`production` | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `AI_MODEL` | Default AI model | `openai:gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key | - |

---

*Last updated: November 2025*
