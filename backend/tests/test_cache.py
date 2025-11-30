"""Tests for Redis caching layer."""

import pytest

from app.core.cache import Cache, CacheSerializer, _make_cache_key, cache, cached
from app.core.redis import redis_pool


async def redis_available() -> bool:
    """Check if Redis is available for testing."""
    return await redis_pool.ping()


class TestCacheSerializer:
    """Tests for cache serialization."""

    def test_serialize_dict(self) -> None:
        """Test serializing a dictionary."""
        serializer = CacheSerializer()
        data = {"name": "John", "age": 30}
        result = serializer.serialize(data)
        assert result == '{"name": "John", "age": 30}'

    def test_serialize_list(self) -> None:
        """Test serializing a list."""
        serializer = CacheSerializer()
        data = [1, 2, 3, "four"]
        result = serializer.serialize(data)
        assert result == '[1, 2, 3, "four"]'

    def test_deserialize_dict(self) -> None:
        """Test deserializing a dictionary."""
        serializer = CacheSerializer()
        data = '{"name": "John", "age": 30}'
        result = serializer.deserialize(data)
        assert result == {"name": "John", "age": 30}

    def test_deserialize_none(self) -> None:
        """Test deserializing None."""
        serializer = CacheSerializer()
        result = serializer.deserialize(None)
        assert result is None


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_build_key_without_tenant(self) -> None:
        """Test building a key without tenant ID."""
        c = Cache(prefix="test")
        key = c._build_key("user:123")
        assert key == "test:user:123"

    def test_build_key_with_tenant(self) -> None:
        """Test building a key with tenant ID."""
        c = Cache(prefix="test")
        key = c._build_key("user:123", tenant_id="tenant-abc")
        assert key == "test:tenant-abc:user:123"

    def test_make_cache_key_simple(self) -> None:
        """Test generating cache key from function args."""
        key = _make_cache_key("fn", "get_user", ("123",), {})
        assert key == "fn:get_user:123"

    def test_make_cache_key_with_kwargs(self) -> None:
        """Test generating cache key with kwargs."""
        key = _make_cache_key("fn", "get_user", (), {"user_id": "123", "active": True})
        assert "active=True" in key
        assert "user_id=123" in key

    def test_make_cache_key_long_args_hashed(self) -> None:
        """Test that long keys are hashed."""
        long_arg = "x" * 300
        key = _make_cache_key("fn", "get_data", (long_arg,), {})
        assert len(key) < 250
        assert "get_data:" in key


