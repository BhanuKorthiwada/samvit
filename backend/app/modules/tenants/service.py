"""Tenant service - business logic layer."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from app.modules.tenants.models import Tenant, TenantStatus
from app.modules.tenants.repository import TenantRepository
from app.modules.tenants.schemas import TenantCreate, TenantUpdate


class TenantService:
    """Service for tenant business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TenantRepository(session)

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        # Check if slug exists
        if await self.repository.slug_exists(data.slug):
            raise EntityAlreadyExistsError("Tenant", data.slug)

        # Check if email exists
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise EntityAlreadyExistsError("Tenant", data.email)

        tenant = Tenant(
            name=data.name,
            slug=data.slug,
            email=data.email,
            phone=data.phone,
            domain=data.domain,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            timezone=data.timezone,
            currency=data.currency,
            status=TenantStatus.PENDING.value,
        )

        return await self.repository.create(tenant)

    async def get_tenant(self, tenant_id: str) -> Tenant:
        """Get tenant by ID."""
        tenant = await self.repository.get_by_id(tenant_id)
        if not tenant:
            raise EntityNotFoundError("Tenant", tenant_id)
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        """Get tenant by slug."""
        tenant = await self.repository.get_by_slug(slug)
        if not tenant:
            raise EntityNotFoundError("Tenant", slug)
        return tenant

    async def update_tenant(
        self,
        tenant_id: str,
        data: TenantUpdate,
    ) -> Tenant:
        """Update tenant."""
        tenant = await self.get_tenant(tenant_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        return await self.repository.update(tenant)

    async def activate_tenant(self, tenant_id: str) -> Tenant:
        """Activate a tenant."""
        tenant = await self.get_tenant(tenant_id)
        tenant.status = TenantStatus.ACTIVE.value
        tenant.is_active = True
        return await self.repository.update(tenant)

    async def suspend_tenant(self, tenant_id: str) -> Tenant:
        """Suspend a tenant."""
        tenant = await self.get_tenant(tenant_id)
        tenant.status = TenantStatus.SUSPENDED.value
        tenant.is_active = False
        return await self.repository.update(tenant)

    async def list_tenants(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Tenant], int]:
        """List all tenants with count."""
        tenants = await self.repository.get_all(offset=offset, limit=limit)
        total = await self.repository.count()
        return tenants, total

    async def delete_tenant(self, tenant_id: str) -> None:
        """Delete a tenant (soft delete recommended in production)."""
        tenant = await self.get_tenant(tenant_id)
        await self.repository.delete(tenant)
