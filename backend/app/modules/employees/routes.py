"""Employee API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.tenancy import TenantDep
from app.modules.employees.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentSummary,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeSummary,
    EmployeeUpdate,
    PositionCreate,
    PositionResponse,
    PositionSummary,
    PositionUpdate,
)
from app.modules.employees.service import EmployeeService
from app.shared.schemas import PaginatedResponse, SuccessResponse

department_router = APIRouter(prefix="/departments", tags=["Departments"])
position_router = APIRouter(prefix="/positions", tags=["Positions"])
employee_router = APIRouter(prefix="/employees", tags=["Employees"])


def get_employee_service(
    tenant: TenantDep,
    session: DbSession,
) -> EmployeeService:
    """Get employee service dependency."""
    return EmployeeService(session, tenant.tenant_id)


@department_router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
async def create_department(
    data: DepartmentCreate,
    service: EmployeeService = Depends(get_employee_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> DepartmentResponse:
    """Create a new department."""
    department = await service.create_department(data)
    return DepartmentResponse.model_validate(department)


@department_router.get(
    "",
    response_model=PaginatedResponse[DepartmentSummary],
    summary="List departments",
)
async def list_departments(
    page: int = 1,
    page_size: int = 20,
    service: EmployeeService = Depends(get_employee_service),
) -> PaginatedResponse[DepartmentSummary]:
    """List all departments."""
    offset = (page - 1) * page_size
    departments, total = await service.list_departments(offset=offset, limit=page_size)
    items = [DepartmentSummary.model_validate(d) for d in departments]
    return PaginatedResponse.create(items, total, page, page_size)


@department_router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department",
)
async def get_department(
    department_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> DepartmentResponse:
    """Get department by ID."""
    department = await service.get_department(department_id)
    return DepartmentResponse.model_validate(department)


@department_router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update department",
)
async def update_department(
    department_id: str,
    data: DepartmentUpdate,
    service: EmployeeService = Depends(get_employee_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,  # 30 per minute
) -> DepartmentResponse:
    """Update a department."""
    department = await service.update_department(department_id, data)
    return DepartmentResponse.model_validate(department)


@department_router.delete(
    "/{department_id}",
    response_model=SuccessResponse,
    summary="Delete department",
)
async def delete_department(
    department_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> SuccessResponse:
    """Delete a department."""
    await service.delete_department(department_id)
    return SuccessResponse(message="Department deleted successfully")


@position_router.post(
    "",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create position",
)
async def create_position(
    data: PositionCreate,
    service: EmployeeService = Depends(get_employee_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> PositionResponse:
    """Create a new position."""
    position = await service.create_position(data)
    return PositionResponse.model_validate(position)


@position_router.get(
    "",
    response_model=PaginatedResponse[PositionSummary],
    summary="List positions",
)
async def list_positions(
    page: int = 1,
    page_size: int = 20,
    service: EmployeeService = Depends(get_employee_service),
) -> PaginatedResponse[PositionSummary]:
    """List all positions."""
    offset = (page - 1) * page_size
    positions, total = await service.list_positions(offset=offset, limit=page_size)
    items = [PositionSummary.model_validate(p) for p in positions]
    return PaginatedResponse.create(items, total, page, page_size)


@position_router.get(
    "/{position_id}",
    response_model=PositionResponse,
    summary="Get position",
)
async def get_position(
    position_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> PositionResponse:
    """Get position by ID."""
    position = await service.get_position(position_id)
    return PositionResponse.model_validate(position)


@position_router.patch(
    "/{position_id}",
    response_model=PositionResponse,
    summary="Update position",
)
async def update_position(
    position_id: str,
    data: PositionUpdate,
    service: EmployeeService = Depends(get_employee_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,  # 30 per minute
) -> PositionResponse:
    """Update a position."""
    position = await service.update_position(position_id, data)
    return PositionResponse.model_validate(position)


@position_router.delete(
    "/{position_id}",
    response_model=SuccessResponse,
    summary="Delete position",
)
async def delete_position(
    position_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> SuccessResponse:
    """Delete a position."""
    await service.delete_position(position_id)
    return SuccessResponse(message="Position deleted successfully")


@employee_router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
)
async def create_employee(
    data: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,  # 20 per minute
) -> EmployeeResponse:
    """Create a new employee."""
    employee = await service.create_employee(data)
    return EmployeeResponse.model_validate(employee)


@employee_router.get(
    "",
    response_model=PaginatedResponse[EmployeeSummary],
    summary="List employees",
)
async def list_employees(
    page: int = 1,
    page_size: int = 20,
    department_id: str | None = Query(default=None),
    service: EmployeeService = Depends(get_employee_service),
) -> PaginatedResponse[EmployeeSummary]:
    """List employees with optional filters."""
    offset = (page - 1) * page_size
    employees, total = await service.list_employees(
        offset=offset,
        limit=page_size,
        department_id=department_id,
    )
    items = [EmployeeSummary.model_validate(e) for e in employees]
    return PaginatedResponse.create(items, total, page, page_size)


@employee_router.get(
    "/search",
    response_model=list[EmployeeSummary],
    summary="Search employees",
)
async def search_employees(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, le=50),
    service: EmployeeService = Depends(get_employee_service),
) -> list[EmployeeSummary]:
    """Search employees by name, email, or code."""
    employees = await service.search_employees(q, limit=limit)
    return [EmployeeSummary.model_validate(e) for e in employees]


@employee_router.get(
    "/stats",
    summary="Employee statistics",
)
async def get_employee_stats(
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    """Get employee statistics."""
    return await service.get_employee_stats()


@employee_router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee",
)
async def get_employee(
    employee_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Get employee by ID."""
    employee = await service.get_employee_with_details(employee_id)
    return EmployeeResponse.model_validate(employee)


@employee_router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee",
)
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,  # 30 per minute
) -> EmployeeResponse:
    """Update an employee."""
    employee = await service.update_employee(employee_id, data)
    return EmployeeResponse.model_validate(employee)


@employee_router.get(
    "/{employee_id}/direct-reports",
    response_model=list[EmployeeSummary],
    summary="Get direct reports",
)
async def get_direct_reports(
    employee_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> list[EmployeeSummary]:
    """Get employees reporting to this employee."""
    employees = await service.get_direct_reports(employee_id)
    return [EmployeeSummary.model_validate(e) for e in employees]


@employee_router.post(
    "/{employee_id}/deactivate",
    response_model=EmployeeResponse,
    summary="Deactivate employee",
)
async def deactivate_employee(
    employee_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Deactivate an employee."""
    employee = await service.deactivate_employee(employee_id)
    return EmployeeResponse.model_validate(employee)
