"""API routes for policy management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.security import CurrentUser
from app.core.tenancy import TenantDep
from app.modules.policies.schemas import (
    PolicyCategory,
    PolicyCreate,
    PolicyIndexRequest,
    PolicyIndexResponse,
    PolicyResponse,
    PolicySummary,
    PolicyUpdate,
    VectorStoreStats,
)
from app.modules.policies.service import PolicyService
from app.shared.schemas import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["Policies"])


def get_service(tenant: TenantDep, session: DbSession) -> PolicyService:
    """Dependency to create policy service."""
    return PolicyService(session, tenant.tenant_id)


@router.post(
    "/upload",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a policy document",
)
async def upload_policy(
    file: Annotated[UploadFile, File(description="Policy document file")],
    name: Annotated[str, Form(description="Policy name")],
    category: Annotated[PolicyCategory, Form()] = PolicyCategory.GENERAL,
    description: Annotated[str | None, Form()] = None,
    version: Annotated[str, Form()] = "1.0",
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,
) -> PolicyResponse:
    """Upload a new policy document.

    Supported file types: .txt, .md, .pdf
    """
    content = await file.read()

    metadata = PolicyCreate(
        name=name,
        description=description,
        category=category,
        version=version,
    )

    policy = await service.upload_policy(
        file_content=content,
        file_name=file.filename or "policy.txt",
        metadata=metadata,
    )

    return PolicyResponse.model_validate(policy)


@router.get(
    "",
    response_model=PaginatedResponse[PolicySummary],
    summary="List policies",
)
async def list_policies(
    category: PolicyCategory | None = None,
    include_archived: bool = False,
    page: int = 1,
    page_size: int = 20,
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
) -> PaginatedResponse[PolicySummary]:
    """List all policies with optional filtering."""
    offset = (page - 1) * page_size

    policies, total = await service.list_policies(
        category=category.value if category else None,
        include_archived=include_archived,
        offset=offset,
        limit=page_size,
    )

    items = [PolicySummary.model_validate(p) for p in policies]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/stats",
    response_model=VectorStoreStats,
    summary="Get vector store statistics",
)
async def get_vectorstore_stats(
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
) -> VectorStoreStats:
    """Get statistics about the policy vector store."""
    stats = service.get_vectorstore_stats()
    return VectorStoreStats.model_validate(stats)


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Get policy details",
)
async def get_policy(
    policy_id: str,
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
) -> PolicyResponse:
    """Get details of a specific policy."""
    policy = await service.get_policy(policy_id)
    return PolicyResponse.model_validate(policy)


@router.patch(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Update policy metadata",
)
async def update_policy(
    policy_id: str,
    update_data: PolicyUpdate,
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
    _rate_limit: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> PolicyResponse:
    """Update policy metadata. Triggers re-indexing if content-related fields change."""
    policy = await service.update_policy(policy_id, update_data)
    return PolicyResponse.model_validate(policy)


@router.delete(
    "/{policy_id}",
    response_model=SuccessResponse,
    summary="Delete a policy",
)
async def delete_policy(
    policy_id: str,
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
    _rate_limit: Annotated[None, Depends(rate_limit(10, 60))] = None,
) -> SuccessResponse:
    """Delete a policy and its indexed data."""
    await service.delete_policy(policy_id)
    return SuccessResponse(message="Policy deleted successfully")


@router.post(
    "/index",
    response_model=PolicyIndexResponse,
    summary="Index policies for RAG",
)
async def index_policies(
    request: PolicyIndexRequest,
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
    _rate_limit: Annotated[None, Depends(rate_limit(5, 60))] = None,
) -> PolicyIndexResponse:
    """Index policies into the vector store for RAG queries.

    If no policy_ids provided, indexes all unindexed active policies.
    Use force=true to reindex already indexed policies.
    """
    result = await service.index_all_policies(
        policy_ids=request.policy_ids,
        force=request.force,
    )
    return PolicyIndexResponse.model_validate(result)


@router.post(
    "/{policy_id}/index",
    response_model=PolicyIndexResponse,
    summary="Index a single policy",
)
async def index_single_policy(
    policy_id: str,
    force: bool = False,
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
    _rate_limit: Annotated[None, Depends(rate_limit(10, 60))] = None,
) -> PolicyIndexResponse:
    """Index a specific policy into the vector store."""
    policy = await service.get_policy(policy_id)
    chunks = await service.index_policy(policy_id, force)

    return PolicyIndexResponse(
        indexed_count=1,
        total_chunks=chunks,
        policies=[policy.name],
        errors=[],
    )


@router.delete(
    "/index/clear",
    response_model=SuccessResponse,
    summary="Clear vector store index",
)
async def clear_index(
    _current_user: CurrentUser = None,
    service: PolicyService = Depends(get_service),
    _rate_limit: Annotated[None, Depends(rate_limit(2, 60))] = None,
) -> SuccessResponse:
    """Clear all indexed data from the vector store.

    This does not delete the policies, only their embeddings.
    You'll need to re-index policies to use RAG queries.
    """
    deleted = await service.clear_index()
    return SuccessResponse(message=f"Cleared {deleted} chunks from vector store")
