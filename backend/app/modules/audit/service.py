"""Audit logging service."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditLog
from app.core.exceptions import EntityNotFoundError


class AuditService:
    """Service for querying audit logs."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def get_audit_log(self, audit_id: str) -> AuditLog:
        """Get a specific audit log by ID."""
        query = select(AuditLog).where(
            AuditLog.id == audit_id,
            AuditLog.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(query)
        audit_log = result.scalar_one_or_none()

        if not audit_log:
            raise EntityNotFoundError("AuditLog", audit_id)

        return audit_log

    async def list_audit_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        user_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """List audit logs with optional filters."""
        query = select(AuditLog).where(AuditLog.tenant_id == self.tenant_id)

        # Apply filters
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        audit_logs = list(result.scalars().all())

        return audit_logs, total

    async def get_user_audit_logs(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Get all audit logs for a specific user."""
        return await self.list_audit_logs(
            offset=offset,
            limit=limit,
            user_id=user_id,
        )

    async def get_entity_audit_logs(
        self,
        entity_type: str,
        entity_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Get all audit logs for a specific entity."""
        return await self.list_audit_logs(
            offset=offset,
            limit=limit,
            entity_type=entity_type,
            entity_id=entity_id,
        )

    async def get_audit_stats(self) -> dict:
        """Get audit log statistics."""
        # Total count
        total_query = select(func.count(AuditLog.id)).where(
            AuditLog.tenant_id == self.tenant_id
        )
        total_result = await self.session.execute(total_query)
        total_logs = total_result.scalar() or 0

        # Actions breakdown
        actions_query = (
            select(AuditLog.action, func.count(AuditLog.id))
            .where(AuditLog.tenant_id == self.tenant_id)
            .group_by(AuditLog.action)
        )
        actions_result = await self.session.execute(actions_query)
        actions_breakdown = {row[0]: row[1] for row in actions_result.all()}

        # Entity types breakdown
        entity_query = (
            select(AuditLog.entity_type, func.count(AuditLog.id))
            .where(
                AuditLog.tenant_id == self.tenant_id,
                AuditLog.entity_type.isnot(None),
            )
            .group_by(AuditLog.entity_type)
        )
        entity_result = await self.session.execute(entity_query)
        entity_types_breakdown = {row[0]: row[1] for row in entity_result.all()}

        # Top users by activity
        users_query = (
            select(AuditLog.user_id, func.count(AuditLog.id).label("count"))
            .where(AuditLog.tenant_id == self.tenant_id)
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )
        users_result = await self.session.execute(users_query)
        top_users = [
            {"user_id": row[0], "action_count": row[1]} for row in users_result.all()
        ]

        return {
            "total_logs": total_logs,
            "actions_breakdown": actions_breakdown,
            "entity_types_breakdown": entity_types_breakdown,
            "top_users": top_users,
        }
