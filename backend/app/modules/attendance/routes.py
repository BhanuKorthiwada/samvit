"""Attendance API routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.security import CurrentUserId
from app.core.tenancy import TenantDep
from app.modules.attendance.schemas import (
    AttendanceRegularize,
    AttendanceResponse,
    ClockInRequest,
    ClockOutRequest,
    DailyAttendanceReport,
    ShiftCreate,
    ShiftResponse,
    ShiftUpdate,
    TimeEntryResponse,
)
from app.modules.attendance.service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def get_attendance_service(
    tenant: TenantDep,
    session: DbSession,
) -> AttendanceService:
    """Get attendance service dependency."""
    return AttendanceService(session, tenant.tenant_id)


@router.post(
    "/shifts",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shift",
)
async def create_shift(
    data: ShiftCreate,
    service: AttendanceService = Depends(get_attendance_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> ShiftResponse:
    """Create a new shift."""
    shift = await service.create_shift(data)
    return ShiftResponse.model_validate(shift)


@router.get(
    "/shifts",
    response_model=list[ShiftResponse],
    summary="List shifts",
)
async def list_shifts(
    service: AttendanceService = Depends(get_attendance_service),
) -> list[ShiftResponse]:
    """List all shifts."""
    shifts = await service.list_shifts()
    return [ShiftResponse.model_validate(s) for s in shifts]


@router.get(
    "/shifts/{shift_id}",
    response_model=ShiftResponse,
    summary="Get shift",
)
async def get_shift(
    shift_id: str,
    service: AttendanceService = Depends(get_attendance_service),
) -> ShiftResponse:
    """Get shift by ID."""
    shift = await service.get_shift(shift_id)
    return ShiftResponse.model_validate(shift)


@router.patch(
    "/shifts/{shift_id}",
    response_model=ShiftResponse,
    summary="Update shift",
)
async def update_shift(
    shift_id: str,
    data: ShiftUpdate,
    service: AttendanceService = Depends(get_attendance_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> ShiftResponse:
    """Update a shift."""
    shift = await service.update_shift(shift_id, data)
    return ShiftResponse.model_validate(shift)


@router.post(
    "/clock-in",
    response_model=TimeEntryResponse,
    summary="Clock in",
)
async def clock_in(
    request: Request,
    data: ClockInRequest,
    user_id: CurrentUserId,
    service: AttendanceService = Depends(get_attendance_service),
    _: Annotated[
        None, Depends(rate_limit(10, 60))
    ] = None,  # 10 per minute - prevent spam
) -> TimeEntryResponse:
    """Record clock in."""
    ip_address = request.client.host if request.client else None
    entry = await service.clock_in(data, user_id, ip_address)
    return TimeEntryResponse.model_validate(entry)


@router.post(
    "/clock-out",
    response_model=TimeEntryResponse,
    summary="Clock out",
)
async def clock_out(
    request: Request,
    data: ClockOutRequest,
    user_id: CurrentUserId,
    service: AttendanceService = Depends(get_attendance_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> TimeEntryResponse:
    """Record clock out."""
    ip_address = request.client.host if request.client else None
    entry = await service.clock_out(data, user_id, ip_address)
    return TimeEntryResponse.model_validate(entry)


@router.get(
    "/my-attendance",
    response_model=list[AttendanceResponse],
    summary="Get my attendance",
)
async def get_my_attendance(
    user_id: CurrentUserId,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: AttendanceService = Depends(get_attendance_service),
) -> list[AttendanceResponse]:
    """Get current user's attendance for a date range."""
    records = await service.get_attendance_range(user_id, start_date, end_date)
    return [AttendanceResponse.model_validate(r) for r in records]


@router.get(
    "/employee/{employee_id}",
    response_model=list[AttendanceResponse],
    summary="Get employee attendance",
)
async def get_employee_attendance(
    employee_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: AttendanceService = Depends(get_attendance_service),
) -> list[AttendanceResponse]:
    """Get an employee's attendance for a date range."""
    records = await service.get_attendance_range(employee_id, start_date, end_date)
    return [AttendanceResponse.model_validate(r) for r in records]


@router.post(
    "/regularize/{employee_id}/{attendance_date}",
    response_model=AttendanceResponse,
    summary="Regularize attendance",
)
async def regularize_attendance(
    employee_id: str,
    attendance_date: date,
    data: AttendanceRegularize,
    service: AttendanceService = Depends(get_attendance_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> AttendanceResponse:
    """Regularize attendance (correct times with reason)."""
    attendance = await service.regularize_attendance(employee_id, attendance_date, data)
    return AttendanceResponse.model_validate(attendance)


@router.get(
    "/report/daily",
    response_model=DailyAttendanceReport,
    summary="Daily attendance report",
)
async def get_daily_report(
    report_date: date = Query(default_factory=date.today),
    service: AttendanceService = Depends(get_attendance_service),
) -> DailyAttendanceReport:
    """Get daily attendance report."""
    report = await service.get_daily_report(report_date)
    return DailyAttendanceReport(**report)
