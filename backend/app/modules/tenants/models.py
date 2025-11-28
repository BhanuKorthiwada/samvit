"""Tenant models."""

from enum import Enum

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import BaseModel, TimestampMixin


class SubscriptionPlan(str, Enum):
    """Subscription plans for tenants."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class Tenant(BaseModel, TimestampMixin):
    """Tenant/Organization model - the root of multi-tenancy."""

    __tablename__ = "tenants"

    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Full domain: acme.samvit.bhanu.dev OR hr.acme.com (custom domain)
    domain: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Contact
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Address
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Subscription
    plan: Mapped[str] = mapped_column(
        String(50),
        default=SubscriptionPlan.FREE.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=TenantStatus.PENDING.value,
        nullable=False,
    )

    # Limits based on plan
    max_employees: Mapped[int] = mapped_column(default=10)
    max_users: Mapped[int] = mapped_column(default=5)

    # Settings
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    date_format: Mapped[str] = mapped_column(String(20), default="DD/MM/YYYY")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")

    # Relationships (defined in other modules)
    # users = relationship("User", back_populates="tenant")
    # employees = relationship("Employee", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.domain})>"
