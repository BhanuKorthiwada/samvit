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
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""
        # Check if email exists
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
            status=UserStatus.ACTIVE.value,  # Set to ACTIVE for testing
            is_active=True,
        )

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def register_with_tokens(
        self, data: RegisterRequest
    ) -> tuple[User, TokenResponse]:
        """Register a new user and return tokens."""
        user = await self.register(data)

        # Create tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

        return user, tokens

    async def login(self, data: LoginRequest) -> TokenResponse:
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

        # Create tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")
        user = await self.get_user(user_id)

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        token_data = {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
        }

        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id, User.tenant_id == self.tenant_id)
        )
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
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
