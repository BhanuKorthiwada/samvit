"""
SAMVIT HRMS - Main Application.

AI-powered multi-tenant Human Resource Management System.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

# Import all routers
from app.ai.agents.router import router as ai_router
from app.core.config import settings
from app.core.database import async_session_maker, engine, init_db
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    SamvitException,
    ValidationError,
)
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.rate_limit import RateLimitHeaderMiddleware, rate_limiter
from app.core.redis import redis_pool
from app.core.tenancy import TenantMiddleware
from app.core.token_blacklist import token_blacklist
from app.modules.attendance.routes import router as attendance_router
from app.modules.audit.routes import router as audit_router
from app.modules.auth.routes import admin_router as users_router
from app.modules.auth.routes import router as auth_router
from app.modules.employees.routes import (
    department_router,
    employee_router,
    position_router,
)
from app.modules.leave.routes import router as leave_router
from app.modules.payroll.routes import router as payroll_router
from app.modules.platform.routes import router as platform_router
from app.modules.tenants.routes import router as tenants_router
from app.modules.tenants.settings_routes import router as tenant_settings_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Environment: %s, Debug: %s", settings.environment, settings.debug)
    await init_db()
    logger.info("Database initialized")

    # Initialize shared Redis pool first (used by rate_limiter and token_blacklist)
    await redis_pool.connect()
    logger.info("Redis connection pool initialized")

    # Initialize services that use Redis
    await token_blacklist.connect()
    await rate_limiter.connect()
    logger.info(
        "Redis-based services initialized (token blacklist, rate limiter, cache)"
    )

    yield

    # Shutdown
    logger.info("Shutting down application")
    await rate_limiter.close()
    await token_blacklist.close()
    await redis_pool.close()
    await engine.dispose()


# OpenAPI tags for better organization
OPENAPI_TAGS = [
    {"name": "Health", "description": "Health check endpoints"},
    {
        "name": "Platform Admin",
        "description": "Platform-level administration (super_admin only)",
    },
    {"name": "Auth", "description": "Authentication and authorization"},
    {"name": "Tenants", "description": "Public tenant information"},
    {
        "name": "Tenant Settings",
        "description": "Tenant-level customizations and preferences",
    },
    {"name": "Departments", "description": "Department management"},
    {"name": "Positions", "description": "Position/role management"},
    {"name": "Employees", "description": "Employee management"},
    {"name": "Attendance", "description": "Time tracking and attendance"},
    {"name": "Leave", "description": "Leave policies, requests, and balances"},
    {"name": "Payroll", "description": "Salary structures and payslips"},
    {"name": "Audit Logs", "description": "Audit trail and activity logging"},
    {"name": "AI Agents", "description": "AI-powered conversational HR assistant"},
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered multi-tenant Human Resource Management System",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=OPENAPI_TAGS,
    swagger_ui_parameters={
        "docExpansion": "list",
        "filter": True,
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": 3,
        "defaultModelExpandDepth": 3,
        "syntaxHighlight.theme": "monokai",
    },
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
        "X-Response-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    ],
)

# --- Rate Limit Header Middleware ---
app.add_middleware(RateLimitHeaderMiddleware)

# --- Request ID Middleware (for tracing) ---
app.add_middleware(RequestIDMiddleware)

# --- Tenant Middleware ---
app.add_middleware(TenantMiddleware)


# --- Exception Handlers ---


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(
    _request: Request,
    exc: EntityNotFoundError,
) -> JSONResponse:
    """Handle entity not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(EntityAlreadyExistsError)
async def entity_already_exists_handler(
    _request: Request,
    exc: EntityAlreadyExistsError,
) -> JSONResponse:
    """Handle entity already exists errors (conflicts)."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(
    _request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    _request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    """Handle authentication errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message, "code": exc.code},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(
    _request: Request,
    exc: AuthorizationError,
) -> JSONResponse:
    """Handle authorization errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(BusinessRuleViolationError)
async def business_rule_error_handler(
    _request: Request,
    exc: BusinessRuleViolationError,
) -> JSONResponse:
    """Handle business rule violations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(SamvitException)
async def samvit_exception_handler(
    _request: Request,
    exc: SamvitException,
) -> JSONResponse:
    """Handle general Samvit exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unhandled exceptions with proper logging."""
    request_id = getattr(request.state, "request_id", "N/A")
    logger.exception(
        "Unhandled exception: %s",
        exc,
        extra={"request_id": request_id},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
            "request_id": request_id,
        },
    )


# --- API Routers ---
API_V1_PREFIX = "/api/v1"

app.include_router(platform_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(tenants_router, prefix=API_V1_PREFIX)
app.include_router(tenant_settings_router, prefix=API_V1_PREFIX)
app.include_router(department_router, prefix=API_V1_PREFIX)
app.include_router(position_router, prefix=API_V1_PREFIX)
app.include_router(employee_router, prefix=API_V1_PREFIX)
app.include_router(attendance_router, prefix=API_V1_PREFIX)
app.include_router(leave_router, prefix=API_V1_PREFIX)
app.include_router(payroll_router, prefix=API_V1_PREFIX)
app.include_router(audit_router, prefix=API_V1_PREFIX)
app.include_router(ai_router, prefix=API_V1_PREFIX)


# --- Health Check ---


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint with database and Redis connectivity verification."""
    import time

    # Database health check
    db_status = "healthy"
    db_latency_ms: float | None = None

    try:
        start = time.perf_counter()
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_latency_ms = (time.perf_counter() - start) * 1000
    except Exception as e:
        db_status = "unhealthy"
        logger.error("Database health check failed: %s", e)

    # Redis health check
    redis_status = "healthy"
    redis_latency_ms: float | None = None

    try:
        start = time.perf_counter()
        is_reachable = await redis_pool.ping()
        redis_latency_ms = (time.perf_counter() - start) * 1000
        if not is_reachable:
            redis_status = "unhealthy"
    except Exception as e:
        redis_status = "unhealthy"
        logger.error("Redis health check failed: %s", e)

    # Overall status
    if db_status == "healthy" and redis_status == "healthy":
        overall_status = "healthy"
    elif db_status == "unhealthy":
        overall_status = "unhealthy"  # DB is critical
    else:
        overall_status = "degraded"  # Redis down = degraded (fail-open)

    return {
        "status": overall_status,
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {
            "database": {
                "status": db_status,
                "latency_ms": round(db_latency_ms, 2) if db_latency_ms else None,
            },
            "redis": {
                "status": redis_status,
                "latency_ms": round(redis_latency_ms, 2) if redis_latency_ms else None,
            },
        },
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to SAMVIT HRMS API",
        "docs": "/api/docs",
        "version": settings.app_version,
    }
