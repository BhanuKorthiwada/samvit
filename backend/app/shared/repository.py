"""Base repository for common database operations."""

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import current_tenant_id
from app.core.exceptions import EntityNotFoundError, TenantMismatchError
from app.shared.models import BaseModel, TenantBaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
TenantModelType = TypeVar("TenantModelType", bound=TenantBaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository for non-tenant models."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> ModelType | None:
        """Get entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, id: str) -> ModelType:
        """Get entity by ID or raise EntityNotFoundError."""
        entity = await self.get_by_id(id)
        if not entity:
            raise EntityNotFoundError(self.model.__name__, id)
        return entity

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count all entities."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, entity: ModelType) -> ModelType:
        """Create a new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Update an existing entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Delete an entity."""
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_id(self, id: str) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
            return True
        return False


class TenantRepository(Generic[TenantModelType]):
    """Base repository for tenant-scoped models."""

    model: type[TenantModelType]

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    def _apply_tenant_filter(self, query: Select) -> Select:
        """Apply tenant filter to query."""
        return query.where(self.model.tenant_id == self.tenant_id)

    def _verify_tenant(self, entity: TenantModelType) -> None:
        """Verify entity belongs to current tenant."""
        if entity.tenant_id != self.tenant_id:
            raise TenantMismatchError()

    async def get_by_id(self, id: str) -> TenantModelType | None:
        """Get entity by ID within tenant scope."""
        result = await self.session.execute(
            self._apply_tenant_filter(select(self.model).where(self.model.id == id))
        )
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, id: str) -> TenantModelType:
        """Get entity by ID or raise EntityNotFoundError."""
        entity = await self.get_by_id(id)
        if not entity:
            raise EntityNotFoundError(self.model.__name__, id)
        return entity

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[TenantModelType]:
        """Get all entities within tenant scope with pagination."""
        query = self._apply_tenant_filter(select(self.model))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities within tenant scope."""
        query = self._apply_tenant_filter(select(func.count()).select_from(self.model))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, entity: TenantModelType) -> TenantModelType:
        """Create a new entity with tenant_id."""
        # Ensure tenant_id is set
        entity.tenant_id = self.tenant_id
        current_tenant_id.set(self.tenant_id)

        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: TenantModelType) -> TenantModelType:
        """Update an existing entity."""
        self._verify_tenant(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: TenantModelType) -> None:
        """Delete an entity."""
        self._verify_tenant(entity)
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_id(self, id: str) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
            return True
        return False
