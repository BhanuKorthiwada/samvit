"""Integration tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.modules.auth.models import User
from app.modules.tenants.models import Tenant
from tests.conftest import get_auth_headers, get_tenant_headers

pytestmark = pytest.mark.asyncio


class TestCompanyRegistration:
    """Tests for company (tenant + admin) registration."""

    async def test_register_company_success(self, client: AsyncClient):
        """Test successful company registration."""
        data = {
            "company_name": "New Company",
            "subdomain": "newcompany",
            "company_email": "info@newcompany.com",
            "admin_email": "admin@newcompany.com",
            "admin_password": "Admin@12345",
            "admin_first_name": "Admin",
            "admin_last_name": "User",
        }

        response = await client.post("/api/v1/auth/register/company", json=data)

        assert response.status_code == 201
        result = response.json()
        assert "tenant_id" in result
        assert "user_id" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["tenant_domain"] == "newcompany.samvit.bhanu.dev"

    async def test_register_company_duplicate_subdomain(self, client: AsyncClient):
        """Test company registration with duplicate subdomain."""
        data = {
            "company_name": "First Company",
            "subdomain": "duplicate",
            "company_email": "info@first.com",
            "admin_email": "admin@first.com",
            "admin_password": "Admin@12345",
            "admin_first_name": "Admin",
            "admin_last_name": "User",
        }

        # First registration
        response1 = await client.post("/api/v1/auth/register/company", json=data)
        assert response1.status_code == 201

        # Second registration with same subdomain
        data["company_email"] = "info@second.com"
        data["admin_email"] = "admin@second.com"
        response2 = await client.post("/api/v1/auth/register/company", json=data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    async def test_register_company_invalid_subdomain(self, client: AsyncClient):
        """Test company registration with invalid subdomain."""
        data = {
            "company_name": "Invalid Company",
            "subdomain": "INVALID_SUBDOMAIN!",  # Invalid characters
            "company_email": "info@invalid.com",
            "admin_email": "admin@invalid.com",
            "admin_password": "Admin@12345",
            "admin_first_name": "Admin",
            "admin_last_name": "User",
        }

        response = await client.post("/api/v1/auth/register/company", json=data)

        assert response.status_code == 422  # Validation error

    async def test_register_company_weak_password(self, client: AsyncClient):
        """Test company registration with weak password."""
        data = {
            "company_name": "Weak Pass Company",
            "subdomain": "weakpass",
            "company_email": "info@weakpass.com",
            "admin_email": "admin@weakpass.com",
            "admin_password": "weak",  # Too short
            "admin_first_name": "Admin",
            "admin_last_name": "User",
        }

        response = await client.post("/api/v1/auth/register/company", json=data)

        assert response.status_code == 422  # Validation error


class TestUserRegistration:
    """Tests for user registration within a tenant."""

    async def test_register_user_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "password": "NewUser@123",
            "first_name": "New",
            "last_name": "User",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=data,
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 201
        result = response.json()
        assert "user" in result
        assert "access_token" in result
        assert result["user"]["email"] == "newuser@example.com"
        assert result["user"]["first_name"] == "New"

    async def test_register_user_duplicate_email(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test user registration with duplicate email in same tenant."""
        data = {
            "email": test_user.email,  # Existing user's email
            "password": "Duplicate@123",
            "first_name": "Duplicate",
            "last_name": "User",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=data,
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 409


class TestLogin:
    """Tests for user login."""

    async def test_login_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test successful login."""
        data = {
            "email": test_user.email,
            "password": "Test@12345",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=data,
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] > 0

    async def test_login_invalid_password(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test login with invalid password."""
        data = {
            "email": test_user.email,
            "password": "WrongPassword@123",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=data,
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    async def test_login_nonexistent_user(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test login with nonexistent user."""
        data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword@123",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=data,
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 401

    async def test_login_wrong_tenant(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test login from wrong tenant domain.

        When using a non-existent tenant domain, the middleware returns 404
        because tenant lookup fails before auth is checked.
        """
        data = {
            "email": test_user.email,
            "password": "Test@12345",
        }

        # Use a different tenant domain that doesn't exist
        response = await client.post(
            "/api/v1/auth/login",
            json=data,
            headers={"Host": "wrong-tenant.samvit.bhanu.dev"},
        )

        # Tenant middleware returns 404 when tenant not found
        assert response.status_code == 404


class TestCurrentUser:
    """Tests for current user endpoint."""

    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test getting current user info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["email"] == test_user.email
        assert result["first_name"] == test_user.first_name
        assert result["last_name"] == test_user.last_name
        assert result["tenant_id"] == test_tenant.id

    async def test_get_current_user_unauthorized(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test getting current user without authentication."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Host": test_tenant.domain},
        )

        assert response.status_code == 401

    async def test_get_current_user_invalid_token(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={
                "Host": test_tenant.domain,
                "Authorization": "Bearer invalid.token.here",
            },
        )

        assert response.status_code == 401


class TestUpdateProfile:
    """Tests for profile update endpoint."""

    async def test_update_profile_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test updating user profile."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+91-9876543210",
        }

        response = await client.patch(
            "/api/v1/auth/me",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["first_name"] == "Updated"
        assert result["last_name"] == "Name"
        assert result["phone"] == "+91-9876543210"

    async def test_update_profile_partial(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test partial profile update."""
        data = {
            "first_name": "PartiallyUpdated",
        }

        response = await client.patch(
            "/api/v1/auth/me",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert result["first_name"] == "PartiallyUpdated"
        assert result["last_name"] == test_user.last_name  # Unchanged


class TestChangePassword:
    """Tests for password change endpoint."""

    async def test_change_password_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test successful password change."""
        data = {
            "current_password": "Test@12345",
            "new_password": "NewPassword@123",
        }

        response = await client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

    async def test_change_password_wrong_current(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test password change with wrong current password."""
        data = {
            "current_password": "WrongPassword@123",
            "new_password": "NewPassword@123",
        }

        response = await client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 400

    async def test_change_password_weak_new(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test password change with weak new password."""
        data = {
            "current_password": "Test@12345",
            "new_password": "weak",  # Too short
        }

        response = await client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 422  # Validation error


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    async def test_refresh_token_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test successful token refresh."""
        # First login to get refresh token
        login_data = {
            "email": test_user.email,
            "password": "Test@12345",
        }
        login_response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers=get_tenant_headers(test_tenant),
        )
        refresh_token = login_response.json()["refresh_token"]

        # Now use refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result

    async def test_refresh_token_invalid(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test token refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.refresh.token"},
            headers=get_tenant_headers(test_tenant),
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    async def test_logout_success(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test successful logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=get_auth_headers(test_user, test_tenant),
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

    async def test_logout_unauthorized(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test logout without authentication."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Host": test_tenant.domain},
        )

        assert response.status_code == 401
