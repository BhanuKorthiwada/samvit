"""Multi-tenancy middleware and utilities."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.database import current_tenant_id


class TenantContext:
    """Context for the current tenant."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def __repr__(self) -> str:
        return f"TenantContext(tenant_id={self.tenant_id})"


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context from request."""

    # Paths that don't require tenant context
    EXEMPT_PATHS = {
        "/health",
        "/",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request and set tenant context."""
        path = request.url.path

        # Skip tenant check for exempt paths
        if path in self.EXEMPT_PATHS or path.startswith("/api/docs"):
            return await call_next(request)

        # Extract tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID")

        # Try subdomain if no header
        if not tenant_id:
            host = request.headers.get("host", "")
            parts = host.split(".")
            if len(parts) > 2:
                tenant_id = parts[0]

        # Use default for development
        if not tenant_id and settings.default_tenant_id:
            tenant_id = settings.default_tenant_id

        # Set in context variable
        if tenant_id:
            current_tenant_id.set(tenant_id)

        return await call_next(request)


async def get_tenant_from_header(
    request: Request,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> TenantContext:
    """
    Extract tenant ID from request header.
    
    In production, this would also validate the tenant exists
    and the user has access to it.
    """
    tenant_id = x_tenant_id

    # Try to get from subdomain if not in header
    if not tenant_id:
        host = request.headers.get("host", "")
        parts = host.split(".")
        if len(parts) > 2:  # e.g., tenant1.samvit.com
            tenant_id = parts[0]

    # Fallback to default tenant for development
    if not tenant_id:
        tenant_id = settings.default_tenant_id

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required. Provide X-Tenant-ID header.",
        )

    # Set tenant in context variable for use in repositories
    current_tenant_id.set(tenant_id)

    return TenantContext(tenant_id=tenant_id)


async def get_optional_tenant(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> TenantContext | None:
    """Get tenant context if provided, otherwise None."""
    if x_tenant_id:
        current_tenant_id.set(x_tenant_id)
        return TenantContext(tenant_id=x_tenant_id)
    return None


# Type alias for dependency injection
TenantDep = Annotated[TenantContext, Depends(get_tenant_from_header)]
OptionalTenantDep = Annotated[TenantContext | None, Depends(get_optional_tenant)]
