"""Tenant repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.shared.repository import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant operations."""

    model = Tenant

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Get tenant by slug."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Tenant | None:
        """Get tenant by custom domain."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.domain == domain)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Tenant | None:
        """Get tenant by email."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.email == email)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        """Check if slug exists."""
        query = select(Tenant.id).where(Tenant.slug == slug)
        if exclude_id:
            query = query.where(Tenant.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_active_tenants(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Tenant]:
        """Get all active tenants."""
        result = await self.session.execute(
            select(Tenant)
            .where(Tenant.is_active.is_(True))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
