"""Auth service - authentication and user management."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.models import User, UserStatus
from app.modules.auth.schemas import (
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
)
from app.modules.tenants.models import Tenant, TenantStatus


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self.session = session
        self.tenant_id = tenant_id

    def _create_tokens(
        self, user: User, domain: str | None = None
    ) -> tuple[str, str, int]:
        """Create access and refresh tokens for a user."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
        }

        access_token = create_access_token(token_data, issuer=domain)
        refresh_token = create_refresh_token(token_data, issuer=domain)
        expires_in = settings.access_token_expire_minutes * 60

        return access_token, refresh_token, expires_in

    async def register_company(
        self, data: CompanyRegisterRequest
    ) -> CompanyRegisterResponse:
        """Register a new company (tenant) with admin user.

        This is the main signup flow for new organizations.
        Creates: Tenant -> Admin User -> Returns tokens
        """
        # Build full domain
        domain = f"{data.subdomain}.{settings.base_domain}"

        # Check if domain is reserved
        if domain in settings.reserved_domains:
            raise EntityAlreadyExistsError(
                "Domain", f"'{data.subdomain}' is a reserved subdomain"
            )

        # Check if domain already exists
        existing_tenant = await self.session.execute(
            select(Tenant).where(Tenant.domain == domain)
        )
        if existing_tenant.scalar_one_or_none():
            raise EntityAlreadyExistsError("Tenant", f"Domain '{domain}' already taken")

        # Check if tenant email exists
        existing_email = await self.session.execute(
            select(Tenant).where(Tenant.email == data.company_email)
        )
        if existing_email.scalar_one_or_none():
            raise EntityAlreadyExistsError("Tenant", data.company_email)

        # Create tenant
        tenant = Tenant(
            name=data.company_name,
            domain=domain,
            email=data.company_email,
            phone=data.company_phone,
            timezone=data.timezone,
            country=data.country,
            status=TenantStatus.ACTIVE.value,
            is_active=True,
        )
        self.session.add(tenant)
        await self.session.flush()

        # Check if admin email exists in this tenant (shouldn't, but be safe)
        existing_user = await self.session.execute(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == data.admin_email,
            )
        )
        if existing_user.scalar_one_or_none():
            raise EntityAlreadyExistsError("User", data.admin_email)

        # Create admin user
        user = User(
            tenant_id=tenant.id,
            email=data.admin_email,
            password_hash=get_password_hash(data.admin_password),
            first_name=data.admin_first_name,
            last_name=data.admin_last_name,
            status=UserStatus.ACTIVE.value,
            is_active=True,
            email_verified=False,  # Should verify via email
        )
        self.session.add(user)
        await self.session.flush()

        # Create tokens with domain as issuer
        access_token, refresh_token, expires_in = self._create_tokens(user, domain)

        return CompanyRegisterResponse(
            tenant_id=tenant.id,
            tenant_domain=domain,
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user in existing tenant (invitation flow)."""
        if not self.tenant_id:
            raise AuthenticationError("Tenant context required for registration")

        # Check if email exists in this tenant
        existing = await self._get_user_by_email(data.email)
        if existing:
            raise EntityAlreadyExistsError("User", data.email)

        user = User(
            tenant_id=self.tenant_id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            status=UserStatus.ACTIVE.value,
            is_active=True,
        )

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def register_with_tokens(
        self, data: RegisterRequest, domain: str | None = None
    ) -> tuple[User, TokenResponse]:
        """Register a new user and return tokens."""
        user = await self.register(data)

        access_token, refresh_token, expires_in = self._create_tokens(user, domain)

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

        return user, tokens

    async def login(
        self, data: LoginRequest, domain: str | None = None
    ) -> TokenResponse:
        """Authenticate user and return tokens."""
        user = await self._get_user_by_email(data.email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        if user.status == UserStatus.LOCKED.value:
            raise AuthenticationError("Account is locked")

        # Verify user belongs to the expected tenant (if tenant_id is set)
        if self.tenant_id and user.tenant_id != self.tenant_id:
            raise AuthenticationError("Invalid email or password")

        access_token, refresh_token, expires_in = self._create_tokens(user, domain)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    async def login_with_tenant_lookup(
        self, data: LoginRequest, domain: str
    ) -> TokenResponse:
        """Login by looking up tenant from domain first.

        Used when tenant context is resolved from Host header.
        """
        # Look up tenant by domain
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.domain == domain,
                Tenant.is_active.is_(True),
            )
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise AuthenticationError("Invalid domain")

        # Set tenant context
        self.tenant_id = tenant.id

        # Now perform login
        return await self.login(data, domain)

    async def refresh_tokens(
        self, refresh_token: str, domain: str | None = None
    ) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")

        # Get user without tenant filter (trust the token)
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        access_token, new_refresh_token, expires_in = self._create_tokens(user, domain)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        query = select(User).options(selectinload(User.roles)).where(User.id == user_id)

        # Filter by tenant if set
        if self.tenant_id:
            query = query.where(User.tenant_id == self.tenant_id)

        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise EntityNotFoundError("User", user_id)
        return user

    async def get_current_user(self, user_id: str) -> dict:
        """Get current user with roles and permissions."""
        user = await self.get_user(user_id)

        roles = [role.name for role in user.roles]
        permissions = set()
        for role in user.roles:
            try:
                perms = json.loads(role.permissions)
                permissions.update(perms)
            except json.JSONDecodeError:
                pass

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "tenant_id": user.tenant_id,
            "roles": roles,
            "permissions": list(permissions),
        }

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user (admin action)."""
        if not self.tenant_id:
            raise AuthenticationError("Tenant context required")

        existing = await self._get_user_by_email(data.email)
        if existing:
            raise EntityAlreadyExistsError("User", data.email)

        user = User(
            tenant_id=self.tenant_id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            employee_id=data.employee_id,
            status=UserStatus.ACTIVE.value,
        )

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def update_user(self, user_id: str, data: UserUpdate) -> User:
        """Update user profile."""
        user = await self.get_user(user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self.get_user(user_id)

        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        user.password_hash = get_password_hash(new_password)
        await self.session.flush()

        return True

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """List users in tenant."""
        if not self.tenant_id:
            raise AuthenticationError("Tenant context required")

        result = await self.session.execute(
            select(User)
            .where(User.tenant_id == self.tenant_id)
            .offset(offset)
            .limit(limit)
        )
        users = list(result.scalars().all())

        count_result = await self.session.execute(
            select(User).where(User.tenant_id == self.tenant_id)
        )
        total = len(list(count_result.scalars().all()))

        return users, total

    async def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email within tenant."""
        query = select(User).where(User.email == email)

        # Filter by tenant if set (email is unique per tenant)
        if self.tenant_id:
            query = query.where(User.tenant_id == self.tenant_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()
