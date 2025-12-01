"""Platform service - Business logic for platform administration."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from app.modules.auth.models import User
from app.modules.employees.models import Employee
from app.modules.platform.schemas import PlatformStatsResponse, TenantStatsResponse
from app.modules.tenants.models import Tenant, TenantStatus
from app.modules.tenants.schemas import TenantCreate, TenantUpdate


class PlatformService:
    """Service for platform-level administration."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_platform_stats(self) -> PlatformStatsResponse:
        """Get platform-wide statistics."""
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        total_tenants = await self.session.scalar(select(func.count(Tenant.id)))
        active_tenants = await self.session.scalar(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.ACTIVE.value
            )
        )
        suspended_tenants = await self.session.scalar(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.SUSPENDED.value
            )
        )
        pending_tenants = await self.session.scalar(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.PENDING.value
            )
        )
        total_users = await self.session.scalar(select(func.count(User.id)))
        total_employees = await self.session.scalar(select(func.count(Employee.id)))
        tenants_last_30_days = await self.session.scalar(
            select(func.count(Tenant.id)).where(Tenant.created_at >= thirty_days_ago)
        )
        tenants_last_7_days = await self.session.scalar(
            select(func.count(Tenant.id)).where(Tenant.created_at >= seven_days_ago)
        )

        return PlatformStatsResponse(
            total_tenants=total_tenants or 0,
            active_tenants=active_tenants or 0,
            suspended_tenants=suspended_tenants or 0,
            pending_tenants=pending_tenants or 0,
            total_users=total_users or 0,
            total_employees=total_employees or 0,
            tenants_created_last_30_days=tenants_last_30_days or 0,
            tenants_created_last_7_days=tenants_last_7_days or 0,
        )

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        domain = data.domain.lower()

        if domain in settings.reserved_domains:
            raise EntityAlreadyExistsError("Tenant", f"Domain '{domain}' is reserved")

        existing_domain = await self.session.scalar(
            select(Tenant).where(Tenant.domain == domain)
        )
        if existing_domain:
            raise EntityAlreadyExistsError("Tenant", domain)

        existing_email = await self.session.scalar(
            select(Tenant).where(Tenant.email == data.email)
        )
        if existing_email:
            raise EntityAlreadyExistsError("Tenant", data.email)

        tenant = Tenant(
            name=data.name,
            domain=domain,
            email=data.email,
            phone=data.phone,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            timezone=data.timezone,
            currency=data.currency,
            status=TenantStatus.PENDING.value,
        )
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        """Get tenant by ID."""
        tenant = await self.session.get(Tenant, tenant_id)
        if not tenant:
            raise EntityNotFoundError("Tenant", tenant_id)
        return tenant

    async def get_tenant_by_domain(self, domain: str) -> Tenant:
        """Get tenant by domain."""
        tenant = await self.session.scalar(
            select(Tenant).where(Tenant.domain == domain.lower())
        )
        if not tenant:
            raise EntityNotFoundError("Tenant", domain)
        return tenant

    async def update_tenant(self, tenant_id: str, data: TenantUpdate) -> Tenant:
        """Update tenant."""
        tenant = await self.get_tenant(tenant_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def activate_tenant(self, tenant_id: str) -> Tenant:
        """Activate a tenant."""
        tenant = await self.get_tenant(tenant_id)
        tenant.status = TenantStatus.ACTIVE.value
        tenant.is_active = True
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def suspend_tenant(self, tenant_id: str) -> Tenant:
        """Suspend a tenant."""
        tenant = await self.get_tenant(tenant_id)
        tenant.status = TenantStatus.SUSPENDED.value
        tenant.is_active = False
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def delete_tenant(self, tenant_id: str) -> None:
        """Delete a tenant."""
        tenant = await self.get_tenant(tenant_id)
        await self.session.delete(tenant)
        await self.session.flush()

    async def get_tenant_stats(self, tenant_id: str) -> TenantStatsResponse | None:
        """Get statistics for a specific tenant."""
        tenant = await self.session.get(Tenant, tenant_id)
        if not tenant:
            return None

        user_count = await self.session.scalar(
            select(func.count(User.id)).where(User.tenant_id == tenant_id)
        )
        employee_count = await self.session.scalar(
            select(func.count(Employee.id)).where(Employee.tenant_id == tenant_id)
        )

        return TenantStatsResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            domain=tenant.domain,
            status=tenant.status,
            user_count=user_count or 0,
            employee_count=employee_count or 0,
            created_at=tenant.created_at,
            last_activity=tenant.updated_at,
        )

    async def get_all_tenant_stats(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[TenantStatsResponse], int]:
        """Get statistics for all tenants with pagination."""
        result = await self.session.execute(
            select(Tenant)
            .offset(offset)
            .limit(limit)
            .order_by(Tenant.created_at.desc())
        )
        tenants = result.scalars().all()
        total = await self.session.scalar(select(func.count(Tenant.id)))

        stats_list = []
        for tenant in tenants:
            user_count = await self.session.scalar(
                select(func.count(User.id)).where(User.tenant_id == tenant.id)
            )
            employee_count = await self.session.scalar(
                select(func.count(Employee.id)).where(Employee.tenant_id == tenant.id)
            )
            stats_list.append(
                TenantStatsResponse(
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    domain=tenant.domain,
                    status=tenant.status,
                    user_count=user_count or 0,
                    employee_count=employee_count or 0,
                    created_at=tenant.created_at,
                    last_activity=tenant.updated_at,
                )
            )

        return stats_list, total or 0

    async def search_tenants(
        self,
        query: str,
        status: str | None = None,
        limit: int = 20,
    ) -> list[TenantStatsResponse]:
        """Search tenants by name or domain."""
        stmt = select(Tenant).where(
            (Tenant.name.ilike(f"%{query}%")) | (Tenant.domain.ilike(f"%{query}%"))
        )
        if status:
            stmt = stmt.where(Tenant.status == status)
        stmt = stmt.limit(limit).order_by(Tenant.name)

        result = await self.session.execute(stmt)
        tenants = result.scalars().all()

        stats_list = []
        for tenant in tenants:
            user_count = await self.session.scalar(
                select(func.count(User.id)).where(User.tenant_id == tenant.id)
            )
            employee_count = await self.session.scalar(
                select(func.count(Employee.id)).where(Employee.tenant_id == tenant.id)
            )
            stats_list.append(
                TenantStatsResponse(
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    domain=tenant.domain,
                    status=tenant.status,
                    user_count=user_count or 0,
                    employee_count=employee_count or 0,
                    created_at=tenant.created_at,
                    last_activity=tenant.updated_at,
                )
            )

        return stats_list
