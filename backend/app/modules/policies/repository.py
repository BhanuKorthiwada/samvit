"""Repository for policy data access."""

from sqlalchemy import select

from app.modules.policies.models import Policy, PolicyStatus
from app.shared.repository import TenantRepository


class PolicyRepository(TenantRepository[Policy]):
    """Repository for Policy model."""

    model = Policy

    async def get_by_category(
        self,
        category: str,
        include_archived: bool = False,
    ) -> list[Policy]:
        """Get policies by category."""
        query = self._apply_tenant_filter(
            select(Policy).where(Policy.category == category)
        )

        if not include_archived:
            query = query.where(Policy.status != PolicyStatus.ARCHIVED.value)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_policies(self) -> list[Policy]:
        """Get all active policies for the tenant."""
        query = self._apply_tenant_filter(
            select(Policy).where(Policy.status == PolicyStatus.ACTIVE.value)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unindexed_policies(self) -> list[Policy]:
        """Get policies that haven't been indexed."""
        query = self._apply_tenant_filter(
            select(Policy).where(
                Policy.status == PolicyStatus.ACTIVE.value,
                Policy.is_indexed == False,  # noqa: E712
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_ids(self, policy_ids: list[str]) -> list[Policy]:
        """Get policies by list of IDs."""
        if not policy_ids:
            return []

        query = self._apply_tenant_filter(
            select(Policy).where(Policy.id.in_(policy_ids))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_by_name(self, search_term: str) -> list[Policy]:
        """Search policies by name."""
        query = self._apply_tenant_filter(
            select(Policy).where(
                Policy.name.ilike(f"%{search_term}%"),
                Policy.status != PolicyStatus.ARCHIVED.value,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_name(
        self,
        name: str,
        exclude_archived: bool = True,
    ) -> Policy | None:
        """Get policy by exact name (case-insensitive)."""
        query = self._apply_tenant_filter(select(Policy).where(Policy.name.ilike(name)))

        if exclude_archived:
            query = query.where(Policy.status != PolicyStatus.ARCHIVED.value)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()
