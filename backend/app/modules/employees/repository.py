"""Employee repository."""

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.modules.employees.models import Department, Employee, Position
from app.shared.repository import TenantRepository


class DepartmentRepository(TenantRepository[Department]):
    """Repository for department operations."""

    model = Department

    async def get_by_code(self, code: str) -> Department | None:
        """Get department by code."""
        result = await self.session.execute(
            self._apply_tenant_filter(select(Department).where(Department.code == code))
        )
        return result.scalar_one_or_none()

    async def get_with_employees(self, department_id: str) -> Department | None:
        """Get department with employees loaded."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Department)
                .options(selectinload(Department.employees))
                .where(Department.id == department_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_root_departments(self) -> list[Department]:
        """Get top-level departments (no parent)."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Department).where(Department.parent_id.is_(None))
            )
        )
        return list(result.scalars().all())


class PositionRepository(TenantRepository[Position]):
    """Repository for position operations."""

    model = Position

    async def get_by_code(self, code: str) -> Position | None:
        """Get position by code."""
        result = await self.session.execute(
            self._apply_tenant_filter(select(Position).where(Position.code == code))
        )
        return result.scalar_one_or_none()

    async def get_by_department(self, department_id: str) -> list[Position]:
        """Get positions in a department."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Position).where(Position.department_id == department_id)
            )
        )
        return list(result.scalars().all())


class EmployeeRepository(TenantRepository[Employee]):
    """Repository for employee operations."""

    model = Employee

    async def get_by_code(self, employee_code: str) -> Employee | None:
        """Get employee by employee code."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Employee).where(Employee.employee_code == employee_code)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Employee | None:
        """Get employee by email."""
        result = await self.session.execute(
            self._apply_tenant_filter(select(Employee).where(Employee.email == email))
        )
        return result.scalar_one_or_none()

    async def get_with_relations(self, employee_id: str) -> Employee | None:
        """Get employee with department and position loaded."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Employee)
                .options(
                    selectinload(Employee.department),
                    selectinload(Employee.position),
                    selectinload(Employee.reporting_manager),
                )
                .where(Employee.id == employee_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_department(
        self,
        department_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Employee]:
        """Get employees in a department."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Employee)
                .where(Employee.department_id == department_id)
                .offset(offset)
                .limit(limit)
            )
        )
        return list(result.scalars().all())

    async def get_direct_reports(self, manager_id: str) -> list[Employee]:
        """Get employees reporting to a manager."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Employee).where(Employee.reporting_manager_id == manager_id)
            )
        )
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Employee]:
        """Search employees by name, email, or code."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(Employee)
                .where(
                    (Employee.first_name.ilike(search_pattern))
                    | (Employee.last_name.ilike(search_pattern))
                    | (Employee.email.ilike(search_pattern))
                    | (Employee.employee_code.ilike(search_pattern))
                )
                .offset(offset)
                .limit(limit)
            )
        )
        return list(result.scalars().all())

    async def get_active_count(self) -> int:
        """Get count of active employees."""
        result = await self.session.execute(
            self._apply_tenant_filter(
                select(func.count())
                .select_from(Employee)
                .where(Employee.is_active.is_(True))
            )
        )
        return result.scalar_one()
