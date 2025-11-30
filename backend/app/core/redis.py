"""Centralized Redis connection pool for all Redis-based services.

This module provides a shared Redis connection pool to avoid creating
multiple connections for rate limiting, token blacklist, and caching.

Features:
- Single connection pool with health checks
- Automatic reconnection on failure
- Graceful shutdown handling
- Fail-open design philosophy
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Connection pool configuration
REDIS_CONFIG = {
    "decode_responses": True,
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True,
    "health_check_interval": 30,
    "max_connections": 50,  # Shared across all services
}


class RedisPool:
    """Centralized Redis connection pool manager.

    Provides a shared connection pool for all Redis-based services:
    - Rate limiter
    - Token blacklist
    - Future: Caching, sessions, etc.

    Design Philosophy:
    - Single pool to minimize connections
    - Fail-open: Services should handle unavailability gracefully
    - Health checks to detect issues early
    """

    __slots__ = ("_pool", "_url")

    def __init__(self, url: str | None = None) -> None:
        self._pool: aioredis.ConnectionPool | None = None
        self._url = url or settings.redis_url

    @property
    def is_connected(self) -> bool:
        """Check if connection pool is initialized."""
        return self._pool is not None

    async def connect(self) -> None:
        """Initialize the connection pool."""
        if self._pool:
            return

        try:
            self._pool = aioredis.ConnectionPool.from_url(
                self._url,
                **REDIS_CONFIG,
            )
            # Test connectivity
            async with self.get_client() as client:
                await client.ping()
            logger.info("Redis connection pool initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis connection pool: %s", e)
            self._pool = None

    async def close(self) -> None:
        """Close the connection pool gracefully."""
        if not self._pool:
            return

        try:
            await self._pool.aclose()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.warning("Error closing Redis connection pool: %s", e)
        finally:
            self._pool = None

    @asynccontextmanager
    async def get_client(self) -> AsyncIterator[aioredis.Redis]:
        """Get a Redis client from the pool.

        Usage:
            async with redis_pool.get_client() as client:
                await client.set("key", "value")

        Yields:
            Redis client instance

        Raises:
            RuntimeError: If pool is not initialized
        """
        if not self._pool:
            await self.connect()

        if not self._pool:
            raise RuntimeError("Redis connection pool not available")

        client = aioredis.Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            await client.aclose()

    async def get_client_unsafe(self) -> aioredis.Redis | None:
        """Get a Redis client without context manager.

        Returns None if pool is not available.
        Caller is responsible for proper error handling.

        Use this for long-lived clients that manage their own lifecycle.
        """
        if not self._pool:
            await self.connect()

        if not self._pool:
            return None

        return aioredis.Redis(connection_pool=self._pool)

    async def ping(self) -> bool:
        """Check if Redis is reachable.

        Returns:
            True if Redis responds to ping, False otherwise
        """
        try:
            async with self.get_client() as client:
                await client.ping()
            return True
        except Exception:
            return False


# Global singleton instance
redis_pool = RedisPool()
