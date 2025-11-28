"""
SAMVIT HRMS - Main Application.

AI-powered multi-tenant Human Resource Management System.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    EntityNotFoundError,
    SamvitException,
    ValidationError,
)
from app.core.tenancy import TenantMiddleware

# Import all routers
from app.ai.agents.router import router as ai_router
from app.modules.attendance.routes import router as attendance_router
from app.modules.auth.routes import router as auth_router
from app.modules.employees.routes import (
    department_router,
    employee_router,
    position_router,
)
from app.modules.leave.routes import router as leave_router
from app.modules.payroll.routes import router as payroll_router
from app.modules.tenants.routes import router as tenants_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting SAMVIT HRMS...")
    yield
    # Shutdown
    print("👋 Shutting down SAMVIT HRMS...")
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered multi-tenant Human Resource Management System",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Tenant Middleware ---
app.add_middleware(TenantMiddleware)


# --- Exception Handlers ---


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(
    request: Request,
    exc: EntityNotFoundError,
) -> JSONResponse:
    """Handle entity not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    request: Request,
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
    request: Request,
    exc: AuthorizationError,
) -> JSONResponse:
    """Handle authorization errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(BusinessRuleViolationError)
async def business_rule_error_handler(
    request: Request,
    exc: BusinessRuleViolationError,
) -> JSONResponse:
    """Handle business rule violations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(SamvitException)
async def samvit_exception_handler(
    request: Request,
    exc: SamvitException,
) -> JSONResponse:
    """Handle general Samvit exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message, "code": exc.code},
    )


# --- API Routers ---
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(tenants_router, prefix=API_V1_PREFIX)
app.include_router(department_router, prefix=API_V1_PREFIX)
app.include_router(position_router, prefix=API_V1_PREFIX)
app.include_router(employee_router, prefix=API_V1_PREFIX)
app.include_router(attendance_router, prefix=API_V1_PREFIX)
app.include_router(leave_router, prefix=API_V1_PREFIX)
app.include_router(payroll_router, prefix=API_V1_PREFIX)
app.include_router(ai_router, prefix=API_V1_PREFIX)


# --- Health Check ---


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to SAMVIT HRMS API",
        "docs": "/api/docs",
        "version": settings.app_version,
    }