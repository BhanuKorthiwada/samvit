"""High-performance Redis-based rate limiter for FastAPI.

Features:
- Atomic Lua script for race-condition-free limiting
- Sliding window with token bucket hybrid algorithm
- Per-IP and per-user rate limiting
- Fail-open design for high availability
- Standard rate limit headers on all responses
- Configurable burst allowance
- Shared Redis connection pool
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, Response, status
from redis.exceptions import NoScriptError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.redis import redis_pool

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass(frozen=True, slots=True)
class RateLimitInfo:
    """Rate limit check result - immutable for thread safety."""

    allowed: bool
    limit: int
    remaining: int
    reset: int
    retry_after: int = 0


# Lua script for atomic sliding window rate limiting
# This prevents race conditions by doing check + increment atomically
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local request_id = ARGV[4]

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Get current count
local count = redis.call('ZCARD', key)

if count < limit then
    -- Add this request with unique ID to prevent duplicate entries
    redis.call('ZADD', key, now, request_id)
    redis.call('EXPIRE', key, window + 10)
    return {1, limit - count - 1, now + window}
else
    -- Get oldest entry to calculate reset time
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset_at = now + window
    if oldest and #oldest >= 2 then
        reset_at = tonumber(oldest[2]) + window
    end
    return {0, 0, reset_at}
end
"""

# Lua script for token bucket algorithm (allows bursting)
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])     -- Max tokens (burst capacity)
local refill_rate = tonumber(ARGV[2])  -- Tokens per second
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])    -- Usually 1

-- Get current bucket state
local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Calculate tokens to add based on time elapsed
local elapsed = now - last_refill
local refill = elapsed * refill_rate
tokens = math.min(capacity, tokens + refill)

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 10)
    return {1, math.floor(tokens), math.ceil((capacity - tokens) / refill_rate)}
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 10)
    local wait_time = math.ceil((requested - tokens) / refill_rate)
    return {0, 0, wait_time}
end
"""


class RateLimiter:
    """High-performance Redis-based rate limiter with multiple strategies.

    Uses shared Redis connection pool from app.core.redis.
    """

    __slots__ = ("_redis", "_sliding_window_sha", "_token_bucket_sha")

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self._sliding_window_sha: str | None = None
        self._token_bucket_sha: str | None = None

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._redis is not None

    async def connect(self) -> None:
        """Connect to Redis using shared pool and load Lua scripts."""
        if self._redis:
            return

        try:
            self._redis = await redis_pool.get_client_unsafe()
            if not self._redis:
                logger.warning("Redis pool not available for rate limiter")
                return

            await self._redis.ping()

            # Pre-load Lua scripts for better performance
            self._sliding_window_sha = await self._redis.script_load(
                SLIDING_WINDOW_SCRIPT
            )
            self._token_bucket_sha = await self._redis.script_load(TOKEN_BUCKET_SCRIPT)

            logger.info("Rate limiter connected to Redis with Lua scripts loaded")
        except Exception as e:
            logger.error("Failed to initialize rate limiter: %s", e)
            self._redis = None
            self._sliding_window_sha = None
            self._token_bucket_sha = None

    async def close(self) -> None:
        """Close Redis client (pool is managed separately)."""
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception as e:
                logger.warning("Error closing rate limiter Redis client: %s", e)
            finally:
                self._redis = None
                self._sliding_window_sha = None
                self._token_bucket_sha = None

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies and load balancers."""
        # Check proxy headers in order of preference
        # Cloudflare (most specific)
        if cf_ip := request.headers.get("cf-connecting-ip"):
            return cf_ip

        # Standard proxy headers
        if forwarded := request.headers.get("x-forwarded-for"):
            # Take the first (original client) IP
            return forwarded.split(",")[0].strip()

        if real_ip := request.headers.get("x-real-ip"):
            return real_ip

        # Direct connection
        return request.client.host if request.client else "unknown"

    async def check_sliding_window(
        self, key: str, limit: int, window: int
    ) -> RateLimitInfo:
        """
        Check rate limit using atomic sliding window algorithm.

        Args:
            key: Unique identifier for the rate limit bucket
            limit: Maximum requests allowed in the window
            window: Time window in seconds

        Returns:
            RateLimitInfo with the result
        """
        now = time.time()

        if not self._redis or not self._sliding_window_sha:
            await self.connect()

        if not self._redis or not self._sliding_window_sha:
            # Fail open - allow request if Redis unavailable
            logger.warning("Redis unavailable - rate limit bypassed")
            return RateLimitInfo(
                allowed=True, limit=limit, remaining=limit, reset=int(now + window)
            )

        try:
            # Generate unique request ID to prevent duplicate entries
            request_id = f"{now}:{id(key)}"

            result = await self._redis.evalsha(
                self._sliding_window_sha,
                1,  # Number of keys
                key,
                limit,
                window,
                now,
                request_id,
            )

            allowed = bool(result[0])
            remaining = int(result[1])
            reset_at = int(result[2])
            retry_after = max(0, reset_at - int(now)) if not allowed else 0

            return RateLimitInfo(
                allowed=allowed,
                limit=limit,
                remaining=remaining,
                reset=reset_at,
                retry_after=retry_after,
            )

        except NoScriptError:
            # Script was flushed, reload it
            logger.warning("Lua script not found, reloading...")
            self._sliding_window_sha = await self._redis.script_load(
                SLIDING_WINDOW_SCRIPT
            )
            return await self.check_sliding_window(key, limit, window)

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error("Redis connection error: %s - failing open", e)
            return RateLimitInfo(
                allowed=True, limit=limit, remaining=limit, reset=int(now + window)
            )

        except Exception as e:
            logger.exception("Rate limiter error: %s", e)
            return RateLimitInfo(
                allowed=True, limit=limit, remaining=limit, reset=int(now + window)
            )

    async def check_token_bucket(
        self, key: str, capacity: int, refill_rate: float
    ) -> RateLimitInfo:
        """
        Check rate limit using token bucket algorithm (allows bursting).

        Args:
            key: Unique identifier for the bucket
            capacity: Maximum tokens (burst capacity)
            refill_rate: Tokens added per second

        Returns:
            RateLimitInfo with the result
        """
        now = time.time()

        if not self._redis or not self._token_bucket_sha:
            await self.connect()

        if not self._redis or not self._token_bucket_sha:
            logger.warning("Redis unavailable - rate limit bypassed")
            return RateLimitInfo(
                allowed=True,
                limit=capacity,
                remaining=capacity,
                reset=int(now + capacity / refill_rate),
            )

        try:
            result = await self._redis.evalsha(
                self._token_bucket_sha,
                1,
                key,
                capacity,
                refill_rate,
                now,
                1,  # Request 1 token
            )

            allowed = bool(result[0])
            remaining = int(result[1])
            wait_time = int(result[2])

            return RateLimitInfo(
                allowed=allowed,
                limit=capacity,
                remaining=remaining,
                reset=int(now + wait_time),
                retry_after=wait_time if not allowed else 0,
            )

        except NoScriptError:
            logger.warning("Lua script not found, reloading...")
            self._token_bucket_sha = await self._redis.script_load(TOKEN_BUCKET_SCRIPT)
            return await self.check_token_bucket(key, capacity, refill_rate)

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error("Redis connection error: %s - failing open", e)
            return RateLimitInfo(
                allowed=True,
                limit=capacity,
                remaining=capacity,
                reset=int(now + capacity / refill_rate),
            )

        except Exception as e:
            logger.exception("Rate limiter error: %s", e)
            return RateLimitInfo(
                allowed=True,
                limit=capacity,
                remaining=capacity,
                reset=int(now + capacity / refill_rate),
            )


