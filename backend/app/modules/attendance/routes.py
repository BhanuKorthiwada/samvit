"""Attendance API routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import CurrentUserId, TenantDep
from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError
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
from app.shared.schemas import SuccessResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def get_attendance_service(
    tenant: TenantDep,
    session: AsyncSession = Depends(get_async_session),
) -> AttendanceService:
    """Get attendance service dependency."""
    return AttendanceService(session, tenant.tenant_id)


# --- Shift Routes ---


@router.post(
    "/shifts",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shift",
)
async def create_shift(
    data: ShiftCreate,
    service: AttendanceService = Depends(get_attendance_service),
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
    try:
        shift = await service.get_shift(shift_id)
        return ShiftResponse.model_validate(shift)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch(
    "/shifts/{shift_id}",
    response_model=ShiftResponse,
    summary="Update shift",
)
async def update_shift(
    shift_id: str,
    data: ShiftUpdate,
    service: AttendanceService = Depends(get_attendance_service),
) -> ShiftResponse:
    """Update a shift."""
    try:
        shift = await service.update_shift(shift_id, data)
        return ShiftResponse.model_validate(shift)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --- Clock In/Out Routes ---


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
) -> TimeEntryResponse:
    """Record clock in."""
    try:
        ip_address = request.client.host if request.client else None
        entry = await service.clock_in(data, user_id, ip_address)
        return TimeEntryResponse.model_validate(entry)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


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
) -> TimeEntryResponse:
    """Record clock out."""
    try:
        ip_address = request.client.host if request.client else None
        entry = await service.clock_out(data, user_id, ip_address)
        return TimeEntryResponse.model_validate(entry)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


# --- Attendance Routes ---


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
