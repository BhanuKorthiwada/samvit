"""Schemas for policy management."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.shared.schemas import BaseSchema, TenantEntitySchema


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


class PolicyStatus(str, Enum):
    """Status of a policy document."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class PolicyCreate(BaseSchema):
    """Schema for creating a policy (via file upload)."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category: PolicyCategory = Field(default=PolicyCategory.GENERAL)
    version: str = Field(default="1.0", max_length=50)
    effective_date: datetime | None = None
    expiry_date: datetime | None = None


class PolicyUpdate(BaseSchema):
    """Schema for updating policy metadata."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category: PolicyCategory | None = None
    status: PolicyStatus | None = None
    version: str | None = Field(default=None, max_length=50)
    effective_date: datetime | None = None
    expiry_date: datetime | None = None


class PolicyResponse(TenantEntitySchema):
    """Response schema for a policy."""

    name: str
    description: str | None
    category: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    status: str
    version: str
    is_indexed: bool
    indexed_at: datetime | None
    chunk_count: int
    effective_date: datetime | None
    expiry_date: datetime | None


class PolicySummary(BaseSchema):
    """Summary schema for policy listings."""

    id: str
    name: str
    category: str
    status: str
    version: str
    is_indexed: bool
    file_type: str
    created_at: datetime
    updated_at: datetime


class PolicyIndexRequest(BaseSchema):
    """Request to index/reindex policies."""

    policy_ids: list[str] | None = Field(
        default=None,
        description="Specific policy IDs to index. If empty, indexes all active policies.",
    )
    force: bool = Field(
        default=False,
        description="Force reindex even if already indexed",
    )


class PolicyIndexResponse(BaseSchema):
    """Response from indexing operation."""

    indexed_count: int
    total_chunks: int
    policies: list[str]
    errors: list[str] = []


class PolicyQueryRequest(BaseSchema):
    """Request for querying policies via RAG."""

    question: str = Field(..., min_length=1, max_length=2000)
    policy_ids: list[str] | None = Field(
        default=None,
        description="Optional: limit search to specific policies",
    )
    categories: list[PolicyCategory] | None = Field(
        default=None,
        description="Optional: limit search to specific categories",
    )
    max_chunks: int = Field(default=5, ge=1, le=20)


class PolicyQueryResponse(BaseSchema):
    """Response from policy query."""

    answer: str
    sources: list[dict]
    confidence: str
    follow_up_questions: list[str] = []


class VectorStoreStats(BaseSchema):
    """Vector store statistics."""

    tenant_id: str
    collection_name: str
    total_chunks: int
    policies: dict[str, int]
