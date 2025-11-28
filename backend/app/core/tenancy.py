"""Multi-tenancy middleware and utilities."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.database import async_session_maker, current_tenant_id, get_async_session


class TenantContext:
    """Context for the current tenant."""

    def __init__(self, tenant_id: str, domain: str | None = None):
        self.tenant_id = tenant_id
        self.domain = domain

    def __repr__(self) -> str:
        return f"TenantContext(tenant_id={self.tenant_id}, domain={self.domain})"


def extract_domain_from_host(host: str) -> str:
    """Extract clean domain from Host header.

    Examples:
        - "acme.samvit.bhanu.dev:8000" -> "acme.samvit.bhanu.dev"
        - "hr.acme.com" -> "hr.acme.com"
        - "localhost:8000" -> "localhost"
    """
    # Remove port if present
    return host.split(":")[0].lower()


def is_reserved_domain(domain: str) -> bool:
    """Check if domain is reserved (main app, not tenant)."""
    return domain in settings.reserved_domains or domain in ["localhost", "127.0.0.1"]


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant from Host header and set in request context.

    This middleware:
    1. Extracts domain from Host header
    2. Looks up tenant in database by domain
    3. Sets tenant_id in request.state and context variable
    4. Makes tenant info available for logging and downstream handlers
    """

    # Paths that don't require tenant context
    EXEMPT_PATHS = {
        "/health",
        "/",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        # Platform-level admin endpoints (manage all tenants)
        "/api/v1/tenants",
    }

    # Paths where tenant is optional (resolved if present, but not required)
    OPTIONAL_TENANT_PATHS = {
        "/api/v1/auth/register/company",  # Creates a new tenant
    }

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from tenant requirement."""
        if path in self.EXEMPT_PATHS:
            return True
        # Check path prefixes
        if path.startswith("/api/docs"):
            return True
        # Platform admin tenant management
        if path.startswith("/api/v1/tenants"):
            return True
        return False

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request and set tenant context from Host header."""
        # Import here to avoid circular imports
        from app.modules.tenants.models import Tenant

        path = request.url.path

        # Initialize request state
        request.state.tenant_id = None
        request.state.domain = None

        # Skip tenant lookup for exempt paths
        if self._is_exempt_path(path):
            return await call_next(request)

        # Extract domain from Host header
        host = request.headers.get("host", "")
        domain = extract_domain_from_host(host)
        request.state.domain = domain

        # Skip lookup for reserved domains (localhost, etc.)
        if is_reserved_domain(domain):
            # For optional tenant paths, continue without tenant
            if path in self.OPTIONAL_TENANT_PATHS:
                return await call_next(request)
            # Otherwise, this is an error - need proper tenant domain
            return Response(
                content='{"detail": "Please access via your tenant domain (e.g., acme.samvit.bhanu.dev)"}',
                status_code=400,
                media_type="application/json",
            )

        # Look up tenant by domain in database
        async with async_session_maker() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.domain == domain, Tenant.is_active.is_(True)
                )
            )
            tenant = result.scalar_one_or_none()

        if tenant:
            # Set tenant context for the request
            request.state.tenant_id = tenant.id
            current_tenant_id.set(tenant.id)
        elif path not in self.OPTIONAL_TENANT_PATHS:
            # Tenant not found and path requires tenant
            return Response(
                content=f'{{"detail": "Tenant not found for domain: {domain}"}}',
                status_code=404,
                media_type="application/json",
            )

        return await call_next(request)


async def get_current_tenant(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> TenantContext:
    """
    Get tenant context for the current request.

    Uses middleware-set value if available (avoids duplicate DB query).
    Otherwise, looks up tenant from Host header domain.
    """
    # Check if middleware already resolved tenant
    tenant_id = getattr(request.state, "tenant_id", None)
    domain = getattr(request.state, "domain", None)

    if tenant_id:
        # Already resolved by middleware, ensure context var is set
        current_tenant_id.set(tenant_id)
        return TenantContext(tenant_id=tenant_id, domain=domain)

    # Need to resolve tenant (middleware might have skipped this path)
    from app.modules.tenants.models import Tenant

    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    # Check if reserved domain
    if is_reserved_domain(domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This domain is reserved. Please access via your tenant domain.",
        )

    # Look up tenant by domain
    result = await session.execute(
        select(Tenant).where(Tenant.domain == domain, Tenant.is_active.is_(True))
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found for domain: {domain}",
        )

    # Set tenant in context variable and request state
    current_tenant_id.set(tenant.id)
    request.state.tenant_id = tenant.id
    request.state.domain = domain

    return TenantContext(tenant_id=tenant.id, domain=domain)


# Type alias for dependency injection
TenantDep = Annotated[TenantContext, Depends(get_current_tenant)]
