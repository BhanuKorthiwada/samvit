"""Integration tests for employee management endpoints."""

import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.employees.models import Department, Employee, Position
from app.modules.tenants.models import Tenant
from tests.conftest import get_auth_headers

pytestmark = pytest.mark.asyncio


# --- Fixtures ---


@pytest.fixture
async def test_department(
    test_session: AsyncSession, test_tenant: Tenant
) -> Department:
    """Create a test department."""
    department = Department(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        name="Engineering",
        code="ENG",
        description="Engineering department",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(department)
    await test_session.commit()
    await test_session.refresh(department)
    return department


@pytest.fixture
async def test_position(
    test_session: AsyncSession,
    test_tenant: Tenant,
    test_department: Department,
) -> Position:
    """Create a test position."""
    position = Position(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        title="Software Engineer",
        code="SWE",
        description="Software Engineer position",
        level=3,
        min_salary=50000,
        max_salary=150000,
        department_id=test_department.id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(position)
    await test_session.commit()
    await test_session.refresh(position)
    return position


@pytest.fixture
async def test_employee(
    test_session: AsyncSession,
    test_tenant: Tenant,
    test_department: Department,
    test_position: Position,
) -> Employee:
    """Create a test employee."""
    employee = Employee(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        employee_code="EMP001",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+91-9876543210",
        date_of_birth=date(1990, 1, 15),
        gender="male",
        date_of_joining=date(2024, 1, 1),
        department_id=test_department.id,
        position_id=test_position.id,
        employment_type="full_time",
        employment_status="active",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)
    return employee


# --- Department Tests ---


class TestDepartments:
    """Tests for department CRUD operations."""

    async def test_create_department_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test successful department creation."""
        data = {
            "name": "Human Resources",
            "code": "HR",
            "description": "HR department",
        }

        response = await client.post(
            "/api/v1/departments",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Human Resources"
        assert result["code"] == "HR"
        assert result["is_active"] is True

    async def test_create_department_with_parent(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
    ):
        """Test creating department with parent."""
        data = {
            "name": "Frontend Team",
            "code": "FE",
            "description": "Frontend development team",
            "parent_id": test_department.id,
        }

        response = await client.post(
            "/api/v1/departments",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 201
        result = response.json()
        assert result["parent_id"] == test_department.id

    async def test_list_departments(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
    ):
        """Test listing departments."""
        response = await client.get(
            "/api/v1/departments",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert result["total"] >= 1
        assert any(d["id"] == test_department.id for d in result["items"])

    async def test_get_department(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
    ):
        """Test getting a specific department."""
        response = await client.get(
            f"/api/v1/departments/{test_department.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == test_department.id
        assert result["name"] == test_department.name

    async def test_get_department_not_found(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test getting non-existent department."""
        response = await client.get(
            f"/api/v1/departments/{uuid.uuid4()}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 404

    async def test_update_department(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
    ):
        """Test updating a department."""
        data = {
            "name": "Updated Engineering",
            "description": "Updated description",
        }

        response = await client.patch(
            f"/api/v1/departments/{test_department.id}",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Engineering"
        assert result["description"] == "Updated description"

    async def test_delete_department(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
    ):
        """Test deleting a department."""
        response = await client.delete(
            f"/api/v1/departments/{test_department.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/departments/{test_department.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )
        assert get_response.status_code == 404


# --- Position Tests ---


class TestPositions:
    """Tests for position CRUD operations."""

    async def test_create_position_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
    ):
        """Test successful position creation."""
        data = {
            "title": "Senior Software Engineer",
            "code": "SSE",
            "description": "Senior engineer position",
            "level": 4,
            "min_salary": 80000,
            "max_salary": 200000,
            "department_id": test_department.id,
        }

        response = await client.post(
            "/api/v1/positions",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Senior Software Engineer"
        assert result["code"] == "SSE"
        assert result["level"] == 4
        assert result["is_active"] is True

    async def test_list_positions(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_position: Position,
    ):
        """Test listing positions."""
        response = await client.get(
            "/api/v1/positions",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert result["total"] >= 1

    async def test_get_position(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_position: Position,
    ):
        """Test getting a specific position."""
        response = await client.get(
            f"/api/v1/positions/{test_position.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == test_position.id
        assert result["title"] == test_position.title

    async def test_update_position(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_position: Position,
    ):
        """Test updating a position."""
        data = {
            "title": "Updated Position Title",
            "level": 5,
        }

        response = await client.patch(
            f"/api/v1/positions/{test_position.id}",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "Updated Position Title"
        assert result["level"] == 5

    async def test_delete_position(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_position: Position,
    ):
        """Test deleting a position."""
        response = await client.delete(
            f"/api/v1/positions/{test_position.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200


# --- Employee Tests ---


class TestEmployees:
    """Tests for employee CRUD operations."""

    async def test_create_employee_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_department: Department,
        test_position: Position,
    ):
        """Test successful employee creation."""
        data = {
            "employee_code": "EMP002",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+91-9876543211",
            "date_of_birth": "1992-05-20",
            "gender": "female",
            "date_of_joining": "2024-02-01",
            "department_id": test_department.id,
            "position_id": test_position.id,
            "employment_type": "full_time",
        }

        response = await client.post(
            "/api/v1/employees",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 201
        result = response.json()
        assert result["employee_code"] == "EMP002"
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Smith"
        assert result["is_active"] is True

    async def test_create_employee_duplicate_code(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test creating employee with duplicate code."""
        data = {
            "employee_code": test_employee.employee_code,  # Duplicate
            "first_name": "Another",
            "last_name": "Person",
            "email": "another@example.com",
            "date_of_joining": "2024-03-01",
        }

        response = await client.post(
            "/api/v1/employees",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 409  # Conflict

    async def test_list_employees(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test listing employees."""
        response = await client.get(
            "/api/v1/employees",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert result["total"] >= 1

    async def test_list_employees_by_department(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
        test_department: Department,
    ):
        """Test listing employees filtered by department."""
        response = await client.get(
            f"/api/v1/employees?department_id={test_department.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert all(e["department_id"] == test_department.id for e in result["items"])

    async def test_get_employee(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test getting a specific employee."""
        response = await client.get(
            f"/api/v1/employees/{test_employee.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == test_employee.id
        assert result["employee_code"] == test_employee.employee_code

    async def test_get_employee_not_found(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test getting non-existent employee."""
        response = await client.get(
            f"/api/v1/employees/{uuid.uuid4()}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 404

    async def test_update_employee(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test updating an employee."""
        data = {
            "first_name": "Jonathan",
            "phone": "+91-1234567890",
        }

        response = await client.patch(
            f"/api/v1/employees/{test_employee.id}",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["first_name"] == "Jonathan"
        assert result["phone"] == "+91-1234567890"
        assert result["last_name"] == test_employee.last_name  # Unchanged

    async def test_search_employees(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test searching employees."""
        response = await client.get(
            f"/api/v1/employees/search?q={test_employee.first_name}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 1
        assert any(e["id"] == test_employee.id for e in result)

    async def test_get_employee_stats(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test getting employee statistics."""
        response = await client.get(
            "/api/v1/employees/stats",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        # API returns 'total', 'active', 'inactive'
        assert "total" in result
        assert "active" in result
        assert "inactive" in result
        assert result["total"] >= 1

    async def test_deactivate_employee(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_employee: Employee,
    ):
        """Test deactivating an employee."""
        response = await client.post(
            f"/api/v1/employees/{test_employee.id}/deactivate",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["is_active"] is False


# --- Tenant Isolation Tests ---


class TestTenantIsolation:
    """Tests to verify tenant isolation in employee data."""

    async def test_cannot_access_other_tenant_department(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test that users cannot access departments from other tenants."""
        # Create a department in a different tenant
        other_tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Other Company",
            domain="other.samvit.bhanu.dev",
            email="other@example.com",
            status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_session.add(other_tenant)

        other_dept = Department(
            id=str(uuid.uuid4()),
            tenant_id=other_tenant.id,
            name="Other Dept",
            code="OTH",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_session.add(other_dept)
        await test_session.commit()

        # Try to access the other tenant's department
        response = await client.get(
            f"/api/v1/departments/{other_dept.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        # Should return 404 (not found) because of tenant isolation
        assert response.status_code == 404

    async def test_cannot_access_other_tenant_employee(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test that users cannot access employees from other tenants."""
        # Create an employee in a different tenant
        other_tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Another Company",
            domain="another.samvit.bhanu.dev",
            email="another@example.com",
            status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_session.add(other_tenant)

        other_employee = Employee(
            id=str(uuid.uuid4()),
            tenant_id=other_tenant.id,
            employee_code="OTHER001",
            first_name="Other",
            last_name="Employee",
            email="other.employee@example.com",
            date_of_joining=date(2024, 1, 1),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_session.add(other_employee)
        await test_session.commit()

        # Try to access the other tenant's employee
        response = await client.get(
            f"/api/v1/employees/{other_employee.id}",
            headers=get_auth_headers(test_user, test_tenant),
        )

        # Should return 404 (not found) because of tenant isolation
        assert response.status_code == 404


# --- Pagination Tests ---


class TestPagination:
    """Tests for pagination in list endpoints."""

    async def test_departments_pagination(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_session: AsyncSession,
    ):
        """Test department list pagination."""
        # Create multiple departments
        for i in range(5):
            dept = Department(
                id=str(uuid.uuid4()),
                tenant_id=test_tenant.id,
                name=f"Department {i}",
                code=f"D{i}",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            test_session.add(dept)
        await test_session.commit()

        # Test first page
        response = await client.get(
            "/api/v1/departments?page=1&page_size=2",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) <= 2
        assert result["total"] >= 5
        assert result["page"] == 1
        assert result["page_size"] == 2

    async def test_employees_pagination(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
        test_session: AsyncSession,
    ):
        """Test employee list pagination."""
        # Create multiple employees
        for i in range(5):
            emp = Employee(
                id=str(uuid.uuid4()),
                tenant_id=test_tenant.id,
                employee_code=f"PAGEMP{i}",
                first_name=f"Employee{i}",
                last_name="Test",
                email=f"emp{i}@example.com",
                date_of_joining=date(2024, 1, 1),
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            test_session.add(emp)
        await test_session.commit()

        # Test pagination
        response = await client.get(
            "/api/v1/employees?page=1&page_size=3",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) <= 3
        assert result["total"] >= 5
