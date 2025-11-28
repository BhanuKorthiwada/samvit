"""Attendance models."""

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBaseModel


class AttendanceStatus(str, Enum):
    """Attendance status."""

    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"
    LATE = "late"


class ClockType(str, Enum):
    """Clock in/out type."""

    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class Shift(TenantBaseModel):
    """Work shift configuration."""

    __tablename__ = "shifts"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_night_shift: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Shift {self.name}: {self.start_time}-{self.end_time}>"


class TimeEntry(TenantBaseModel):
    """Individual clock in/out entry."""

    __tablename__ = "time_entries"

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="web")  # web, mobile, biometric
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<TimeEntry {self.entry_type} at {self.timestamp}>"


class Attendance(TenantBaseModel):
    """Daily attendance record."""

    __tablename__ = "attendance"

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    shift_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("shifts.id"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=AttendanceStatus.ABSENT.value,
    )

    # Actual times
    clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Calculated fields
    work_hours: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    break_hours: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    overtime_hours: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    early_leave_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Flags
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    is_early_leave: Mapped[bool] = mapped_column(Boolean, default=False)
    is_regularized: Mapped[bool] = mapped_column(Boolean, default=False)
    regularization_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    shift: Mapped[Shift | None] = relationship("Shift")

    def __repr__(self) -> str:
        return f"<Attendance {self.employee_id} on {self.date}: {self.status}>"
