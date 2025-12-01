"""Platform routes - API endpoints for platform administration.

All endpoints require super_admin role and operate across all tenants.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.core.exceptions import EntityNotFoundError
from app.core.rate_limit import rate_limit
from app.core.security import RequireSuperAdmin
from app.modules.platform.schemas import PlatformStatsResponse, TenantStatsResponse
from app.modules.platform.service import PlatformService
from app.modules.tenants.schemas import TenantCreate, TenantResponse, TenantUpdate
from app.shared.schemas import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/platform", tags=["Platform Admin"])


def get_platform_service(session: DbSession) -> PlatformService:
    """Get platform service dependency."""
    return PlatformService(session)


@router.get(
    "/stats",
    response_model=PlatformStatsResponse,
    summary="Get platform statistics",
)
async def get_platform_stats(
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
) -> PlatformStatsResponse:
    """Get platform-wide statistics including tenant counts, user counts, etc."""
    return await service.get_platform_stats()


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
)
async def create_tenant(
    data: TenantCreate,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
    _rate: Annotated[None, Depends(rate_limit(5, 60))] = None,
) -> TenantResponse:
    """Create a new tenant/organization."""
    tenant = await service.create_tenant(data)
    return TenantResponse.model_validate(tenant)


@router.get(
    "/tenants",
    response_model=PaginatedResponse[TenantStatsResponse],
    summary="List all tenants with stats",
)
async def list_tenants(
    _auth: RequireSuperAdmin,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: PlatformService = Depends(get_platform_service),
) -> PaginatedResponse[TenantStatsResponse]:
    """List all tenants with their statistics."""
    offset = (page - 1) * page_size
    stats, total = await service.get_all_tenant_stats(offset=offset, limit=page_size)
    return PaginatedResponse.create(stats, total, page, page_size)


@router.get(
    "/tenants/search",
    response_model=list[TenantStatsResponse],
    summary="Search tenants",
)
async def search_tenants(
    _auth: RequireSuperAdmin,
    q: str = Query(..., min_length=1, description="Search query"),
    tenant_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    service: PlatformService = Depends(get_platform_service),
) -> list[TenantStatsResponse]:
    """Search tenants by name or domain."""
    return await service.search_tenants(query=q, status=tenant_status, limit=limit)


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
)
async def get_tenant(
    tenant_id: str,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
) -> TenantResponse:
    """Get a specific tenant by ID."""
    tenant = await service.get_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.get(
    "/tenants/{tenant_id}/stats",
    response_model=TenantStatsResponse,
    summary="Get tenant statistics",
)
async def get_tenant_stats(
    tenant_id: str,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
) -> TenantStatsResponse:
    """Get detailed statistics for a specific tenant."""
    stats = await service.get_tenant_stats(tenant_id)
    if not stats:
        raise EntityNotFoundError("Tenant", tenant_id)
    return stats


@router.get(
    "/tenants/domain/{domain:path}",
    response_model=TenantResponse,
    summary="Get tenant by domain",
)
async def get_tenant_by_domain(
    domain: str,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
) -> TenantResponse:
    """Get a tenant by its domain."""
    tenant = await service.get_tenant_by_domain(domain)
    return TenantResponse.model_validate(tenant)


@router.patch(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
    _rate: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> TenantResponse:
    """Update a tenant."""
    tenant = await service.update_tenant(tenant_id, data)
    return TenantResponse.model_validate(tenant)


@router.post(
    "/tenants/{tenant_id}/activate",
    response_model=TenantResponse,
    summary="Activate tenant",
)
async def activate_tenant(
    tenant_id: str,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
    _rate: Annotated[None, Depends(rate_limit(10, 60))] = None,
) -> TenantResponse:
    """Activate a suspended or pending tenant."""
    tenant = await service.activate_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.post(
    "/tenants/{tenant_id}/suspend",
    response_model=TenantResponse,
    summary="Suspend tenant",
)
async def suspend_tenant(
    tenant_id: str,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
    _rate: Annotated[None, Depends(rate_limit(10, 60))] = None,
) -> TenantResponse:
    """Suspend a tenant (disable access)."""
    tenant = await service.suspend_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.delete(
    "/tenants/{tenant_id}",
    response_model=SuccessResponse,
    summary="Delete tenant",
)
async def delete_tenant(
    tenant_id: str,
    _auth: RequireSuperAdmin,
    service: PlatformService = Depends(get_platform_service),
    _rate: Annotated[None, Depends(rate_limit(5, 60))] = None,
) -> SuccessResponse:
    """Delete a tenant permanently."""
    await service.delete_tenant(tenant_id)
    return SuccessResponse(message="Tenant deleted successfully")
