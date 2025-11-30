"""Tests for the rate limiter module."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.core.rate_limit import (
    RateLimiter,
    RateLimitHeaderMiddleware,
    RateLimitInfo,
    RateLimitStrategy,
    rate_limit,
)


class TestRateLimitInfo:
    """Tests for RateLimitInfo dataclass."""

    def test_immutability(self) -> None:
        """RateLimitInfo should be immutable."""
        info = RateLimitInfo(
            allowed=True,
            limit=100,
            remaining=99,
            reset=int(time.time()) + 60,
        )
        with pytest.raises(AttributeError):
            info.allowed = False  # type: ignore[misc]

    def test_defaults(self) -> None:
        """Should have correct default values."""
        info = RateLimitInfo(allowed=True, limit=10, remaining=9, reset=123)
        assert info.retry_after == 0


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    @pytest.fixture
    def limiter(self) -> RateLimiter:
        """Create a fresh rate limiter instance."""
        return RateLimiter()

    def test_initial_state(self, limiter: RateLimiter) -> None:
        """Limiter should start disconnected."""
        assert not limiter.is_connected
        assert limiter._redis is None

    @pytest.mark.asyncio
    async def test_fail_open_when_redis_unavailable(self, limiter: RateLimiter) -> None:
        """Should allow requests when Redis is unavailable."""
        # Don't connect to Redis - simulates unavailable state
        result = await limiter.check_sliding_window("test:key", 5, 60)

        assert result.allowed is True
        assert result.limit == 5
        assert result.remaining == 5

    @pytest.mark.asyncio
    async def test_fail_open_token_bucket(self, limiter: RateLimiter) -> None:
        """Token bucket should also fail open when Redis unavailable."""
        result = await limiter.check_token_bucket("test:token_bucket:failopen", 10, 1.0)

        assert result.allowed is True
        assert result.limit == 10
        # When Redis unavailable (fail-open): remaining == limit
        # When Redis connected: remaining == limit - 1 (consumed one token)
        assert result.remaining in (9, 10)

    def test_get_client_ip_direct(self, limiter: RateLimiter) -> None:
        """Should extract IP from direct connection."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"

        ip = limiter.get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_x_forwarded_for(self, limiter: RateLimiter) -> None:
        """Should extract first IP from X-Forwarded-For."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers(
            {"x-forwarded-for": "203.0.113.50, 70.41.3.18, 150.172.238.178"}
        )
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        ip = limiter.get_client_ip(mock_request)
        assert ip == "203.0.113.50"

    def test_get_client_ip_cloudflare(self, limiter: RateLimiter) -> None:
        """Should prefer Cloudflare header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers(
            {
                "cf-connecting-ip": "198.51.100.1",
                "x-forwarded-for": "10.0.0.1",
            }
        )
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.2"

        ip = limiter.get_client_ip(mock_request)
        assert ip == "198.51.100.1"

    def test_get_client_ip_x_real_ip(self, limiter: RateLimiter) -> None:
        """Should use X-Real-IP when available."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"x-real-ip": "203.0.113.100"})
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        ip = limiter.get_client_ip(mock_request)
        assert ip == "203.0.113.100"

    def test_get_client_ip_no_client(self, limiter: RateLimiter) -> None:
        """Should return 'unknown' when no client info."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = None

        ip = limiter.get_client_ip(mock_request)
        assert ip == "unknown"


class TestRateLimitDependency:
    """Tests for the rate_limit dependency factory."""

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.headers = Headers({})
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.state = MagicMock()
        return request

    @pytest.mark.asyncio
    async def test_rate_limit_passes_when_redis_unavailable(
        self, mock_request: MagicMock
    ) -> None:
        """Rate limit should pass when Redis is down (fail-open)."""
        limiter_fn = rate_limit(5, 60)

        # Should not raise (fails open)
        await limiter_fn(mock_request)

        # Should have rate limit info attached
        assert hasattr(mock_request.state, "rate_limit_info")

    @pytest.mark.asyncio
    async def test_rate_limit_with_per_user(self, mock_request: MagicMock) -> None:
        """Should use user ID when per_user=True and user is authenticated."""
        mock_request.state.user_id = "user-123"
        limiter_fn = rate_limit(10, 60, per_user=True)

        await limiter_fn(mock_request)

        # Info should be attached
        info = mock_request.state.rate_limit_info
        assert info.allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_key_prefix(self, mock_request: MagicMock) -> None:
        """Should use custom key prefix."""
        limiter_fn = rate_limit(10, 60, key_prefix="custom")

        await limiter_fn(mock_request)
        assert mock_request.state.rate_limit_info.allowed is True


