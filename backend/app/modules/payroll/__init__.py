"""Payroll module."""

from app.modules.payroll.models import (
    EmployeeSalary,
    EmployeeSalaryComponent,
    PayrollPeriod,
    PayrollStatus,
    Payslip,
    PayslipItem,
    SalaryComponent,
    SalaryStructure,
)
from app.modules.payroll.routes import router
from app.modules.payroll.schemas import (
    EmployeeSalaryCreate,
    EmployeeSalaryResponse,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayslipResponse,
    SalaryComponentCreate,
    SalaryComponentResponse,
)
from app.modules.payroll.service import PayrollService

__all__ = [
    # Models
    "EmployeeSalary",
    "EmployeeSalaryComponent",
    "Payslip",
    "PayslipItem",
    "PayrollPeriod",
    "PayrollStatus",
    "SalaryComponent",
    "SalaryStructure",
    # Schemas
    "EmployeeSalaryCreate",
    "EmployeeSalaryResponse",
    "PayrollPeriodCreate",
    "PayrollPeriodResponse",
    "PayslipResponse",
    "SalaryComponentCreate",
    "SalaryComponentResponse",
    # Service
    "PayrollService",
    # Router
    "router",
]
