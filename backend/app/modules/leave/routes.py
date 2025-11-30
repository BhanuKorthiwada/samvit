"""Leave management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.security import CurrentUserId
from app.core.tenancy import TenantDep
from app.modules.leave.schemas import (
    HolidayCreate,
    HolidayResponse,
    LeaveApproval,
    LeaveBalanceResponse,
    LeavePolicyCreate,
    LeavePolicyResponse,
    LeavePolicyUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveStatus,
)
from app.modules.leave.service import LeaveService

router = APIRouter(prefix="/leave", tags=["Leave Management"])


def get_leave_service(
    tenant: TenantDep,
    session: DbSession,
) -> LeaveService:
    """Get leave service dependency."""
    return LeaveService(session, tenant.tenant_id)


# --- Leave Policy Routes ---


@router.post(
    "/policies",
    response_model=LeavePolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create leave policy",
)
async def create_policy(
    data: LeavePolicyCreate,
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> LeavePolicyResponse:
    """Create a new leave policy."""
    policy = await service.create_policy(data)
    return LeavePolicyResponse.model_validate(policy)


@router.get(
    "/policies",
    response_model=list[LeavePolicyResponse],
    summary="List leave policies",
)
async def list_policies(
    active_only: bool = Query(default=True),
    service: LeaveService = Depends(get_leave_service),
) -> list[LeavePolicyResponse]:
    """List all leave policies."""
    policies = await service.list_policies(active_only)
    return [LeavePolicyResponse.model_validate(p) for p in policies]


@router.get(
    "/policies/{policy_id}",
    response_model=LeavePolicyResponse,
    summary="Get leave policy",
)
async def get_policy(
    policy_id: str,
    service: LeaveService = Depends(get_leave_service),
) -> LeavePolicyResponse:
    """Get leave policy by ID."""
    policy = await service.get_policy(policy_id)
    return LeavePolicyResponse.model_validate(policy)


@router.patch(
    "/policies/{policy_id}",
    response_model=LeavePolicyResponse,
    summary="Update leave policy",
)
async def update_policy(
    policy_id: str,
    data: LeavePolicyUpdate,
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> LeavePolicyResponse:
    """Update a leave policy."""
    policy = await service.update_policy(policy_id, data)
    return LeavePolicyResponse.model_validate(policy)


# --- Leave Balance Routes ---


@router.get(
    "/balances/me",
    response_model=list[LeaveBalanceResponse],
    summary="Get my leave balances",
)
async def get_my_balances(
    user_id: CurrentUserId,
    year: int | None = Query(default=None),
    service: LeaveService = Depends(get_leave_service),
) -> list[LeaveBalanceResponse]:
    """Get current user's leave balances."""
    balances = await service.get_employee_balances(user_id, year)
    return [LeaveBalanceResponse.model_validate(b) for b in balances]


@router.get(
    "/balances/{employee_id}",
    response_model=list[LeaveBalanceResponse],
    summary="Get employee leave balances",
)
async def get_employee_balances(
    employee_id: str,
    year: int | None = Query(default=None),
    service: LeaveService = Depends(get_leave_service),
) -> list[LeaveBalanceResponse]:
    """Get an employee's leave balances."""
    balances = await service.get_employee_balances(employee_id, year)
    return [LeaveBalanceResponse.model_validate(b) for b in balances]


@router.post(
    "/balances/{employee_id}/initialize",
    response_model=list[LeaveBalanceResponse],
    summary="Initialize employee balances",
)
async def initialize_balances(
    employee_id: str,
    year: int | None = Query(default=None),
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> list[LeaveBalanceResponse]:
    """Initialize leave balances for an employee."""
    balances = await service.initialize_balances(employee_id, year)
    return [LeaveBalanceResponse.model_validate(b) for b in balances]


# --- Leave Request Routes ---


@router.post(
    "/requests",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for leave",
)
async def create_request(
    data: LeaveRequestCreate,
    user_id: CurrentUserId,
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> LeaveRequestResponse:
    """Create a new leave request."""
    request = await service.create_request(user_id, data)
    return LeaveRequestResponse.model_validate(request)


@router.get(
    "/requests/me",
    response_model=list[LeaveRequestResponse],
    summary="Get my leave requests",
)
async def get_my_requests(
    user_id: CurrentUserId,
    leave_status: LeaveStatus | None = Query(default=None, alias="status"),
    year: int | None = Query(default=None),
    service: LeaveService = Depends(get_leave_service),
) -> list[LeaveRequestResponse]:
    """Get current user's leave requests."""
    requests = await service.get_employee_requests(user_id, leave_status, year)
    return [LeaveRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/requests/pending",
    response_model=list[LeaveRequestResponse],
    summary="Get pending approvals",
)
async def get_pending_approvals(
    user_id: CurrentUserId,
    service: LeaveService = Depends(get_leave_service),
) -> list[LeaveRequestResponse]:
    """Get pending leave requests for approval."""
    requests = await service.get_pending_approvals(user_id)
    return [LeaveRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/requests/{request_id}",
    response_model=LeaveRequestResponse,
    summary="Get leave request",
)
async def get_request(
    request_id: str,
    service: LeaveService = Depends(get_leave_service),
) -> LeaveRequestResponse:
    """Get leave request by ID."""
    request = await service.get_request(request_id)
    return LeaveRequestResponse.model_validate(request)


@router.post(
    "/requests/{request_id}/approve",
    response_model=LeaveRequestResponse,
    summary="Approve/Reject leave",
)
async def process_approval(
    request_id: str,
    data: LeaveApproval,
    user_id: CurrentUserId,
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,  # 30 per minute
) -> LeaveRequestResponse:
    """Approve or reject a leave request."""
    request = await service.process_approval(request_id, user_id, data)
    return LeaveRequestResponse.model_validate(request)


@router.post(
    "/requests/{request_id}/cancel",
    response_model=LeaveRequestResponse,
    summary="Cancel leave request",
)
async def cancel_request(
    request_id: str,
    user_id: CurrentUserId,
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> LeaveRequestResponse:
    """Cancel a leave request."""
    request = await service.cancel_request(request_id, user_id)
    return LeaveRequestResponse.model_validate(request)


# --- Holiday Routes ---


@router.post(
    "/holidays",
    response_model=HolidayResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create holiday",
)
async def create_holiday(
    data: HolidayCreate,
    service: LeaveService = Depends(get_leave_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> HolidayResponse:
    """Create a new holiday."""
    holiday = await service.create_holiday(data)
    return HolidayResponse.model_validate(holiday)


@router.get(
    "/holidays",
    response_model=list[HolidayResponse],
    summary="List holidays",
)
async def list_holidays(
    year: int | None = Query(default=None),
    service: LeaveService = Depends(get_leave_service),
) -> list[HolidayResponse]:
    """List holidays for a year."""
    holidays = await service.list_holidays(year)
    return [HolidayResponse.model_validate(h) for h in holidays]
