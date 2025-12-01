"""Tenant public routes - Public tenant info endpoint.

This module only exposes the public tenant info endpoint used by the frontend
for branding on login/signup pages. All admin operations have been moved to
the platform module (/api/v1/platform/tenants/*).
"""

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.core.database import DbSession
from app.core.exceptions import EntityNotFoundError
from app.core.tenancy import extract_domain_from_host
from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas import TenantPublicInfo

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get(
    "/info",
    response_model=TenantPublicInfo,
    summary="Get tenant info from current domain",
)
async def get_tenant_info(
    request: Request,
    session: DbSession,
) -> TenantPublicInfo:
    """
    Get public tenant info based on the current domain (from Host header).
    Used by frontend to show tenant branding on login page.

    This is a PUBLIC endpoint - no authentication required.
    """
    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    result = await session.execute(
        select(Tenant).where(Tenant.domain == domain.lower())
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise EntityNotFoundError("Tenant", domain)

    return TenantPublicInfo(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        logo_url=tenant.logo_url,
        primary_color=tenant.primary_color,
    )
