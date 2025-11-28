"""Attendance schemas."""

from datetime import date, datetime, time
from enum import Enum

from pydantic import Field

from app.shared.schemas import BaseSchema, TenantEntitySchema


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
    """Clock type."""

    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


# --- Shift Schemas ---


class ShiftCreate(BaseSchema):
    """Create shift schema."""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    start_time: time
    end_time: time
    break_duration_minutes: int = Field(default=60, ge=0)
    grace_period_minutes: int = Field(default=15, ge=0)
    is_night_shift: bool = False
    is_default: bool = False


class ShiftUpdate(BaseSchema):
    """Update shift schema."""

    name: str | None = Field(default=None, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    break_duration_minutes: int | None = Field(default=None, ge=0)
    grace_period_minutes: int | None = Field(default=None, ge=0)
    is_night_shift: bool | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class ShiftResponse(TenantEntitySchema):
    """Shift response schema."""

    name: str
    code: str
    start_time: time
    end_time: time
    break_duration_minutes: int
    grace_period_minutes: int
    is_night_shift: bool
    is_default: bool
    is_active: bool


# --- Time Entry Schemas ---


class ClockInRequest(BaseSchema):
    """Clock in request."""

    employee_id: str | None = None  # Optional, uses current user if not provided
    location: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class ClockOutRequest(BaseSchema):
    """Clock out request."""

    employee_id: str | None = None
    location: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class TimeEntryResponse(TenantEntitySchema):
    """Time entry response."""

    employee_id: str
    entry_type: ClockType
    timestamp: datetime
    source: str
    location: str | None
    notes: str | None


# --- Attendance Schemas ---


class AttendanceCreate(BaseSchema):
    """Create/update attendance record."""

    employee_id: str
    date: date
    shift_id: str | None = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    clock_in: datetime | None = None
    clock_out: datetime | None = None
    notes: str | None = None


class AttendanceRegularize(BaseSchema):
    """Regularize attendance request."""

    clock_in: datetime | None = None
    clock_out: datetime | None = None
    reason: str = Field(..., min_length=10, max_length=500)


class AttendanceResponse(TenantEntitySchema):
    """Attendance response schema."""

    employee_id: str
    date: date
    shift_id: str | None
    status: AttendanceStatus
    clock_in: datetime | None
    clock_out: datetime | None
    work_hours: float | None
    break_hours: float | None
    overtime_hours: float | None
    late_minutes: int
    early_leave_minutes: int
    is_late: bool
    is_early_leave: bool
    is_regularized: bool
    regularization_reason: str | None


class AttendanceSummary(BaseSchema):
    """Attendance summary for a period."""

    employee_id: str
    period_start: date
    period_end: date
    total_days: int
    present_days: int
    absent_days: int
    half_days: int
    leave_days: int
    late_count: int
    early_leave_count: int
    total_work_hours: float
    total_overtime_hours: float


class DailyAttendanceReport(BaseSchema):
    """Daily attendance report."""

    date: date
    total_employees: int
    present: int
    absent: int
    on_leave: int
    late: int
    attendance_percentage: float
