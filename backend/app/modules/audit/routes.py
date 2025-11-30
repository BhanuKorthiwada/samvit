"""Audit log API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.tenancy import TenantDep
from app.modules.audit.schemas import (
    AuditAction,
    AuditLogResponse,
    AuditLogSummary,
    AuditStats,
)
from app.modules.audit.service import AuditService
from app.shared.schemas import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


def get_audit_service(
    tenant: TenantDep,
    session: DbSession,
) -> AuditService:
    """Get audit service dependency."""
    return AuditService(session, tenant.tenant_id)


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogSummary],
    summary="List audit logs",
)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    user_id: str | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    _: Annotated[None, Depends(rate_limit(100, 60))] = None,  # 100 per minute
    service: AuditService = Depends(get_audit_service),
) -> PaginatedResponse[AuditLogSummary]:
    """
    List audit logs with optional filters.

    - **user_id**: Filter by user who performed the action
    - **action**: Filter by action type (create, update, delete, login, logout)
    - **entity_type**: Filter by entity type (e.g., Employee, Department)
    - **entity_id**: Filter by specific entity ID
    - **start_date**: Filter logs from this date
    - **end_date**: Filter logs until this date
    """
    offset = (page - 1) * page_size
    audit_logs, total = await service.list_audit_logs(
        offset=offset,
        limit=page_size,
        user_id=user_id,
        action=action.value if action else None,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
    )
    items = [AuditLogSummary.model_validate(log) for log in audit_logs]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/stats",
    response_model=AuditStats,
    summary="Get audit statistics",
)
async def get_audit_stats(
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,  # 30 per minute
    service: AuditService = Depends(get_audit_service),
) -> AuditStats:
    """Get audit log statistics including action breakdown and top users."""
    stats = await service.get_audit_stats()
    return AuditStats(**stats)


@router.get(
    "/user/{user_id}",
    response_model=PaginatedResponse[AuditLogSummary],
    summary="Get user's audit logs",
)
async def get_user_audit_logs(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _: Annotated[None, Depends(rate_limit(100, 60))] = None,  # 100 per minute
    service: AuditService = Depends(get_audit_service),
) -> PaginatedResponse[AuditLogSummary]:
    """Get all audit logs for a specific user."""
    offset = (page - 1) * page_size
    audit_logs, total = await service.get_user_audit_logs(
        user_id=user_id,
        offset=offset,
        limit=page_size,
    )
    items = [AuditLogSummary.model_validate(log) for log in audit_logs]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=PaginatedResponse[AuditLogSummary],
    summary="Get entity's audit logs",
)
async def get_entity_audit_logs(
    entity_type: str,
    entity_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _: Annotated[None, Depends(rate_limit(100, 60))] = None,  # 100 per minute
    service: AuditService = Depends(get_audit_service),
) -> PaginatedResponse[AuditLogSummary]:
    """Get all audit logs for a specific entity."""
    offset = (page - 1) * page_size
    audit_logs, total = await service.get_entity_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        offset=offset,
        limit=page_size,
    )
    items = [AuditLogSummary.model_validate(log) for log in audit_logs]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{audit_id}",
    response_model=AuditLogResponse,
    summary="Get audit log details",
)
async def get_audit_log(
    audit_id: str,
    _: Annotated[None, Depends(rate_limit(100, 60))] = None,  # 100 per minute
    service: AuditService = Depends(get_audit_service),
) -> AuditLogResponse:
    """Get detailed audit log entry."""
    audit_log = await service.get_audit_log(audit_id)
    return AuditLogResponse.model_validate(audit_log)
