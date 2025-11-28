"""Attendance service."""

from datetime import date, datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError
from app.modules.attendance.models import (
    Attendance,
    AttendanceStatus,
    ClockType,
    Shift,
    TimeEntry,
)
from app.modules.attendance.schemas import (
    AttendanceRegularize,
    ClockInRequest,
    ClockOutRequest,
    ShiftCreate,
    ShiftUpdate,
)


class AttendanceService:
    """Service for attendance operations."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    # --- Shift Operations ---

    async def create_shift(self, data: ShiftCreate) -> Shift:
        """Create a new shift."""
        shift = Shift(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            start_time=data.start_time,
            end_time=data.end_time,
            break_duration_minutes=data.break_duration_minutes,
            grace_period_minutes=data.grace_period_minutes,
            is_night_shift=data.is_night_shift,
            is_default=data.is_default,
        )
        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    async def get_shift(self, shift_id: str) -> Shift:
        """Get shift by ID."""
        result = await self.session.execute(
            select(Shift).where(
                Shift.id == shift_id,
                Shift.tenant_id == self.tenant_id,
            )
        )
        shift = result.scalar_one_or_none()
        if not shift:
            raise EntityNotFoundError("Shift", shift_id)
        return shift

    async def list_shifts(self) -> list[Shift]:
        """List all shifts."""
        result = await self.session.execute(
            select(Shift).where(Shift.tenant_id == self.tenant_id)
        )
        return list(result.scalars().all())

    async def update_shift(self, shift_id: str, data: ShiftUpdate) -> Shift:
        """Update a shift."""
        shift = await self.get_shift(shift_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shift, field, value)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    # --- Clock In/Out Operations ---

    async def clock_in(
        self,
        data: ClockInRequest,
        employee_id: str,
        ip_address: str | None = None,
    ) -> TimeEntry:
        """Record clock in."""
        effective_employee_id = data.employee_id or employee_id
        now = datetime.now(timezone.utc)
        today = now.date()

        # Check if already clocked in today
        existing = await self._get_today_attendance(effective_employee_id, today)
        if existing and existing.clock_in and not existing.clock_out:
            raise BusinessRuleViolationError(
                "already_clocked_in",
                "You are already clocked in. Please clock out first.",
            )

        # Create time entry
        time_entry = TimeEntry(
            tenant_id=self.tenant_id,
            employee_id=effective_employee_id,
            entry_type=ClockType.CLOCK_IN.value,
            timestamp=now,
            source="web",
            location=data.location,
            ip_address=ip_address,
            notes=data.notes,
        )
        self.session.add(time_entry)

        # Update or create attendance record
        if existing:
            existing.clock_in = now
            existing.status = AttendanceStatus.PRESENT.value
        else:
            attendance = Attendance(
                tenant_id=self.tenant_id,
                employee_id=effective_employee_id,
                date=today,
                status=AttendanceStatus.PRESENT.value,
                clock_in=now,
            )
            self.session.add(attendance)

        await self.session.flush()
        await self.session.refresh(time_entry)
        return time_entry

    async def clock_out(
        self,
        data: ClockOutRequest,
        employee_id: str,
        ip_address: str | None = None,
    ) -> TimeEntry:
        """Record clock out."""
        effective_employee_id = data.employee_id or employee_id
        now = datetime.now(timezone.utc)
        today = now.date()

        # Check if clocked in
        attendance = await self._get_today_attendance(effective_employee_id, today)
        if not attendance or not attendance.clock_in:
            raise BusinessRuleViolationError(
                "not_clocked_in",
                "You need to clock in first.",
            )

        if attendance.clock_out:
            raise BusinessRuleViolationError(
                "already_clocked_out",
                "You have already clocked out today.",
            )

        # Create time entry
        time_entry = TimeEntry(
            tenant_id=self.tenant_id,
            employee_id=effective_employee_id,
            entry_type=ClockType.CLOCK_OUT.value,
            timestamp=now,
            source="web",
            location=data.location,
            ip_address=ip_address,
            notes=data.notes,
        )
        self.session.add(time_entry)

        # Update attendance
        attendance.clock_out = now
        if attendance.clock_in:
            work_seconds = (now - attendance.clock_in).total_seconds()
            attendance.work_hours = round(work_seconds / 3600, 2)

        await self.session.flush()
        await self.session.refresh(time_entry)
        return time_entry

    # --- Attendance Operations ---

    async def get_attendance(
        self,
        employee_id: str,
        attendance_date: date,
    ) -> Attendance | None:
        """Get attendance for a specific date."""
        return await self._get_today_attendance(employee_id, attendance_date)

    async def get_attendance_range(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> list[Attendance]:
        """Get attendance for a date range."""
        result = await self.session.execute(
            select(Attendance)
            .where(
                Attendance.tenant_id == self.tenant_id,
                Attendance.employee_id == employee_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date,
            )
            .order_by(Attendance.date)
        )
        return list(result.scalars().all())

    async def regularize_attendance(
        self,
        employee_id: str,
        attendance_date: date,
        data: AttendanceRegularize,
    ) -> Attendance:
        """Regularize attendance (correct clock in/out times)."""
        attendance = await self._get_today_attendance(employee_id, attendance_date)

        if not attendance:
            attendance = Attendance(
                tenant_id=self.tenant_id,
                employee_id=employee_id,
                date=attendance_date,
                status=AttendanceStatus.PRESENT.value,
            )
            self.session.add(attendance)

        if data.clock_in:
            attendance.clock_in = data.clock_in
        if data.clock_out:
            attendance.clock_out = data.clock_out

        attendance.is_regularized = True
        attendance.regularization_reason = data.reason

        # Recalculate work hours
        if attendance.clock_in and attendance.clock_out:
            work_seconds = (attendance.clock_out - attendance.clock_in).total_seconds()
            attendance.work_hours = round(work_seconds / 3600, 2)

        await self.session.flush()
        await self.session.refresh(attendance)
        return attendance

    async def get_daily_report(self, report_date: date) -> dict:
        """Get daily attendance report."""
        result = await self.session.execute(
            select(Attendance).where(
                Attendance.tenant_id == self.tenant_id,
                Attendance.date == report_date,
            )
        )
        records = list(result.scalars().all())

        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT.value)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT.value)
        on_leave = sum(
            1 for r in records if r.status == AttendanceStatus.ON_LEAVE.value
        )
        late = sum(1 for r in records if r.is_late)

        total = len(records) if records else 1  # Avoid division by zero

        return {
            "date": report_date,
            "total_employees": len(records),
            "present": present,
            "absent": absent,
            "on_leave": on_leave,
            "late": late,
            "attendance_percentage": round((present / total) * 100, 2),
        }

    async def _get_today_attendance(
        self,
        employee_id: str,
        attendance_date: date,
    ) -> Attendance | None:
        """Get attendance record for a specific date."""
        result = await self.session.execute(
            select(Attendance).where(
                and_(
                    Attendance.tenant_id == self.tenant_id,
                    Attendance.employee_id == employee_id,
                    Attendance.date == attendance_date,
                )
            )
        )
        return result.scalar_one_or_none()
