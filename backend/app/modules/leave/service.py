"""Leave management service."""

from datetime import date, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleViolationError,
    EntityNotFoundError,
)
from app.modules.leave.models import (
    DayType,
    Holiday,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveStatus,
)
from app.modules.leave.schemas import (
    HolidayCreate,
    LeaveApproval,
    LeavePolicyCreate,
    LeavePolicyUpdate,
    LeaveRequestCreate,
)


class LeaveService:
    """Service for leave management."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    # --- Leave Policy Operations ---

    async def create_policy(self, data: LeavePolicyCreate) -> LeavePolicy:
        """Create a leave policy."""
        policy = LeavePolicy(
            tenant_id=self.tenant_id,
            name=data.name,
            leave_type=data.leave_type.value,
            description=data.description,
            annual_allocation=data.annual_allocation,
            max_accumulation=data.max_accumulation,
            carry_forward_limit=data.carry_forward_limit,
            min_days=data.min_days,
            max_days=data.max_days,
            advance_notice_days=data.advance_notice_days,
            requires_attachment=data.requires_attachment,
            attachment_after_days=data.attachment_after_days,
            applicable_gender=data.applicable_gender,
            min_tenure_months=data.min_tenure_months,
            is_paid=data.is_paid,
        )
        self.session.add(policy)
        await self.session.flush()
        await self.session.refresh(policy)
        return policy

    async def get_policy(self, policy_id: str) -> LeavePolicy:
        """Get leave policy by ID."""
        result = await self.session.execute(
            select(LeavePolicy).where(
                LeavePolicy.id == policy_id,
                LeavePolicy.tenant_id == self.tenant_id,
            )
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise EntityNotFoundError("LeavePolicy", policy_id)
        return policy

    async def list_policies(self, active_only: bool = True) -> list[LeavePolicy]:
        """List all leave policies."""
        query = select(LeavePolicy).where(LeavePolicy.tenant_id == self.tenant_id)
        if active_only:
            query = query.where(LeavePolicy.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_policy(
        self,
        policy_id: str,
        data: LeavePolicyUpdate,
    ) -> LeavePolicy:
        """Update leave policy."""
        policy = await self.get_policy(policy_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
        await self.session.flush()
        await self.session.refresh(policy)
        return policy

    # --- Leave Balance Operations ---

    async def get_employee_balances(
        self,
        employee_id: str,
        year: int | None = None,
    ) -> list[LeaveBalance]:
        """Get employee leave balances."""
        if year is None:
            year = date.today().year

        result = await self.session.execute(
            select(LeaveBalance).where(
                LeaveBalance.tenant_id == self.tenant_id,
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year,
            )
        )
        return list(result.scalars().all())

    async def initialize_balances(
        self,
        employee_id: str,
        year: int | None = None,
    ) -> list[LeaveBalance]:
        """Initialize leave balances for an employee for the year."""
        if year is None:
            year = date.today().year

        policies = await self.list_policies()
        balances = []

        for policy in policies:
            # Check if balance already exists
            existing = await self.session.execute(
                select(LeaveBalance).where(
                    LeaveBalance.tenant_id == self.tenant_id,
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.policy_id == policy.id,
                    LeaveBalance.year == year,
                )
            )
            if existing.scalar_one_or_none():
                continue

            balance = LeaveBalance(
                tenant_id=self.tenant_id,
                employee_id=employee_id,
                policy_id=policy.id,
                year=year,
                opening_balance=0,
                credited=float(policy.annual_allocation),
                used=0,
                pending=0,
            )
            self.session.add(balance)
            balances.append(balance)

        await self.session.flush()
        return balances

    # --- Leave Request Operations ---

    async def create_request(
        self,
        employee_id: str,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a leave request."""
        policy = await self.get_policy(data.policy_id)

        # Calculate total days
        total_days = self._calculate_leave_days(
            data.start_date,
            data.end_date,
            data.start_day_type,
            data.end_day_type,
        )

        # Validate against policy
        if policy.min_days and total_days < float(policy.min_days):
            raise BusinessRuleViolationError(
                "min_days",
                f"Minimum leave days for this type is {policy.min_days}",
            )

        if policy.max_days and total_days > float(policy.max_days):
            raise BusinessRuleViolationError(
                "max_days",
                f"Maximum leave days for this type is {policy.max_days}",
            )

        # Check balance
        balances = await self.get_employee_balances(employee_id, data.start_date.year)
        balance = next((b for b in balances if b.policy_id == data.policy_id), None)

        if balance and balance.available < total_days:
            raise BusinessRuleViolationError(
                "insufficient_balance",
                f"Insufficient leave balance. Available: {balance.available}, Requested: {total_days}",
            )

        # Check advance notice
        days_in_advance = (data.start_date - date.today()).days
        if policy.advance_notice_days and days_in_advance < policy.advance_notice_days:
            raise BusinessRuleViolationError(
                "advance_notice",
                f"Leave must be applied {policy.advance_notice_days} days in advance",
            )

        # Create request
        request = LeaveRequest(
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            policy_id=data.policy_id,
            start_date=data.start_date,
            end_date=data.end_date,
            start_day_type=data.start_day_type.value,
            end_day_type=data.end_day_type.value,
            total_days=total_days,
            reason=data.reason,
            attachment_url=data.attachment_url,
            status=LeaveStatus.PENDING.value,
        )
        self.session.add(request)

        # Update pending balance
        if balance:
            balance.pending = float(balance.pending) + total_days

        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def get_request(self, request_id: str) -> LeaveRequest:
        """Get leave request by ID."""
        result = await self.session.execute(
            select(LeaveRequest).where(
                LeaveRequest.id == request_id,
                LeaveRequest.tenant_id == self.tenant_id,
            )
        )
        request = result.scalar_one_or_none()
        if not request:
            raise EntityNotFoundError("LeaveRequest", request_id)
        return request

    async def get_employee_requests(
        self,
        employee_id: str,
        status: LeaveStatus | None = None,
        year: int | None = None,
    ) -> list[LeaveRequest]:
        """Get employee's leave requests."""
        query = select(LeaveRequest).where(
            LeaveRequest.tenant_id == self.tenant_id,
            LeaveRequest.employee_id == employee_id,
        )

        if status:
            query = query.where(LeaveRequest.status == status.value)

        if year:
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            query = query.where(
                LeaveRequest.start_date >= start,
                LeaveRequest.start_date <= end,
            )

        query = query.order_by(LeaveRequest.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_approvals(
        self,
        approver_id: str,
    ) -> list[LeaveRequest]:
        """Get pending leave requests for approval."""
        # In a real app, this would check if approver_id is the reporting manager
        result = await self.session.execute(
            select(LeaveRequest)
            .where(
                LeaveRequest.tenant_id == self.tenant_id,
                LeaveRequest.status == LeaveStatus.PENDING.value,
            )
            .order_by(LeaveRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def process_approval(
        self,
        request_id: str,
        approver_id: str,
        data: LeaveApproval,
    ) -> LeaveRequest:
        """Approve or reject a leave request."""
        request = await self.get_request(request_id)

        if request.status != LeaveStatus.PENDING.value:
            raise BusinessRuleViolationError(
                "invalid_status",
                "Only pending requests can be approved/rejected",
            )

        if data.action == "approve":
            request.status = LeaveStatus.APPROVED.value

            # Update balance: move from pending to used
            balance = await self._get_balance(
                request.employee_id,
                request.policy_id,
                request.start_date.year,
            )
            if balance:
                balance.pending = float(balance.pending) - float(request.total_days)
                balance.used = float(balance.used) + float(request.total_days)

        else:
            request.status = LeaveStatus.REJECTED.value

            # Remove from pending
            balance = await self._get_balance(
                request.employee_id,
                request.policy_id,
                request.start_date.year,
            )
            if balance:
                balance.pending = float(balance.pending) - float(request.total_days)

        request.approver_id = approver_id
        request.approved_at = date.today()
        request.approver_remarks = data.remarks

        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def cancel_request(
        self,
        request_id: str,
        employee_id: str,
    ) -> LeaveRequest:
        """Cancel a leave request."""
        request = await self.get_request(request_id)

        if request.employee_id != employee_id:
            raise BusinessRuleViolationError(
                "not_owner",
                "You can only cancel your own leave requests",
            )

        if request.status not in [
            LeaveStatus.PENDING.value,
            LeaveStatus.APPROVED.value,
        ]:
            raise BusinessRuleViolationError(
                "invalid_status",
                "Only pending or approved requests can be cancelled",
            )

        # Update balance
        balance = await self._get_balance(
            request.employee_id,
            request.policy_id,
            request.start_date.year,
        )

        if balance:
            if request.status == LeaveStatus.PENDING.value:
                balance.pending = float(balance.pending) - float(request.total_days)
            elif request.status == LeaveStatus.APPROVED.value:
                balance.used = float(balance.used) - float(request.total_days)

        request.status = LeaveStatus.CANCELLED.value

        await self.session.flush()
        await self.session.refresh(request)
        return request

    # --- Holiday Operations ---

    async def create_holiday(self, data: HolidayCreate) -> Holiday:
        """Create a holiday."""
        holiday = Holiday(
            tenant_id=self.tenant_id,
            name=data.name,
            date=data.date,
            description=data.description,
            is_optional=data.is_optional,
        )
        self.session.add(holiday)
        await self.session.flush()
        await self.session.refresh(holiday)
        return holiday

    async def list_holidays(self, year: int | None = None) -> list[Holiday]:
        """List holidays for a year."""
        if year is None:
            year = date.today().year

        start = date(year, 1, 1)
        end = date(year, 12, 31)

        result = await self.session.execute(
            select(Holiday)
            .where(
                Holiday.tenant_id == self.tenant_id,
                Holiday.date >= start,
                Holiday.date <= end,
                Holiday.is_active.is_(True),
            )
            .order_by(Holiday.date)
        )
        return list(result.scalars().all())

    # --- Helper Methods ---

    def _calculate_leave_days(
        self,
        start_date: date,
        end_date: date,
        start_type: DayType,
        end_type: DayType,
    ) -> float:
        """Calculate total leave days excluding weekends."""
        total = 0.0
        current = start_date

        while current <= end_date:
            # Skip weekends (Saturday=5, Sunday=6)
            if current.weekday() < 5:
                if current == start_date and start_type != DayType.FULL:
                    total += 0.5
                elif current == end_date and end_type != DayType.FULL:
                    total += 0.5
                else:
                    total += 1.0
            current += timedelta(days=1)

        return total

    async def _get_balance(
        self,
        employee_id: str,
        policy_id: str,
        year: int,
    ) -> LeaveBalance | None:
        """Get specific leave balance."""
        result = await self.session.execute(
            select(LeaveBalance).where(
                and_(
                    LeaveBalance.tenant_id == self.tenant_id,
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.policy_id == policy_id,
                    LeaveBalance.year == year,
                )
            )
        )
        return result.scalar_one_or_none()
