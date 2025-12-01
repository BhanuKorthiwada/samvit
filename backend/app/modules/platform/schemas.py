"""Platform schemas - Request/response models for platform administration."""

from datetime import datetime
from enum import Enum

from pydantic import EmailStr, Field

from app.shared.schemas import BaseSchema


class PlatformUserRole(str, Enum):
    """Platform-level user roles."""

    SUPER_ADMIN = "super_admin"
    SUPPORT = "support"
    BILLING = "billing"
    READONLY = "readonly"


class PlatformUserCreate(BaseSchema):
    """Schema for creating a platform admin user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: PlatformUserRole = PlatformUserRole.READONLY


class PlatformUserResponse(BaseSchema):
    """Response schema for platform admin user."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: PlatformUserRole
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None


class TenantStatsResponse(BaseSchema):
    """Statistics for a single tenant."""

    tenant_id: str
    tenant_name: str
    domain: str
    status: str
    user_count: int
    employee_count: int
    created_at: datetime
    last_activity: datetime | None = None


class PlatformStatsResponse(BaseSchema):
    """Platform-wide statistics."""

    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    pending_tenants: int
    total_users: int
    total_employees: int
    tenants_created_last_30_days: int
    tenants_created_last_7_days: int


class TenantActivityLog(BaseSchema):
    """Activity log entry for a tenant."""

    tenant_id: str
    tenant_name: str
    action: str
    actor_email: str | None = None
    details: dict | None = None
    timestamp: datetime


class SystemHealthResponse(BaseSchema):
    """System health status."""

    status: str
    database: dict
    redis: dict
    storage: dict | None = None
    version: str
    uptime_seconds: float


class BillingPlan(str, Enum):
    """Available billing plans."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantBillingInfo(BaseSchema):
    """Billing information for a tenant."""

    tenant_id: str
    plan: BillingPlan
    billing_email: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    user_limit: int
    employee_limit: int
    storage_limit_mb: int
    features: list[str] = Field(default_factory=list)


class TenantBillingUpdate(BaseSchema):
    """Update billing info for a tenant."""

    plan: BillingPlan | None = None
    billing_email: EmailStr | None = None
    user_limit: int | None = Field(default=None, ge=1)
    employee_limit: int | None = Field(default=None, ge=1)
    storage_limit_mb: int | None = Field(default=None, ge=100)
    features: list[str] | None = None


class ImpersonationRequest(BaseSchema):
    """Request to impersonate a user (support tool)."""

    tenant_id: str
    user_id: str
    reason: str = Field(..., min_length=10, max_length=500)


class ImpersonationResponse(BaseSchema):
    """Response with impersonation token."""

    access_token: str
    expires_in: int
    target_user_email: str
    target_tenant_domain: str


class FeatureFlagCreate(BaseSchema):
    """Create a feature flag."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    enabled_globally: bool = False
    enabled_for_tenants: list[str] = Field(default_factory=list)


class FeatureFlagResponse(BaseSchema):
    """Feature flag response."""

    id: str
    name: str
    description: str | None
    enabled_globally: bool
    enabled_for_tenants: list[str]
    created_at: datetime
    updated_at: datetime


class AnnouncementCreate(BaseSchema):
    """Create a platform-wide announcement."""

    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    level: str = Field(default="info")  # info, warning, critical
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    target_tenants: list[str] | None = None  # None = all tenants


class AnnouncementResponse(BaseSchema):
    """Announcement response."""

    id: str
    title: str
    message: str
    level: str
    starts_at: datetime | None
    ends_at: datetime | None
    target_tenants: list[str] | None
    created_by: str
    created_at: datetime
    is_active: bool
