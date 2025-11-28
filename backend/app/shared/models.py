"""Shared base models for all modules."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, event
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base, current_tenant_id


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TenantMixin:
    """Mixin for multi-tenant models with tenant_id."""

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    @declared_attr
    def __table_args__(cls):  # noqa: N805
        """Add tenant_id index."""
        return ({"extend_existing": True},)


class BaseModel(Base, TimestampMixin):
    """Base model with UUID primary key and timestamps."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


class TenantBaseModel(BaseModel, TenantMixin):
    """Base model for tenant-scoped entities."""

    __abstract__ = True


# Event listener to automatically set tenant_id on insert
@event.listens_for(TenantBaseModel, "before_insert", propagate=True)
def set_tenant_id_on_insert(mapper, connection, target):
    """Automatically set tenant_id from context if not set."""
    if not target.tenant_id:
        tenant_id = current_tenant_id.get()
        if tenant_id:
            target.tenant_id = tenant_id
