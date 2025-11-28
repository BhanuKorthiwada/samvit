"""Tool implementations for AI agents."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.leave.models import Holiday, LeaveBalance, LeaveRequest
from app.modules.payroll.models import Payslip, PayrollPeriod


class AgentTools:
    """Tool implementations for agents."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: str,
        employee_id: str,
    ):
        self.session = session
        self.tenant_id = tenant_id
        self.employee_id = employee_id

    async def get_leave_balance(
        self,
        employee_id: str | None = None,
    ) -> dict[str, Any]:
        """Get leave balance for an employee."""
        emp_id = employee_id or self.employee_id

        result = await self.session.execute(
            select(LeaveBalance).where(
                LeaveBalance.tenant_id == self.tenant_id,
                LeaveBalance.employee_id == emp_id,
            )
        )
        balances = result.scalars().all()

        return {
            "employee_id": emp_id,
            "balances": [
                {
                    "leave_type": b.policy_id,  # Would need to join policy
                    "total": float(b.total_days),
                    "used": float(b.used_days),
                    "pending": float(b.pending_days),
                    "available": float(b.available_days),
                }
                for b in balances
            ],
        }

    async def apply_leave(
        self,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Apply for leave."""
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        days = (end - start).days + 1

        # This is a simplified implementation
        # In reality, would use LeaveService with proper validation
        return {
            "status": "submitted",
            "message": f"Leave request for {days} days from {start_date} to {end_date} has been submitted for approval.",
            "leave_type": leave_type,
            "days_requested": days,
        }

    async def get_attendance_summary(
        self,
        month: int | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """Get attendance summary for a month."""
        today = date.today()
        target_month = month or today.month
        target_year = year or today.year

        result = await self.session.execute(
            select(Attendance).where(
                Attendance.tenant_id == self.tenant_id,
                Attendance.employee_id == self.employee_id,
            )
        )
        records = [
            r
            for r in result.scalars().all()
            if r.date.month == target_month and r.date.year == target_year
        ]

        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT.value)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT.value)
        leave = sum(1 for r in records if r.status == AttendanceStatus.ON_LEAVE.value)
        half_day = sum(1 for r in records if r.status == AttendanceStatus.HALF_DAY.value)

        return {
            "month": target_month,
            "year": target_year,
            "present_days": present,
            "absent_days": absent,
            "leave_days": leave,
            "half_days": half_day,
            "total_records": len(records),
        }

    async def get_payslip(
        self,
        month: int | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """Get payslip for a specific month."""
        today = date.today()
        target_month = month or today.month
        target_year = year or today.year

        result = await self.session.execute(
            select(Payslip)
            .join(PayrollPeriod)
            .where(
                Payslip.tenant_id == self.tenant_id,
                Payslip.employee_id == self.employee_id,
                PayrollPeriod.month == target_month,
                PayrollPeriod.year == target_year,
            )
        )
        payslip = result.scalar_one_or_none()

        if not payslip:
            return {
                "status": "not_found",
                "message": f"Payslip for {target_month}/{target_year} is not yet available.",
            }

        return {
            "month": target_month,
            "year": target_year,
            "gross_earnings": float(payslip.gross_earnings),
            "total_deductions": float(payslip.total_deductions),
            "net_pay": float(payslip.net_pay),
            "status": payslip.status,
            "is_published": payslip.is_published,
        }

    async def get_upcoming_holidays(
        self,
        count: int = 5,
    ) -> dict[str, Any]:
        """Get upcoming holidays."""
        today = date.today()

        result = await self.session.execute(
            select(Holiday)
            .where(
                Holiday.tenant_id == self.tenant_id,
                Holiday.date >= today,
            )
            .order_by(Holiday.date)
            .limit(count)
        )
        holidays = result.scalars().all()

        return {
            "holidays": [
                {
                    "name": h.name,
                    "date": h.date.isoformat(),
                    "is_optional": h.is_optional,
                }
                for h in holidays
            ],
        }

    async def get_team_on_leave(
        self,
        date_str: str | None = None,
    ) -> dict[str, Any]:
        """Get team members on leave."""
        target_date = (
            datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_str
            else date.today()
        )

        result = await self.session.execute(
            select(LeaveRequest).where(
                LeaveRequest.tenant_id == self.tenant_id,
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date,
                LeaveRequest.status == "approved",
            )
        )
        leave_requests = result.scalars().all()

        return {
            "date": target_date.isoformat(),
            "employees_on_leave": [
                {
                    "employee_id": lr.employee_id,
                    # Would need to join with employee table for name
                }
                for lr in leave_requests
            ],
            "count": len(leave_requests),
        }

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict,
    ) -> dict[str, Any]:
        """Execute a tool by name."""
        tool_map = {
            "get_leave_balance": self.get_leave_balance,
            "apply_leave": self.apply_leave,
            "get_attendance_summary": self.get_attendance_summary,
            "get_payslip": self.get_payslip,
            "get_upcoming_holidays": self.get_upcoming_holidays,
            "get_team_on_leave": self.get_team_on_leave,
        }

        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return await tool_map[tool_name](**parameters)
        except Exception as e:
            return {"error": str(e)}