@pytest.mark.asyncio
class TestCacheOperations:
    """Tests for cache operations (require Redis)."""

    async def test_set_and_get(self) -> None:
        """Test basic set and get."""
        if not await redis_available():
            pytest.skip("Redis not available")

        test_key = "test:set_get"
        test_value = {"name": "Test", "count": 42}

        await cache.set(test_key, test_value, ttl=10)
        result = await cache.get(test_key)

        assert result == test_value

        # Cleanup
        await cache.delete(test_key)

    async def test_get_nonexistent(self) -> None:
        """Test getting a nonexistent key."""
        result = await cache.get("nonexistent:key:12345")
        assert result is None

    async def test_delete(self) -> None:
        """Test deleting a key."""
        if not await redis_available():
            pytest.skip("Redis not available")

        test_key = "test:delete"
        await cache.set(test_key, "value", ttl=10)

        deleted = await cache.delete(test_key)
        assert deleted is True

        result = await cache.get(test_key)
        assert result is None

    async def test_exists(self) -> None:
        """Test checking if key exists."""
        if not await redis_available():
            pytest.skip("Redis not available")

        test_key = "test:exists"

        # Should not exist initially
        assert await cache.exists(test_key) is False

        await cache.set(test_key, "value", ttl=10)
        assert await cache.exists(test_key) is True

        await cache.delete(test_key)
        assert await cache.exists(test_key) is False

    async def test_tenant_isolation(self) -> None:
        """Test that tenant keys are isolated."""
        if not await redis_available():
            pytest.skip("Redis not available")

        key = "user:123"
        tenant1 = "tenant-1"
        tenant2 = "tenant-2"

        await cache.set(key, {"tenant": 1}, ttl=10, tenant_id=tenant1)
        await cache.set(key, {"tenant": 2}, ttl=10, tenant_id=tenant2)

        result1 = await cache.get(key, tenant_id=tenant1)
        result2 = await cache.get(key, tenant_id=tenant2)

        assert result1 == {"tenant": 1}
        assert result2 == {"tenant": 2}

        # Cleanup
        await cache.delete(key, tenant_id=tenant1)
        await cache.delete(key, tenant_id=tenant2)

    async def test_get_or_set(self) -> None:
        """Test get_or_set pattern."""
        if not await redis_available():
            pytest.skip("Redis not available")

        test_key = "test:get_or_set"
        call_count = 0

        async def factory() -> dict:
            nonlocal call_count
            call_count += 1
            return {"computed": True}

        # First call should compute
        result1 = await cache.get_or_set(test_key, factory, ttl=10)
        assert result1 == {"computed": True}
        assert call_count == 1

        # Second call should use cache
        result2 = await cache.get_or_set(test_key, factory, ttl=10)
        assert result2 == {"computed": True}
        assert call_count == 1  # Factory not called again

        # Cleanup
        await cache.delete(test_key)

    async def test_increment(self) -> None:
        """Test counter increment."""
        if not await redis_available():
            pytest.skip("Redis not available")

        test_key = "test:counter"

        # Set initial value
        await cache.set(test_key, 0, ttl=10)

        # Increment
        result = await cache.increment(test_key, 5)
        assert result == 5

        result = await cache.increment(test_key, 3)
        assert result == 8

        # Cleanup
        await cache.delete(test_key)

    async def test_set_many_get_many(self) -> None:
        """Test batch operations."""
        if not await redis_available():
            pytest.skip("Redis not available")

        mapping = {
            "batch:1": {"id": 1},
            "batch:2": {"id": 2},
            "batch:3": {"id": 3},
        }

        await cache.set_many(mapping, ttl=10)

        results = await cache.get_many(["batch:1", "batch:2", "batch:3", "batch:999"])

        assert results["batch:1"] == {"id": 1}
        assert results["batch:2"] == {"id": 2}
        assert results["batch:3"] == {"id": 3}
        assert "batch:999" not in results

        # Cleanup
        for key in mapping:
            await cache.delete(key)


@pytest.mark.asyncio
class TestCachedDecorator:
    """Tests for the @cached decorator."""

    async def test_cached_function(self) -> None:
        """Test basic function caching."""
        if not await redis_available():
            pytest.skip("Redis not available")

        call_count = 0

        @cached(ttl=10, prefix="test_cached")
        async def get_data(item_id: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"id": item_id, "data": "value"}

        # First call - cache miss
        result1 = await get_data("123")
        assert result1 == {"id": "123", "data": "value"}
        assert call_count == 1

        # Second call - cache hit
        result2 = await get_data("123")
        assert result2 == {"id": "123", "data": "value"}
        assert call_count == 1  # Not called again

        # Different arg - cache miss
        result3 = await get_data("456")
        assert result3 == {"id": "456", "data": "value"}
        assert call_count == 2

        # Cleanup using invalidate
        await get_data.invalidate("123")
        await get_data.invalidate("456")

    async def test_cached_with_invalidate(self) -> None:
        """Test cache invalidation."""
        if not await redis_available():
            pytest.skip("Redis not available")

        call_count = 0

        @cached(ttl=10, prefix="test_invalidate")
        async def get_item(item_id: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"id": item_id}

        # Populate cache
        await get_item("abc")
        assert call_count == 1

        # Invalidate
        await get_item.invalidate("abc")

        # Should recompute
        await get_item("abc")
        assert call_count == 2

        # Cleanup
        await get_item.invalidate("abc")
