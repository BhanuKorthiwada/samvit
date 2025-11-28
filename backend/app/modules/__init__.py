"""SAMVIT HRMS Modules."""

from app.modules.attendance import router as attendance_router
from app.modules.auth import router as auth_router
from app.modules.employees import (
    department_router,
    employee_router,
    position_router,
)
from app.modules.leave import router as leave_router
from app.modules.payroll import router as payroll_router
from app.modules.tenants import router as tenants_router

__all__ = [
    "attendance_router",
    "auth_router",
    "department_router",
    "employee_router",
    "leave_router",
    "payroll_router",
    "position_router",
    "tenants_router",
]