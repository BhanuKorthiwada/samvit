"""Employee service - business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from app.modules.employees.models import Department, Employee, Position
from app.modules.employees.repository import (
    DepartmentRepository,
    EmployeeRepository,
    PositionRepository,
)
from app.modules.employees.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeUpdate,
    PositionCreate,
    PositionUpdate,
)


class EmployeeService:
    """Service for employee operations."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.employee_repo = EmployeeRepository(session, tenant_id)
        self.department_repo = DepartmentRepository(session, tenant_id)
        self.position_repo = PositionRepository(session, tenant_id)

    # --- Department Operations ---

    async def create_department(self, data: DepartmentCreate) -> Department:
        """Create a new department."""
        existing = await self.department_repo.get_by_code(data.code)
        if existing:
            raise EntityAlreadyExistsError("Department", data.code)

        department = Department(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            parent_id=data.parent_id,
            head_id=data.head_id,
        )
        return await self.department_repo.create(department)

    async def get_department(self, department_id: str) -> Department:
        """Get department by ID."""
        return await self.department_repo.get_by_id_or_raise(department_id)

    async def update_department(
        self,
        department_id: str,
        data: DepartmentUpdate,
    ) -> Department:
        """Update department."""
        department = await self.get_department(department_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(department, field, value)
        return await self.department_repo.update(department)

    async def list_departments(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Department], int]:
        """List all departments."""
        departments = await self.department_repo.get_all(offset=offset, limit=limit)
        total = await self.department_repo.count()
        return departments, total

    async def delete_department(self, department_id: str) -> None:
        """Delete a department."""
        department = await self.get_department(department_id)
        await self.department_repo.delete(department)

    # --- Position Operations ---

    async def create_position(self, data: PositionCreate) -> Position:
        """Create a new position."""
        existing = await self.position_repo.get_by_code(data.code)
        if existing:
            raise EntityAlreadyExistsError("Position", data.code)

        position = Position(
            tenant_id=self.tenant_id,
            title=data.title,
            code=data.code,
            description=data.description,
            level=data.level,
            min_salary=data.min_salary,
            max_salary=data.max_salary,
            department_id=data.department_id,
        )
        return await self.position_repo.create(position)

    async def get_position(self, position_id: str) -> Position:
        """Get position by ID."""
        return await self.position_repo.get_by_id_or_raise(position_id)

    async def update_position(
        self,
        position_id: str,
        data: PositionUpdate,
    ) -> Position:
        """Update position."""
        position = await self.get_position(position_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(position, field, value)
        return await self.position_repo.update(position)

    async def list_positions(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Position], int]:
        """List all positions."""
        positions = await self.position_repo.get_all(offset=offset, limit=limit)
        total = await self.position_repo.count()
        return positions, total

    async def delete_position(self, position_id: str) -> None:
        """Delete a position."""
        position = await self.get_position(position_id)
        await self.position_repo.delete(position)

    # --- Employee Operations ---

    async def create_employee(self, data: EmployeeCreate) -> Employee:
        """Create a new employee."""
        # Check employee code uniqueness
        existing = await self.employee_repo.get_by_code(data.employee_code)
        if existing:
            raise EntityAlreadyExistsError("Employee", data.employee_code)

        # Check email uniqueness
        existing_email = await self.employee_repo.get_by_email(data.email)
        if existing_email:
            raise EntityAlreadyExistsError("Employee", data.email)

        employee = Employee(
            tenant_id=self.tenant_id,
            employee_code=data.employee_code,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            personal_email=data.personal_email,
            date_of_birth=data.date_of_birth,
            gender=data.gender.value if data.gender else None,
            marital_status=data.marital_status.value if data.marital_status else None,
            nationality=data.nationality,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            employment_type=data.employment_type.value,
            date_of_joining=data.date_of_joining,
            probation_end_date=data.probation_end_date,
            department_id=data.department_id,
            position_id=data.position_id,
            reporting_manager_id=data.reporting_manager_id,
            pan_number=data.pan_number,
            aadhaar_number=data.aadhaar_number,
            bank_name=data.bank_name,
            bank_account_number=data.bank_account_number,
            ifsc_code=data.ifsc_code,
        )
        return await self.employee_repo.create(employee)

    async def get_employee(self, employee_id: str) -> Employee:
        """Get employee by ID."""
        return await self.employee_repo.get_by_id_or_raise(employee_id)

    async def get_employee_with_details(self, employee_id: str) -> Employee:
        """Get employee with department, position, and manager."""
        employee = await self.employee_repo.get_with_relations(employee_id)
        if not employee:
            raise EntityNotFoundError("Employee", employee_id)
        return employee

    async def update_employee(
        self,
        employee_id: str,
        data: EmployeeUpdate,
    ) -> Employee:
        """Update employee."""
        employee = await self.get_employee(employee_id)
        update_data = data.model_dump(exclude_unset=True)

        # Handle enum conversions
        if "gender" in update_data and update_data["gender"]:
            update_data["gender"] = update_data["gender"].value
        if "marital_status" in update_data and update_data["marital_status"]:
            update_data["marital_status"] = update_data["marital_status"].value
        if "employment_type" in update_data and update_data["employment_type"]:
            update_data["employment_type"] = update_data["employment_type"].value
        if "employment_status" in update_data and update_data["employment_status"]:
            update_data["employment_status"] = update_data["employment_status"].value

        for field, value in update_data.items():
            setattr(employee, field, value)

        return await self.employee_repo.update(employee)

    async def list_employees(
        self,
        offset: int = 0,
        limit: int = 100,
        department_id: str | None = None,
    ) -> tuple[list[Employee], int]:
        """List employees with optional department filter."""
        if department_id:
            employees = await self.employee_repo.get_by_department(
                department_id,
                offset=offset,
                limit=limit,
            )
            total = await self.employee_repo.count({"department_id": department_id})
        else:
            employees = await self.employee_repo.get_all(offset=offset, limit=limit)
            total = await self.employee_repo.count()
        return employees, total

    async def search_employees(
        self,
        query: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Employee]:
        """Search employees."""
        return await self.employee_repo.search(query, offset, limit)

    async def get_direct_reports(self, manager_id: str) -> list[Employee]:
        """Get employees reporting to a manager."""
        return await self.employee_repo.get_direct_reports(manager_id)

    async def deactivate_employee(self, employee_id: str) -> Employee:
        """Deactivate an employee."""
        employee = await self.get_employee(employee_id)
        employee.is_active = False
        return await self.employee_repo.update(employee)

    async def get_employee_stats(self) -> dict:
        """Get employee statistics."""
        total = await self.employee_repo.count()
        active = await self.employee_repo.get_active_count()
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
        }
