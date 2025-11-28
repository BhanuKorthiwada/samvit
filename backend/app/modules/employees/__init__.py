"""Employees module."""

from app.modules.employees.models import (
    Department,
    Employee,
    EmploymentStatus,
    EmploymentType,
    Gender,
    MaritalStatus,
    Position,
)
from app.modules.employees.routes import department_router, employee_router, position_router
from app.modules.employees.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)
from app.modules.employees.service import EmployeeService

__all__ = [
    # Models
    "Department",
    "Position",
    "Employee",
    "EmploymentType",
    "EmploymentStatus",
    "Gender",
    "MaritalStatus",
    # Schemas
    "DepartmentCreate",
    "DepartmentResponse",
    "DepartmentUpdate",
    "PositionCreate",
    "PositionResponse",
    "PositionUpdate",
    "EmployeeCreate",
    "EmployeeResponse",
    "EmployeeUpdate",
    # Service
    "EmployeeService",
    # Routers
    "department_router",
    "position_router",
    "employee_router",
]
