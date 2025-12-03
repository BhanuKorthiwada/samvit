"""Policy document models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import TenantBaseModel


class PolicyStatus(str, Enum):
    """Status of a policy document."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class PolicyCategory(str, Enum):
    """Category of policy."""

    GENERAL = "general"
    LEAVE = "leave"
    ATTENDANCE = "attendance"
    CONDUCT = "conduct"
    BENEFITS = "benefits"
    COMPENSATION = "compensation"
    SAFETY = "safety"
    IT = "it"
    TRAVEL = "travel"
    EXPENSE = "expense"
    OTHER = "other"


class Policy(TenantBaseModel):
    """Policy document metadata model.

    The actual document content is stored in the file system,
    and embeddings are stored in the vector store.
    """

    __tablename__ = "policies"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable policy name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Brief description of the policy",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PolicyCategory.GENERAL.value,
        index=True,
        doc="Policy category for filtering",
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Relative path to the policy file",
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Original filename",
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="File extension/type (pdf, md, txt)",
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="File size in bytes",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PolicyStatus.ACTIVE.value,
        index=True,
        doc="Policy status",
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
        doc="Policy version",
    )

    is_indexed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether the policy has been indexed in vector store",
    )

    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the policy was last indexed",
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of chunks in vector store",
    )

    effective_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the policy becomes effective",
    )

    expiry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the policy expires (if applicable)",
    )

    def __repr__(self) -> str:
        return f"<Policy {self.name} ({self.id})>"
