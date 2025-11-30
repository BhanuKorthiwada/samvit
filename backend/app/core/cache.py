"""Redis caching layer for the application.

This module provides a flexible caching system with:
- TTL-based expiration
- Key prefixing for namespace isolation
- JSON serialization for complex objects
- Tenant-aware caching
- Cache invalidation patterns
- Fail-open design (cache misses on errors)

Usage:
    from app.core.cache import cache

    # Simple caching
    await cache.set("key", {"data": "value"}, ttl=300)
    data = await cache.get("key")

    # Tenant-scoped caching
    await cache.set("user:123", user_data, tenant_id="tenant-1")

    # Decorator for function caching
    @cached(ttl=60, prefix="employees")
    async def get_employee(employee_id: str) -> dict:
        ...

    # Cache invalidation
    await cache.delete("key")
    await cache.delete_pattern("employees:*")
"""

import functools
import hashlib
import inspect
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, ParamSpec, TypeVar

from pydantic import BaseModel

from app.core.redis import redis_pool

logger = logging.getLogger(__name__)

# Type variables for generic decorator
P = ParamSpec("P")
R = TypeVar("R")

# Default configuration
DEFAULT_TTL = 300  # 5 minutes
KEY_PREFIX = "samvit:cache"


class CacheSerializer:
    """Handles serialization/deserialization for cache values."""

    @staticmethod
    def serialize(value: Any) -> str:
        """Serialize a value to JSON string.

        Handles:
        - Pydantic models
        - Dictionaries
        - Lists
        - Primitives
        """
        if isinstance(value, BaseModel):
            return value.model_dump_json()
        return json.dumps(value, default=str)

    @staticmethod
    def deserialize(value: str | None) -> Any:
        """Deserialize a JSON string back to Python object."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class Cache:
    """Redis-based caching layer with fail-open design.

    Key Features:
    - Automatic serialization of Python objects
    - TTL-based expiration
    - Tenant isolation through key prefixing
    - Pattern-based invalidation
    - Graceful degradation on Redis failures
    """

    __slots__ = ("_prefix", "_serializer")

    def __init__(self, prefix: str = KEY_PREFIX) -> None:
        self._prefix = prefix
        self._serializer = CacheSerializer()

    def _build_key(self, key: str, tenant_id: str | None = None) -> str:
        """Build a namespaced cache key.

        Format: prefix:tenant_id:key or prefix:key
        """
        if tenant_id:
            return f"{self._prefix}:{tenant_id}:{key}"
        return f"{self._prefix}:{key}"

    async def get(self, key: str, tenant_id: str | None = None) -> Any:
        """Get a value from cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for scoping

        Returns:
            Cached value or None if not found/error
        """
        full_key = self._build_key(key, tenant_id)
        try:
            async with redis_pool.get_client() as client:
                value = await client.get(full_key)
                return self._serializer.deserialize(value)
        except Exception as e:
            logger.warning("Cache get failed for key %s: %s", full_key, e)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | timedelta = DEFAULT_TTL,
        tenant_id: str | None = None,
    ) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds or timedelta
            tenant_id: Optional tenant ID for scoping

        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key, tenant_id)
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())

        try:
            serialized = self._serializer.serialize(value)
            async with redis_pool.get_client() as client:
                await client.set(full_key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning("Cache set failed for key %s: %s", full_key, e)
            return False

    async def delete(self, key: str, tenant_id: str | None = None) -> bool:
        """Delete a key from cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for scoping

        Returns:
            True if key was deleted, False otherwise
        """
        full_key = self._build_key(key, tenant_id)
        try:
            async with redis_pool.get_client() as client:
                result = await client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.warning("Cache delete failed for key %s: %s", full_key, e)
            return False

    async def delete_pattern(self, pattern: str, tenant_id: str | None = None) -> int:
        """Delete all keys matching a pattern.

        WARNING: Use sparingly - SCAN can be slow on large keyspaces.

        Args:
            pattern: Glob-style pattern (e.g., "user:*")
            tenant_id: Optional tenant ID for scoping

        Returns:
            Number of keys deleted
        """
        full_pattern = self._build_key(pattern, tenant_id)
        deleted = 0
        try:
            async with redis_pool.get_client() as client:
                cursor = 0
                while True:
                    cursor, keys = await client.scan(
                        cursor=cursor,
                        match=full_pattern,
                        count=100,
                    )
                    if keys:
                        deleted += await client.delete(*keys)
                    if cursor == 0:
                        break
            logger.debug("Deleted %d keys matching pattern %s", deleted, full_pattern)
            return deleted
        except Exception as e:
            logger.warning("Cache delete_pattern failed for %s: %s", full_pattern, e)
            return deleted

    async def exists(self, key: str, tenant_id: str | None = None) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for scoping

        Returns:
            True if key exists, False otherwise
        """
        full_key = self._build_key(key, tenant_id)
        try:
            async with redis_pool.get_client() as client:
                return await client.exists(full_key) > 0
        except Exception as e:
            logger.warning("Cache exists check failed for key %s: %s", full_key, e)
            return False

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[R]],
        ttl: int | timedelta = DEFAULT_TTL,
        tenant_id: str | None = None,
    ) -> R | None:
        """Get from cache or compute and cache the value.

        Args:
            key: Cache key
            factory: Async function to compute the value if not cached
            ttl: Time to live
            tenant_id: Optional tenant ID for scoping

        Returns:
            Cached or computed value
        """
        cached = await self.get(key, tenant_id)
        if cached is not None:
            return cached

        # Compute the value
        value = await factory()
        if value is not None:
            await self.set(key, value, ttl, tenant_id)
        return value

    async def increment(
        self,
        key: str,
        amount: int = 1,
        tenant_id: str | None = None,
    ) -> int | None:
        """Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by
            tenant_id: Optional tenant ID for scoping

        Returns:
            New value after increment, or None on error
        """
        full_key = self._build_key(key, tenant_id)
        try:
            async with redis_pool.get_client() as client:
                return await client.incrby(full_key, amount)
        except Exception as e:
            logger.warning("Cache increment failed for key %s: %s", full_key, e)
            return None

    async def get_ttl(self, key: str, tenant_id: str | None = None) -> int | None:
        """Get remaining TTL for a key.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for scoping

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist, None on error
        """
        full_key = self._build_key(key, tenant_id)
        try:
            async with redis_pool.get_client() as client:
                return await client.ttl(full_key)
        except Exception as e:
            logger.warning("Cache get_ttl failed for key %s: %s", full_key, e)
            return None

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | timedelta = DEFAULT_TTL,
        tenant_id: str | None = None,
    ) -> bool:
        """Set multiple key-value pairs.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live (applied to all keys)
            tenant_id: Optional tenant ID for scoping

        Returns:
            True if all successful, False otherwise
        """
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())

        try:
            async with redis_pool.get_client() as client:
                pipe = client.pipeline()
                for key, value in mapping.items():
                    full_key = self._build_key(key, tenant_id)
                    serialized = self._serializer.serialize(value)
                    pipe.set(full_key, serialized, ex=ttl)
                await pipe.execute()
            return True
        except Exception as e:
            logger.warning("Cache set_many failed: %s", e)
            return False

    async def get_many(
        self,
        keys: list[str],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get multiple values at once.

        Args:
            keys: List of cache keys
            tenant_id: Optional tenant ID for scoping

        Returns:
            Dictionary of key-value pairs (missing keys omitted)
        """
        if not keys:
            return {}

        full_keys = [self._build_key(k, tenant_id) for k in keys]
        try:
            async with redis_pool.get_client() as client:
                values = await client.mget(full_keys)

            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    result[key] = self._serializer.deserialize(value)
            return result
        except Exception as e:
            logger.warning("Cache get_many failed: %s", e)
            return {}

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics from Redis.

        Returns:
            Dictionary with cache stats including memory usage, key count, hit/miss info
        """
        try:
            async with redis_pool.get_client() as client:
                info = await client.info("stats")
                memory = await client.info("memory")

                # Count keys with our prefix
                key_count = 0
                cursor = 0
                while True:
                    cursor, keys = await client.scan(
                        cursor=cursor,
                        match=f"{self._prefix}:*",
                        count=1000,
                    )
                    key_count += len(keys)
                    if cursor == 0:
                        break

                return {
                    "prefix": self._prefix,
                    "key_count": key_count,
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "hit_rate": (
                        info.get("keyspace_hits", 0)
                        / max(
                            info.get("keyspace_hits", 0)
                            + info.get("keyspace_misses", 0),
                            1,
                        )
                        * 100
                    ),
                    "memory_used_bytes": memory.get("used_memory", 0),
                    "memory_used_human": memory.get("used_memory_human", "N/A"),
                }
        except Exception as e:
            logger.warning("Cache stats failed: %s", e)
            return {"error": str(e)}


@dataclass
class CacheStats:
    """Cache statistics container."""

    hits: int = 0
    misses: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.misses += 1


# In-memory stats for decorated functions
_decorator_stats: dict[str, CacheStats] = {}


def _make_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key from function arguments."""
    # Create a deterministic hash of the arguments
    key_parts = [func_name]

    # Add positional args
    for arg in args:
        if isinstance(arg, BaseModel):
            key_parts.append(arg.model_dump_json())
        else:
            key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, BaseModel):
            key_parts.append(f"{k}={v.model_dump_json()}")
        else:
            key_parts.append(f"{k}={v}")

    key_str = ":".join(key_parts)

    # Hash if too long
    if len(key_str) > 200:
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        return f"{prefix}:{func_name}:{key_hash}"

    return f"{prefix}:{key_str}"


def _extract_tenant_id(
    func: Callable,
    tenant_id_param: str | None,
    args: tuple,
    kwargs: dict,
) -> str | None:
    """Extract tenant_id from function arguments (positional or keyword).

    Args:
        func: The decorated function
        tenant_id_param: Name of the tenant_id parameter
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        The tenant_id value or None
    """
    if not tenant_id_param:
        return None

    # Check kwargs first
    if tenant_id_param in kwargs:
        return kwargs[tenant_id_param]

    # Check positional args using function signature
    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if tenant_id_param in params:
            idx = params.index(tenant_id_param)
            if idx < len(args):
                return args[idx]
    except (ValueError, TypeError):
        pass

    return None


def cached(
    ttl: int | timedelta = DEFAULT_TTL,
    prefix: str = "fn",
    tenant_id_param: str | None = "tenant_id",
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator for caching async function results.

    Args:
        ttl: Cache TTL in seconds or timedelta
        prefix: Key prefix for this function's cache
        tenant_id_param: Name of the parameter containing tenant_id (None to disable)

    Usage:
        @cached(ttl=60, prefix="employees")
        async def get_employee(employee_id: str, tenant_id: str) -> dict:
            ...

        # Tenant-aware caching
        @cached(ttl=300, prefix="stats", tenant_id_param="tenant_id")
        async def get_stats(tenant_id: str) -> dict:
            ...

        # No tenant isolation
        @cached(ttl=3600, prefix="config", tenant_id_param=None)
        async def get_global_config() -> dict:
            ...
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        # Initialize stats for this function
        stats_key = f"{prefix}:{func.__name__}"
        _decorator_stats[stats_key] = CacheStats()

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Extract tenant_id from args or kwargs
            tenant_id = _extract_tenant_id(func, tenant_id_param, args, kwargs)

            # Generate cache key
            cache_key = _make_cache_key(prefix, func.__name__, args, kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key, tenant_id)
            if cached_value is not None:
                logger.debug("Cache hit for %s", cache_key)
                _decorator_stats[stats_key].record_hit()
                return cached_value

            # Cache miss - compute value
            logger.debug("Cache miss for %s", cache_key)
            _decorator_stats[stats_key].record_miss()
            result = await func(*args, **kwargs)

            # Cache the result
            if result is not None:
                await cache.set(cache_key, result, ttl, tenant_id)

            return result

        # Attach cache invalidation helper
        async def invalidate(*args: P.args, **kwargs: P.kwargs) -> bool:
            """Invalidate the cache for these specific arguments."""
            tenant_id = _extract_tenant_id(func, tenant_id_param, args, kwargs)
            cache_key = _make_cache_key(prefix, func.__name__, args, kwargs)
            return await cache.delete(cache_key, tenant_id)

        def get_stats() -> CacheStats:
            """Get cache stats for this function."""
            return _decorator_stats[stats_key]

        wrapper.invalidate = invalidate  # type: ignore[attr-defined]
        wrapper.get_stats = get_stats  # type: ignore[attr-defined]
        wrapper.cache_prefix = prefix  # type: ignore[attr-defined]

        return wrapper

    return decorator


def cache_invalidate(prefix: str, tenant_id: str | None = None) -> Callable:
    """Decorator to invalidate cache after a function executes.

    Useful for write operations that should clear related caches.

    Args:
        prefix: Cache prefix pattern to invalidate (supports wildcards)
        tenant_id: Specific tenant to invalidate (or None for all)

    Usage:
        @cache_invalidate(prefix="employees:*")
        async def update_employee(employee_id: str, data: dict) -> Employee:
            ...
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = await func(*args, **kwargs)
            # Invalidate after successful execution
            await cache.delete_pattern(prefix, tenant_id)
            return result

        return wrapper

    return decorator


def get_all_cache_stats() -> dict[str, dict[str, Any]]:
    """Get cache statistics for all decorated functions.

    Returns:
        Dictionary mapping function keys to their stats
    """
    return {
        key: {
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_rate": round(stats.hit_rate, 2),
        }
        for key, stats in _decorator_stats.items()
    }


# Global cache instance
cache = Cache()
