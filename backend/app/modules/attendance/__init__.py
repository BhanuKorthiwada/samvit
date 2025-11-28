"""Attendance module."""

from app.modules.attendance.models import (
    Attendance,
    AttendanceStatus,
    ClockType,
    Shift,
    TimeEntry,
)
from app.modules.attendance.routes import router
from app.modules.attendance.schemas import (
    AttendanceResponse,
    AttendanceSummary,
    ClockInRequest,
    ClockOutRequest,
    ShiftCreate,
    ShiftResponse,
)
from app.modules.attendance.service import AttendanceService

__all__ = [
    # Models
    "Attendance",
    "AttendanceStatus",
    "ClockType",
    "Shift",
    "TimeEntry",
    # Schemas
    "AttendanceResponse",
    "AttendanceSummary",
    "ClockInRequest",
    "ClockOutRequest",
    "ShiftCreate",
    "ShiftResponse",
    # Service
    "AttendanceService",
    # Router
    "router",
]
