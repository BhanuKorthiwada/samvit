"""Payroll API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError
from app.core.security import CurrentUserId
from app.core.tenancy import TenantDep
from app.modules.payroll.schemas import (
    EmployeeSalaryCreate,
    EmployeeSalaryResponse,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayrollSummary,
    PayslipResponse,
    SalaryComponentCreate,
    SalaryComponentResponse,
    SalaryComponentUpdate,
    SalaryStructureCreate,
    SalaryStructureResponse,
)
from app.modules.payroll.service import PayrollService

router = APIRouter(prefix="/payroll", tags=["Payroll"])


def get_payroll_service(
    tenant: TenantDep,
    session: AsyncSession = Depends(get_async_session),
) -> PayrollService:
    """Get payroll service dependency."""
    return PayrollService(session, tenant.tenant_id)


# --- Salary Component Routes ---


@router.post(
    "/components",
    response_model=SalaryComponentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create salary component",
)
async def create_component(
    data: SalaryComponentCreate,
    service: PayrollService = Depends(get_payroll_service),
) -> SalaryComponentResponse:
    """Create a new salary component."""
    component = await service.create_component(data)
    return SalaryComponentResponse.model_validate(component)


@router.get(
    "/components",
    response_model=list[SalaryComponentResponse],
    summary="List salary components",
)
async def list_components(
    active_only: bool = Query(default=True),
    service: PayrollService = Depends(get_payroll_service),
) -> list[SalaryComponentResponse]:
    """List all salary components."""
    components = await service.list_components(active_only)
    return [SalaryComponentResponse.model_validate(c) for c in components]


@router.get(
    "/components/{component_id}",
    response_model=SalaryComponentResponse,
    summary="Get salary component",
)
async def get_component(
    component_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> SalaryComponentResponse:
    """Get salary component by ID."""
    try:
        component = await service.get_component(component_id)
        return SalaryComponentResponse.model_validate(component)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch(
    "/components/{component_id}",
    response_model=SalaryComponentResponse,
    summary="Update salary component",
)
async def update_component(
    component_id: str,
    data: SalaryComponentUpdate,
    service: PayrollService = Depends(get_payroll_service),
) -> SalaryComponentResponse:
    """Update a salary component."""
    try:
        component = await service.update_component(component_id, data)
        return SalaryComponentResponse.model_validate(component)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --- Salary Structure Routes ---


@router.post(
    "/structures",
    response_model=SalaryStructureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create salary structure",
)
async def create_structure(
    data: SalaryStructureCreate,
    service: PayrollService = Depends(get_payroll_service),
) -> SalaryStructureResponse:
    """Create a new salary structure."""
    structure = await service.create_structure(data)
    return SalaryStructureResponse.model_validate(structure)


@router.get(
    "/structures",
    response_model=list[SalaryStructureResponse],
    summary="List salary structures",
)
async def list_structures(
    active_only: bool = Query(default=True),
    service: PayrollService = Depends(get_payroll_service),
) -> list[SalaryStructureResponse]:
    """List all salary structures."""
    structures = await service.list_structures(active_only)
    return [SalaryStructureResponse.model_validate(s) for s in structures]


@router.get(
    "/structures/{structure_id}",
    response_model=SalaryStructureResponse,
    summary="Get salary structure",
)
async def get_structure(
    structure_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> SalaryStructureResponse:
    """Get salary structure by ID."""
    try:
        structure = await service.get_structure(structure_id)
        return SalaryStructureResponse.model_validate(structure)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --- Employee Salary Routes ---


@router.post(
    "/employee-salaries",
    response_model=EmployeeSalaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign employee salary",
)
async def assign_salary(
    data: EmployeeSalaryCreate,
    service: PayrollService = Depends(get_payroll_service),
) -> EmployeeSalaryResponse:
    """Assign salary structure to an employee."""
    salary = await service.assign_salary(data)
    return EmployeeSalaryResponse.model_validate(salary)


@router.get(
    "/employee-salaries/{employee_id}",
    response_model=EmployeeSalaryResponse | None,
    summary="Get employee salary",
)
async def get_employee_salary(
    employee_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> EmployeeSalaryResponse | None:
    """Get current salary for an employee."""
    salary = await service.get_employee_salary(employee_id)
    if salary:
        return EmployeeSalaryResponse.model_validate(salary)
    return None


@router.get(
    "/employee-salaries/{employee_id}/history",
    response_model=list[EmployeeSalaryResponse],
    summary="Get employee salary history",
)
async def get_employee_salary_history(
    employee_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> list[EmployeeSalaryResponse]:
    """Get salary history for an employee."""
    salaries = await service.get_employee_salary_history(employee_id)
    return [EmployeeSalaryResponse.model_validate(s) for s in salaries]


# --- Payroll Period Routes ---


@router.post(
    "/periods",
    response_model=PayrollPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create payroll period",
)
async def create_period(
    data: PayrollPeriodCreate,
    service: PayrollService = Depends(get_payroll_service),
) -> PayrollPeriodResponse:
    """Create a new payroll period."""
    period = await service.create_period(data)
    return PayrollPeriodResponse.model_validate(period)


@router.get(
    "/periods",
    response_model=list[PayrollPeriodResponse],
    summary="List payroll periods",
)
async def list_periods(
    year: int | None = Query(default=None),
    service: PayrollService = Depends(get_payroll_service),
) -> list[PayrollPeriodResponse]:
    """List all payroll periods."""
    periods = await service.list_periods(year)
    return [PayrollPeriodResponse.model_validate(p) for p in periods]


@router.get(
    "/periods/{period_id}",
    response_model=PayrollPeriodResponse,
    summary="Get payroll period",
)
async def get_period(
    period_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> PayrollPeriodResponse:
    """Get payroll period by ID."""
    try:
        period = await service.get_period(period_id)
        return PayrollPeriodResponse.model_validate(period)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post(
    "/periods/{period_id}/generate",
    response_model=list[PayslipResponse],
    summary="Generate payslips",
)
async def generate_payslips(
    period_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> list[PayslipResponse]:
    """Generate payslips for a payroll period."""
    try:
        payslips = await service.generate_payslips(period_id)
        return [PayslipResponse.model_validate(p) for p in payslips]
    except (EntityNotFoundError, BusinessRuleViolationError) as e:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post(
    "/periods/{period_id}/approve",
    response_model=PayrollPeriodResponse,
    summary="Approve payroll",
)
async def approve_payroll(
    period_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> PayrollPeriodResponse:
    """Approve payroll for a period."""
    try:
        period = await service.approve_payroll(period_id)
        return PayrollPeriodResponse.model_validate(period)
    except (EntityNotFoundError, BusinessRuleViolationError) as e:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=e.message)


@router.get(
    "/periods/{period_id}/summary",
    response_model=PayrollSummary,
    summary="Get payroll summary",
)
async def get_payroll_summary(
    period_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> PayrollSummary:
    """Get payroll summary for a period."""
    try:
        summary = await service.get_payroll_summary(period_id)
        return PayrollSummary(**summary)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --- Payslip Routes ---


@router.get(
    "/payslips/me",
    response_model=list[PayslipResponse],
    summary="Get my payslips",
)
async def get_my_payslips(
    user_id: CurrentUserId,
    year: int | None = Query(default=None),
    service: PayrollService = Depends(get_payroll_service),
) -> list[PayslipResponse]:
    """Get current user's payslips."""
    payslips = await service.get_employee_payslips(user_id, year)
    return [PayslipResponse.model_validate(p) for p in payslips]


@router.get(
    "/payslips/{payslip_id}",
    response_model=PayslipResponse,
    summary="Get payslip",
)
async def get_payslip(
    payslip_id: str,
    service: PayrollService = Depends(get_payroll_service),
) -> PayslipResponse:
    """Get payslip by ID."""
    try:
        payslip = await service.get_payslip(payslip_id)
        return PayslipResponse.model_validate(payslip)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
