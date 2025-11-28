"""Employee API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import TenantDep
from app.core.exceptions import EntityAlreadyExistsError, EntityNotFoundError
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

# --- Routers ---

department_router = APIRouter(prefix="/departments", tags=["Departments"])
position_router = APIRouter(prefix="/positions", tags=["Positions"])
employee_router = APIRouter(prefix="/employees", tags=["Employees"])


def get_employee_service(
    tenant: TenantDep,
    session: AsyncSession = Depends(get_async_session),
) -> EmployeeService:
    """Get employee service dependency."""
    return EmployeeService(session, tenant.tenant_id)


# --- Department Routes ---


@department_router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
async def create_department(
    data: DepartmentCreate,
    service: EmployeeService = Depends(get_employee_service),
) -> DepartmentResponse:
    """Create a new department."""
    try:
        department = await service.create_department(data)
        return DepartmentResponse.model_validate(department)
    except EntityAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


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
    try:
        department = await service.get_department(department_id)
        return DepartmentResponse.model_validate(department)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@department_router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update department",
)
async def update_department(
    department_id: str,
    data: DepartmentUpdate,
    service: EmployeeService = Depends(get_employee_service),
) -> DepartmentResponse:
    """Update a department."""
    try:
        department = await service.update_department(department_id, data)
        return DepartmentResponse.model_validate(department)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


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
    try:
        await service.delete_department(department_id)
        return SuccessResponse(message="Department deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --- Position Routes ---


@position_router.post(
    "",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create position",
)
async def create_position(
    data: PositionCreate,
    service: EmployeeService = Depends(get_employee_service),
) -> PositionResponse:
    """Create a new position."""
    try:
        position = await service.create_position(data)
        return PositionResponse.model_validate(position)
    except EntityAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


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
    try:
        position = await service.get_position(position_id)
        return PositionResponse.model_validate(position)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@position_router.patch(
    "/{position_id}",
    response_model=PositionResponse,
    summary="Update position",
)
async def update_position(
    position_id: str,
    data: PositionUpdate,
    service: EmployeeService = Depends(get_employee_service),
) -> PositionResponse:
    """Update a position."""
    try:
        position = await service.update_position(position_id, data)
        return PositionResponse.model_validate(position)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


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
    try:
        await service.delete_position(position_id)
        return SuccessResponse(message="Position deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --- Employee Routes ---


@employee_router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
)
async def create_employee(
    data: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Create a new employee."""
    try:
        employee = await service.create_employee(data)
        return EmployeeResponse.model_validate(employee)
    except EntityAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


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
    try:
        employee = await service.get_employee_with_details(employee_id)
        return EmployeeResponse.model_validate(employee)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@employee_router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee",
)
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Update an employee."""
    try:
        employee = await service.update_employee(employee_id, data)
        return EmployeeResponse.model_validate(employee)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


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
    try:
        employee = await service.deactivate_employee(employee_id)
        return EmployeeResponse.model_validate(employee)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
