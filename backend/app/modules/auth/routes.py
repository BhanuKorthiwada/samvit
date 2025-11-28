"""Auth API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import AuthenticationError, EntityAlreadyExistsError
from app.core.security import CurrentUserId
from app.core.tenancy import TenantDep, extract_domain_from_host
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserSummary,
    UserUpdate,
)
from app.modules.auth.service import AuthService
from app.shared.schemas import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(
    tenant: TenantDep,
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Get auth service dependency with tenant context."""
    return AuthService(session, tenant.tenant_id)


def get_auth_service_no_tenant(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Get auth service dependency without tenant context (for company signup)."""
    return AuthService(session)


@router.post(
    "/register/company",
    response_model=CompanyRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new company",
)
async def register_company(
    data: CompanyRegisterRequest,
    service: AuthService = Depends(get_auth_service_no_tenant),
) -> CompanyRegisterResponse:
    """
    Register a new company (tenant) with admin user.

    This is the main signup endpoint for new organizations.
    Creates a new tenant and the first admin user.
    """
    try:
        return await service.register_company(data)
    except EntityAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user (invitation)",
)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Register a new user in an existing tenant.

    This endpoint is for invited users joining an existing organization.
    Tenant is identified via the Host header (subdomain or custom domain).
    """
    try:
        user, tokens = await service.register_with_tokens(data)
        # Build response manually to avoid lazy loading issues
        user_response = UserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            status=user.status,
            is_active=user.is_active,
            email_verified=user.email_verified,
            employee_id=user.employee_id,
            roles=[],
        )
        return RegisterResponse(
            user=user_response,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )
    except EntityAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
)
async def login(
    request: Request,
    data: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """
    Authenticate and get access tokens.

    Tenant is resolved from the Host header (subdomain or custom domain).
    """
    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    service = AuthService(session)
    try:
        return await service.login_with_tenant_lookup(data, domain)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
)
async def refresh_tokens(
    request: Request,
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    # Extract domain for issuer
    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    service = AuthService(session)
    try:
        return await service.refresh_tokens(data.refresh_token, domain)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user",
)
async def get_current_user(
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_async_session),
) -> CurrentUserResponse:
    """Get current authenticated user info."""
    # Don't require tenant context - trust the JWT
    service = AuthService(session)
    user_data = await service.get_current_user(user_id)
    return CurrentUserResponse(**user_data)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update profile",
)
async def update_profile(
    data: UserUpdate,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_async_session),
) -> UserResponse:
    """Update current user's profile."""
    service = AuthService(session)
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change password",
)
async def change_password(
    data: ChangePasswordRequest,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Change current user's password."""
    service = AuthService(session)
    try:
        await service.change_password(
            user_id,
            data.current_password,
            data.new_password,
        )
        return SuccessResponse(message="Password changed successfully")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# --- Admin endpoints for user management ---


admin_router = APIRouter(prefix="/users", tags=["Users (Admin)"])


@admin_router.get(
    "",
    response_model=PaginatedResponse[UserSummary],
    summary="List users",
)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    service: AuthService = Depends(get_auth_service),
) -> PaginatedResponse[UserSummary]:
    """List all users in tenant (admin only)."""
    offset = (page - 1) * page_size
    users, total = await service.list_users(offset=offset, limit=page_size)
    items = [UserSummary.model_validate(u) for u in users]
    return PaginatedResponse.create(items, total, page, page_size)


@admin_router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(
    data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Create a new user (admin only)."""
    try:
        user = await service.create_user(data)
        return UserResponse.model_validate(user)
    except EntityAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@admin_router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
)
async def get_user(
    user_id: str,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Get a specific user (admin only)."""
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)
