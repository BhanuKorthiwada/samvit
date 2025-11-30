"""Audit log schemas."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.shared.schemas import BaseSchema, TenantEntitySchema


class AuditAction(str, Enum):
    """Audit action types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"


class AuditLogResponse(TenantEntitySchema):
    """Audit log response schema."""

    user_id: str
    action: AuditAction
    entity_type: str | None
    entity_id: str | None
    changes: dict | None
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime


class AuditLogSummary(BaseSchema):
    """Brief audit log info for lists."""

    id: str
    user_id: str
    action: AuditAction
    entity_type: str | None
    entity_id: str | None
    timestamp: datetime
    ip_address: str | None


class AuditLogFilter(BaseSchema):
    """Filter options for audit logs."""

    user_id: str | None = None
    action: AuditAction | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class AuditStats(BaseSchema):
    """Audit statistics."""

    total_logs: int
    actions_breakdown: dict[str, int] = Field(default_factory=dict)
    entity_types_breakdown: dict[str, int] = Field(default_factory=dict)
    top_users: list[dict[str, str | int]] = Field(default_factory=list)
