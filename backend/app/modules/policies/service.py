"""Service layer for policy management."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.document_loader import ChunkingConfig, DocumentLoader
from app.ai.rag.vectorstore import PolicyVectorStore
from app.core.exceptions import EntityAlreadyExistsError, ValidationError
from app.modules.policies.models import Policy, PolicyStatus
from app.modules.policies.repository import PolicyRepository
from app.modules.policies.schemas import PolicyCreate, PolicyUpdate

logger = logging.getLogger(__name__)


POLICIES_BASE_DIR = Path("data/policies")


def get_tenant_policy_dir(tenant_id: str) -> Path:
    """Get the policy directory for a tenant."""
    path = POLICIES_BASE_DIR / tenant_id
    path.mkdir(parents=True, exist_ok=True)
    return path


class PolicyService:
    """Service for managing policies and their indexing."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = PolicyRepository(session, tenant_id)
        self.vectorstore = PolicyVectorStore(tenant_id)
        self.document_loader = DocumentLoader(
            ChunkingConfig(
                chunk_size=1000,
                chunk_overlap=200,
            )
        )

    async def upload_policy(
        self,
        file_content: bytes,
        file_name: str,
        metadata: PolicyCreate,
    ) -> Policy:
        """Upload a policy document and create metadata record."""
        file_ext = Path(file_name).suffix.lower()

        if file_ext not in DocumentLoader.SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file type: {file_ext}. "
                f"Supported: {DocumentLoader.SUPPORTED_EXTENSIONS}"
            )

        existing = await self.repo.get_by_name(metadata.name)
        if existing:
            raise EntityAlreadyExistsError("Policy", metadata.name)

        policy_dir = get_tenant_policy_dir(self.tenant_id)

        import uuid

        unique_name = f"{uuid.uuid4().hex[:8]}_{file_name}"
        file_path = policy_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(file_content)

        policy = Policy(
            tenant_id=self.tenant_id,
            name=metadata.name,
            description=metadata.description,
            category=metadata.category.value,
            file_path=str(file_path.relative_to(POLICIES_BASE_DIR.parent)),
            file_name=file_name,
            file_type=file_ext.lstrip("."),
            file_size=len(file_content),
            version=metadata.version,
            effective_date=metadata.effective_date,
            expiry_date=metadata.expiry_date,
            status=PolicyStatus.ACTIVE.value,
            is_indexed=False,
        )

        self.session.add(policy)
        await self.session.flush()
        await self.session.refresh(policy)

        logger.info(
            "Policy '%s' uploaded for tenant %s (file: %s)",
            policy.name,
            self.tenant_id,
            file_path,
        )

        return policy

    async def get_policy(self, policy_id: str) -> Policy:
        """Get policy by ID."""
        return await self.repo.get_by_id_or_raise(policy_id)

    async def list_policies(
        self,
        category: str | None = None,
        status: str | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Policy], int]:
        """List policies with optional filtering."""
        if category:
            policies = await self.repo.get_by_category(category, include_archived)
        else:
            policies = await self.repo.get_active_policies()
            if include_archived:
                policies = await self.repo.get_all(offset=0, limit=1000)

        if status:
            policies = [p for p in policies if p.status == status]

        total = len(policies)
        policies = policies[offset : offset + limit]

        return policies, total

    async def update_policy(
        self,
        policy_id: str,
        update_data: PolicyUpdate,
    ) -> Policy:
        """Update policy metadata."""
        policy = await self.repo.get_by_id_or_raise(policy_id)

        updates = update_data.model_dump(exclude_unset=True)

        if "category" in updates and updates["category"]:
            updates["category"] = updates["category"].value
        if "status" in updates and updates["status"]:
            updates["status"] = updates["status"].value

        for field, value in updates.items():
            setattr(policy, field, value)

        await self.session.flush()
        await self.session.refresh(policy)

        if policy.is_indexed:
            policy.is_indexed = False
            await self.session.flush()

        logger.info("Policy '%s' updated", policy.name)
        return policy

    async def delete_policy(self, policy_id: str) -> None:
        """Delete a policy and its indexed data."""
        policy = await self.repo.get_by_id_or_raise(policy_id)

        self.vectorstore.delete_policy(policy_id)

        file_path = POLICIES_BASE_DIR.parent / policy.file_path
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted policy file: %s", file_path)

        await self.session.delete(policy)
        await self.session.flush()

        logger.info("Policy '%s' deleted", policy.name)

    async def index_policy(self, policy_id: str, force: bool = False) -> int:
        """Index a single policy in the vector store.

        Returns the number of chunks created.
        """
        policy = await self.repo.get_by_id_or_raise(policy_id)

        if policy.is_indexed and not force:
            logger.info("Policy '%s' already indexed, skipping", policy.name)
            return policy.chunk_count

        file_path = POLICIES_BASE_DIR.parent / policy.file_path
        if not file_path.exists():
            raise ValidationError(f"Policy file not found: {file_path}")

        if force and policy.is_indexed:
            self.vectorstore.delete_policy(policy_id)

        chunks = self.document_loader.load_and_chunk(
            file_path,
            metadata={
                "policy_id": policy.id,
                "policy_name": policy.name,
                "category": policy.category,
                "version": policy.version,
            },
        )

        chunk_count = self.vectorstore.add_chunks(chunks, policy_id)

        policy.is_indexed = True
        policy.indexed_at = datetime.now(timezone.utc)
        policy.chunk_count = chunk_count
        await self.session.flush()

        logger.info(
            "Policy '%s' indexed with %d chunks",
            policy.name,
            chunk_count,
        )

        return chunk_count

    async def index_all_policies(
        self,
        policy_ids: list[str] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Index multiple policies.

        Returns summary of indexing operation.
        """
        if policy_ids:
            policies = await self.repo.get_by_ids(policy_ids)
        else:
            if force:
                policies = await self.repo.get_active_policies()
            else:
                policies = await self.repo.get_unindexed_policies()

        indexed_count = 0
        total_chunks = 0
        indexed_policies = []
        errors = []

        for policy in policies:
            try:
                chunks = await self.index_policy(policy.id, force)
                indexed_count += 1
                total_chunks += chunks
                indexed_policies.append(policy.name)
            except Exception as e:
                logger.error("Failed to index policy '%s': %s", policy.name, e)
                errors.append(f"{policy.name}: {str(e)}")

        return {
            "indexed_count": indexed_count,
            "total_chunks": total_chunks,
            "policies": indexed_policies,
            "errors": errors,
        }

    def get_vectorstore_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        return self.vectorstore.get_stats()

    async def clear_index(self) -> int:
        """Clear all indexed data for the tenant.

        Returns number of chunks deleted.
        """
        deleted = self.vectorstore.clear()

        policies = await self.repo.get_active_policies()
        for policy in policies:
            policy.is_indexed = False
            policy.indexed_at = None
            policy.chunk_count = 0

        await self.session.flush()

        logger.info(
            "Cleared vector store for tenant %s (%d chunks)",
            self.tenant_id,
            deleted,
        )

        return deleted
