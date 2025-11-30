"""Token blacklist service for JWT revocation.

Features:
- Redis-based token blacklist with automatic TTL
- Fail-open design for high availability (auth continues if Redis is down)
- Shared Redis connection pool
- Graceful error handling and logging
- Uses token hash for storage efficiency
"""

import hashlib
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.core.redis import redis_pool

logger = logging.getLogger(__name__)

# Key prefix for blacklisted tokens
BLACKLIST_PREFIX = "token:revoked:"


def _hash_token(token: str) -> str:
    """Hash token for storage efficiency and security.

    Using SHA-256 hash instead of storing full JWT:
    - Reduces Redis memory usage (~64 bytes vs ~500+ bytes per token)
    - Prevents token exposure if Redis is compromised
    """
    return hashlib.sha256(token.encode()).hexdigest()


class TokenBlacklist:
    """Redis-based token blacklist for logout and token revocation.

    Design Principles:
    - Fail-open for is_revoked(): If Redis is down, allow the request
      (security tradeoff: can't revoke during outage, but app stays up)
    - Fail with warning for revoke_token(): Logout may fail, user can retry
    - Uses shared Redis connection pool from app.core.redis
    """

    __slots__ = ("_redis",)

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._redis is not None

    async def connect(self) -> None:
        """Connect to Redis using shared pool."""
        if self._redis:
            return

        try:
            self._redis = await redis_pool.get_client_unsafe()
            if not self._redis:
                logger.warning("Redis pool not available for token blacklist")
                return

            await self._redis.ping()
            logger.info("Token blacklist connected to Redis")
        except Exception as e:
            logger.error("Failed to connect token blacklist to Redis: %s", e)
            self._redis = None

    async def close(self) -> None:
        """Close Redis client (pool is managed separately)."""
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception as e:
                logger.warning("Error closing token blacklist Redis client: %s", e)
            finally:
                self._redis = None

    async def revoke_token(self, token: str, expires_at: datetime) -> bool:
        """Add token to blacklist until its expiry time.

        Args:
            token: The JWT token to revoke
            expires_at: When the token naturally expires

        Returns:
            True if token was successfully blacklisted, False otherwise
        """
        if not self._redis:
            await self.connect()

        if not self._redis:
            logger.warning("Cannot revoke token - Redis unavailable")
            return False

        try:
            # Calculate TTL (time until token expires)
            now = datetime.now(timezone.utc)
            ttl = int((expires_at - now).total_seconds())

            if ttl <= 0:
                # Token already expired, no need to blacklist
                logger.debug("Token already expired, skipping blacklist")
                return True

            # Use hashed token for storage
            token_hash = _hash_token(token)
            key = f"{BLACKLIST_PREFIX}{token_hash}"

            await self._redis.setex(key, ttl, "1")
            logger.debug("Token blacklisted with TTL %ds", ttl)
            return True

        except aioredis.ConnectionError as e:
            logger.error("Redis connection error during token revocation: %s", e)
            return False

        except aioredis.TimeoutError as e:
            logger.error("Redis timeout during token revocation: %s", e)
            return False

        except Exception as e:
            logger.exception("Unexpected error during token revocation: %s", e)
            return False

    async def is_revoked(self, token: str) -> bool:
        """Check if token is revoked.

        FAIL-OPEN DESIGN: If Redis is unavailable, returns False (not revoked).
        This allows authenticated requests to continue during Redis outages.

        Security tradeoff: During an outage, revoked tokens may still work
        until Redis is restored. This is acceptable because:
        1. Outages should be brief
        2. Tokens have natural expiry
        3. App availability is prioritized

        Args:
            token: The JWT token to check

        Returns:
            True if token is revoked, False otherwise (including Redis errors)
        """
        if not self._redis:
            await self.connect()

        if not self._redis:
            # Fail open - allow request if Redis unavailable
            logger.warning("Token blacklist unavailable - failing open")
            return False

        try:
            token_hash = _hash_token(token)
            key = f"{BLACKLIST_PREFIX}{token_hash}"
            exists = await self._redis.exists(key)
            return bool(exists)

        except aioredis.ConnectionError as e:
            logger.error(
                "Redis connection error checking blacklist: %s - failing open", e
            )
            return False

        except aioredis.TimeoutError as e:
            logger.error("Redis timeout checking blacklist: %s - failing open", e)
            return False

        except Exception as e:
            logger.exception(
                "Unexpected error checking blacklist: %s - failing open", e
            )
            return False

    async def revoke_all_user_tokens(self, user_id: str, ttl: int = 86400) -> bool:
        """Revoke all tokens for a user (e.g., password change, account compromise).

        This uses a separate key to track user-level revocation.
        Token validation should check both individual token and user-level revocation.

        Args:
            user_id: The user whose tokens should be revoked
            ttl: How long to keep the revocation active (default 24 hours)

        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            await self.connect()

        if not self._redis:
            logger.warning("Cannot revoke user tokens - Redis unavailable")
            return False

        try:
            key = f"user:revoked:{user_id}"
            # Store timestamp of revocation
            await self._redis.setex(
                key, ttl, str(int(datetime.now(timezone.utc).timestamp()))
            )
            logger.info("All tokens revoked for user %s", user_id)
            return True

        except Exception as e:
            logger.exception("Error revoking all user tokens: %s", e)
            return False

    async def is_user_tokens_revoked(self, user_id: str, token_issued_at: int) -> bool:
        """Check if user's tokens were revoked after a specific time.

        Args:
            user_id: The user to check
            token_issued_at: Unix timestamp when the token was issued (iat claim)

        Returns:
            True if user's tokens were revoked after token was issued, False otherwise
        """
        if not self._redis:
            await self.connect()

        if not self._redis:
            # Fail open
            return False

        try:
            key = f"user:revoked:{user_id}"
            revoked_at = await self._redis.get(key)

            if revoked_at is None:
                return False

            # Token is revoked if it was issued before the revocation time
            return token_issued_at < int(revoked_at)

        except Exception as e:
            logger.exception(
                "Error checking user token revocation: %s - failing open", e
            )
            return False


# Global singleton instance
token_blacklist = TokenBlacklist()