# Global singleton instance
rate_limiter = RateLimiter()


def rate_limit(
    limit: int,
    window: int = 60,
    *,
    per_user: bool = False,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    key_prefix: str = "rl",
):
    """
    Rate limit dependency for FastAPI endpoints.

    Args:
        limit: Maximum requests allowed (or bucket capacity for token bucket)
        window: Time window in seconds (ignored for token bucket, uses limit/window as refill rate)
        per_user: If True, rate limit per authenticated user instead of IP
        strategy: Algorithm to use (sliding_window or token_bucket)
        key_prefix: Prefix for Redis keys

    Usage:
        @router.post("/login")
        async def login(
            request: Request,
            _: Annotated[None, Depends(rate_limit(5, 60))]
        ):
            pass

        # Per-user rate limiting for authenticated endpoints
        @router.post("/api/action")
        async def action(
            _: Annotated[None, Depends(rate_limit(100, 60, per_user=True))]
        ):
            pass

        # Token bucket for APIs that need burst support
        @router.get("/api/data")
        async def get_data(
            _: Annotated[None, Depends(rate_limit(10, 1, strategy=RateLimitStrategy.TOKEN_BUCKET))]
        ):
            pass
    """

    async def check_limit(request: Request) -> None:
        # Determine the identifier for rate limiting
        identifier: str

        if per_user and hasattr(request.state, "user_id") and request.state.user_id:
            identifier = f"user:{request.state.user_id}"
        else:
            identifier = f"ip:{rate_limiter.get_client_ip(request)}"

        # Build the rate limit key
        path = request.url.path.replace("/", "_")
        key = f"{key_prefix}:{path}:{identifier}"

        # Check rate limit based on strategy
        if strategy == RateLimitStrategy.TOKEN_BUCKET:
            # For token bucket: limit = capacity, window determines refill rate
            refill_rate = limit / window if window > 0 else 1.0
            info = await rate_limiter.check_token_bucket(key, limit, refill_rate)
        else:
            info = await rate_limiter.check_sliding_window(key, limit, window)

        # Store info for middleware to add headers
        request.state.rate_limit_info = info

        if not info.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {info.retry_after} seconds.",
                headers={
                    "X-RateLimit-Limit": str(info.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.reset),
                    "Retry-After": str(info.retry_after),
                },
            )

    return check_limit


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to all responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Add rate limit headers if available
        if hasattr(request.state, "rate_limit_info"):
            info: RateLimitInfo = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(info.limit)
            response.headers["X-RateLimit-Remaining"] = str(info.remaining)
            response.headers["X-RateLimit-Reset"] = str(info.reset)

        return response