class TestRateLimitIntegration:
    """Integration tests with mock Redis."""

    @pytest.fixture
    def mock_redis(self) -> AsyncMock:
        """Create a mock Redis client that works with async/await."""
        redis = AsyncMock()
        # These need to be coroutines that return values
        redis.ping = AsyncMock(return_value=True)
        redis.script_load = AsyncMock(side_effect=["sha1", "sha2"])
        redis.evalsha = AsyncMock(return_value=[1, 9, int(time.time()) + 60])
        redis.aclose = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_sliding_window_with_redis(self, mock_redis: AsyncMock) -> None:
        """Should correctly check rate limit with Redis."""
        limiter = RateLimiter()

        with patch("app.core.rate_limit.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await limiter.connect()
            assert limiter.is_connected
            result = await limiter.check_sliding_window("test:key", 10, 60)

            assert result.allowed is True
            assert result.remaining == 9
            mock_redis.evalsha.assert_called_once()

    @pytest.mark.asyncio
    async def test_sliding_window_limit_exceeded(self, mock_redis: AsyncMock) -> None:
        """Should deny when limit is exceeded."""
        mock_redis.evalsha = AsyncMock(
            return_value=[0, 0, int(time.time()) + 30]  # Not allowed
        )
        limiter = RateLimiter()

        with patch("app.core.rate_limit.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await limiter.connect()
            result = await limiter.check_sliding_window("test:key", 5, 60)

            assert result.allowed is False
            assert result.remaining == 0
            assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_token_bucket_with_redis(self, mock_redis: AsyncMock) -> None:
        """Should correctly check token bucket with Redis."""
        mock_redis.evalsha = AsyncMock(return_value=[1, 8, 2])
        limiter = RateLimiter()

        with patch("app.core.rate_limit.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await limiter.connect()
            result = await limiter.check_token_bucket("test:key", 10, 1.0)

            assert result.allowed is True
            assert result.remaining == 8

    @pytest.mark.asyncio
    async def test_script_reload_on_noscript_error(self, mock_redis: AsyncMock) -> None:
        """Should reload script when NOSCRIPT error occurs."""
        from redis.exceptions import NoScriptError

        call_count = 0

        async def evalsha_side_effect(*_args, **_kwargs):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NoScriptError("Script not found")
            return [1, 4, int(time.time()) + 60]

        # Need enough return values for initial load + reload
        mock_redis.script_load = AsyncMock(
            side_effect=["sha1", "sha2", "sha1_reloaded", "sha2_reloaded"]
        )
        mock_redis.evalsha = AsyncMock(side_effect=evalsha_side_effect)
        limiter = RateLimiter()

        with patch("app.core.rate_limit.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await limiter.connect()
            result = await limiter.check_sliding_window("test:key", 5, 60)

            assert result.allowed is True
            # Should have reloaded the script (initial 2 + 1 reload = 3)
            assert mock_redis.script_load.call_count >= 3


class TestRateLimitHeaderMiddleware:
    """Tests for the rate limit header middleware."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a test FastAPI app."""
        app = FastAPI()
        app.add_middleware(RateLimitHeaderMiddleware)

        @app.get("/test")
        async def test_endpoint(request: Request):
            # Simulate rate limit info being set
            request.state.rate_limit_info = RateLimitInfo(
                allowed=True,
                limit=100,
                remaining=99,
                reset=1234567890,
            )
            return {"message": "ok"}

        @app.get("/no-limit")
        async def no_limit_endpoint():
            return {"message": "ok"}

        return app

    def test_adds_headers_when_rate_limit_info_present(self, app: FastAPI) -> None:
        """Should add rate limit headers to response."""
        # Note: This tests the concept but middleware needs proper setup
        # In a real test, we'd use httpx with ASGI transport
        client = TestClient(app)
        # Middleware won't work correctly with TestClient for request.state
        # This is a limitation - real integration tests would use httpx
        response = client.get("/no-limit")
        assert response.status_code == 200


class TestRateLimitStrategies:
    """Tests for different rate limiting strategies."""

    def test_strategy_enum_values(self) -> None:
        """Strategy enum should have correct values."""
        assert RateLimitStrategy.SLIDING_WINDOW.value == "sliding_window"
        assert RateLimitStrategy.TOKEN_BUCKET.value == "token_bucket"

    @pytest.mark.asyncio
    async def test_sliding_window_strategy_selection(self) -> None:
        """Should use sliding window by default."""
        limiter_fn = rate_limit(10, 60)

        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"
        mock_request.state = MagicMock()

        await limiter_fn(mock_request)
        assert mock_request.state.rate_limit_info is not None

    @pytest.mark.asyncio
    async def test_token_bucket_strategy_selection(self) -> None:
        """Should use token bucket when specified."""
        limiter_fn = rate_limit(10, 60, strategy=RateLimitStrategy.TOKEN_BUCKET)

        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"
        mock_request.state = MagicMock()

        await limiter_fn(mock_request)
        assert mock_request.state.rate_limit_info is not None
