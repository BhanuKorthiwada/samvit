"""Tenant schemas."""

import re
from enum import Enum

from pydantic import EmailStr, Field, field_validator

from app.shared.schemas import BaseEntitySchema, BaseSchema


class SubscriptionPlan(str, Enum):
    """Subscription plans."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class TenantCreate(BaseSchema):
    """Schema for creating a tenant."""

    name: str = Field(..., min_length=2, max_length=255)
    # Full domain: acme.samvit.bhanu.dev or hr.acme.com
    domain: str = Field(..., min_length=4, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)

    # Address
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str = Field(default="India", max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)

    # Settings
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    currency: str = Field(default="INR", max_length=10)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Validate and normalize domain."""
        v = v.lower().strip()
        # Basic domain validation
        pattern = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid domain format")
        return v


class TenantUpdate(BaseSchema):
    """Schema for updating a tenant."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)

    # Address
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)

    # Settings
    timezone: str | None = Field(default=None, max_length=50)
    currency: str | None = Field(default=None, max_length=10)
    date_format: str | None = Field(default=None, max_length=20)

    # Branding
    logo_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TenantResponse(BaseEntitySchema):
    """Schema for tenant response."""

    name: str
    domain: str
    email: str
    phone: str | None

    # Address
    address: str | None
    city: str | None
    state: str | None
    country: str
    postal_code: str | None

    # Subscription
    plan: SubscriptionPlan
    status: TenantStatus
    max_employees: int
    max_users: int

    # Settings
    timezone: str
    currency: str
    date_format: str
    is_active: bool

    # Branding
    logo_url: str | None
    primary_color: str


class TenantSummary(BaseSchema):
    """Brief tenant info for lists."""

    id: str
    name: str
    domain: str
    plan: SubscriptionPlan
    status: TenantStatus
    is_active: bool


class TenantPublicInfo(BaseSchema):
    """Public tenant info (for login page branding)."""

    id: str
    name: str
    domain: str
    logo_url: str | None
    primary_color: str
