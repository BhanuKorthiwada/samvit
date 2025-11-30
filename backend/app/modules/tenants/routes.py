"""Tenant API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.tenancy import extract_domain_from_host
from app.modules.tenants.schemas import (
    TenantCreate,
    TenantPublicInfo,
    TenantResponse,
    TenantSummary,
    TenantUpdate,
)
from app.modules.tenants.service import TenantService
from app.shared.schemas import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_tenant_service(
    session: DbSession,
) -> TenantService:
    """Get tenant service dependency."""
    return TenantService(session)


@router.get(
    "/info",
    response_model=TenantPublicInfo,
    summary="Get tenant info from current domain",
)
async def get_tenant_info(
    request: Request,
    service: TenantService = Depends(get_tenant_service),
) -> TenantPublicInfo:
    """
    Get public tenant info based on the current domain (from Host header).
    Used by frontend to show tenant branding on login page.
    """
    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    tenant = await service.get_tenant_by_domain(domain)
    return TenantPublicInfo(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        logo_url=tenant.logo_url,
        primary_color=tenant.primary_color,
    )


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
)
async def create_tenant(
    data: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
    _: Annotated[None, Depends(rate_limit(5, 60))] = None,  # 5 per minute - admin only
) -> TenantResponse:
    """Create a new tenant/organization."""
    tenant = await service.create_tenant(data)
    return TenantResponse.model_validate(tenant)


@router.get(
    "",
    response_model=PaginatedResponse[TenantSummary],
    summary="List all tenants",
)
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    service: TenantService = Depends(get_tenant_service),
) -> PaginatedResponse[TenantSummary]:
    """List all tenants with pagination."""
    offset = (page - 1) * page_size
    tenants, total = await service.list_tenants(offset=offset, limit=page_size)
    items = [TenantSummary.model_validate(t) for t in tenants]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
)
async def get_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """Get a specific tenant by ID."""
    tenant = await service.get_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.get(
    "/domain/{domain:path}",
    response_model=TenantResponse,
    summary="Get tenant by domain",
)
async def get_tenant_by_domain(
    domain: str,
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """Get a tenant by its domain."""
    tenant = await service.get_tenant_by_domain(domain)
    return TenantResponse.model_validate(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> TenantResponse:
    """Update a tenant."""
    tenant = await service.update_tenant(tenant_id, data)
    return TenantResponse.model_validate(tenant)


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    summary="Activate tenant",
)
async def activate_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> TenantResponse:
    """Activate a tenant."""
    tenant = await service.activate_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantResponse,
    summary="Suspend tenant",
)
async def suspend_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> TenantResponse:
    """Suspend a tenant."""
    tenant = await service.suspend_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.delete(
    "/{tenant_id}",
    response_model=SuccessResponse,
    summary="Delete tenant",
)
async def delete_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    _: Annotated[
        None, Depends(rate_limit(5, 60))
    ] = None,  # 5 per minute - critical operation
) -> SuccessResponse:
    """Delete a tenant."""
    await service.delete_tenant(tenant_id)
    return SuccessResponse(message="Tenant deleted successfully")
