"""Tests for the token blacklist module."""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.token_blacklist import (
    BLACKLIST_PREFIX,
    TokenBlacklist,
    _hash_token,
    token_blacklist,
)


class TestHashToken:
    """Tests for the _hash_token function."""

    def test_hash_is_consistent(self) -> None:
        """Same token should produce same hash."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        hash1 = _hash_token(token)
        hash2 = _hash_token(token)
        assert hash1 == hash2

    def test_hash_is_64_chars(self) -> None:
        """SHA-256 hash should be 64 hex characters."""
        token = "test-token"
        token_hash = _hash_token(token)
        assert len(token_hash) == 64
        assert all(c in "0123456789abcdef" for c in token_hash)

    def test_different_tokens_different_hashes(self) -> None:
        """Different tokens should produce different hashes."""
        hash1 = _hash_token("token1")
        hash2 = _hash_token("token2")
        assert hash1 != hash2


class TestTokenBlacklist:
    """Tests for the TokenBlacklist class."""

    @pytest.fixture
    def blacklist(self) -> TokenBlacklist:
        """Create a fresh token blacklist instance."""
        return TokenBlacklist()

    def test_initial_state(self, blacklist: TokenBlacklist) -> None:
        """Blacklist should start disconnected."""
        assert not blacklist.is_connected
        assert blacklist._redis is None

    @pytest.mark.asyncio
    async def test_fail_open_is_revoked_when_redis_unavailable(
        self, blacklist: TokenBlacklist
    ) -> None:
        """is_revoked should return False when Redis is unavailable (fail-open)."""
        # Mock redis_pool to return None (simulates unavailable)
        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=None)
            result = await blacklist.is_revoked("some-token")
            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_token_returns_false_when_redis_unavailable(
        self, blacklist: TokenBlacklist
    ) -> None:
        """revoke_token should return False when Redis is unavailable."""
        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=None)
            expires_at = datetime.now(timezone.utc)
            result = await blacklist.revoke_token("some-token", expires_at)
            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_token_skips_expired_token(
        self, blacklist: TokenBlacklist
    ) -> None:
        """Should skip blacklisting already expired tokens."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.setex = AsyncMock()
        blacklist._redis = mock_redis

        # Token that expired in the past
        expires_at = datetime.fromtimestamp(time.time() - 100, tz=timezone.utc)

        result = await blacklist.revoke_token("expired-token", expires_at)
        assert result is True
        mock_redis.setex.assert_not_called()


class TestTokenBlacklistIntegration:
    """Integration tests with mock Redis."""

    @pytest.fixture
    def mock_redis(self) -> AsyncMock:
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.ping = AsyncMock(return_value=True)
        redis.setex = AsyncMock(return_value=True)
        redis.exists = AsyncMock(return_value=0)
        redis.get = AsyncMock(return_value=None)
        redis.aclose = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, mock_redis: AsyncMock) -> None:
        """Should successfully revoke a token."""
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()

            expires_at = datetime.fromtimestamp(time.time() + 3600, tz=timezone.utc)
            result = await blacklist.revoke_token("test-token", expires_at)

            assert result is True
            mock_redis.setex.assert_called_once()

            # Verify the key format
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            assert key.startswith(BLACKLIST_PREFIX)

    @pytest.mark.asyncio
    async def test_is_revoked_returns_true_for_blacklisted(
        self, mock_redis: AsyncMock
    ) -> None:
        """Should return True for blacklisted tokens."""
        mock_redis.exists = AsyncMock(return_value=1)
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()
            result = await blacklist.is_revoked("blacklisted-token")

            assert result is True

    @pytest.mark.asyncio
    async def test_is_revoked_returns_false_for_valid(
        self, mock_redis: AsyncMock
    ) -> None:
        """Should return False for non-blacklisted tokens."""
        mock_redis.exists = AsyncMock(return_value=0)
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()
            result = await blacklist.is_revoked("valid-token")

            assert result is False

    @pytest.mark.asyncio
    async def test_connection_error_fails_open(self, mock_redis: AsyncMock) -> None:
        """Should fail open on connection errors during is_revoked."""
        import redis.asyncio as aioredis

        mock_redis.exists = AsyncMock(
            side_effect=aioredis.ConnectionError("Connection lost")
        )
        blacklist = TokenBlacklist()
        blacklist._redis = mock_redis

        result = await blacklist.is_revoked("some-token")
        assert result is False  # Fail open

    @pytest.mark.asyncio
    async def test_timeout_error_fails_open(self, mock_redis: AsyncMock) -> None:
        """Should fail open on timeout errors during is_revoked."""
        import redis.asyncio as aioredis

        mock_redis.exists = AsyncMock(side_effect=aioredis.TimeoutError("Timeout"))
        blacklist = TokenBlacklist()
        blacklist._redis = mock_redis

        result = await blacklist.is_revoked("some-token")
        assert result is False  # Fail open


class TestUserTokenRevocation:
    """Tests for user-level token revocation."""

    @pytest.fixture
    def mock_redis(self) -> AsyncMock:
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.ping = AsyncMock(return_value=True)
        redis.setex = AsyncMock(return_value=True)
        redis.get = AsyncMock(return_value=None)
        redis.aclose = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_success(self, mock_redis: AsyncMock) -> None:
        """Should successfully revoke all user tokens."""
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()
            result = await blacklist.revoke_all_user_tokens("user-123")

            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            assert "user:revoked:user-123" in key

    @pytest.mark.asyncio
    async def test_is_user_tokens_revoked_before_revocation(
        self, mock_redis: AsyncMock
    ) -> None:
        """Tokens issued before revocation should be considered revoked."""
        # Simulate revocation happened at timestamp 1000
        mock_redis.get = AsyncMock(return_value="1000")
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()
            # Token issued at 900 (before revocation at 1000)
            result = await blacklist.is_user_tokens_revoked("user-123", 900)

            assert result is True

    @pytest.mark.asyncio
    async def test_is_user_tokens_revoked_after_revocation(
        self, mock_redis: AsyncMock
    ) -> None:
        """Tokens issued after revocation should NOT be considered revoked."""
        # Simulate revocation happened at timestamp 1000
        mock_redis.get = AsyncMock(return_value="1000")
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()
            # Token issued at 1100 (after revocation at 1000)
            result = await blacklist.is_user_tokens_revoked("user-123", 1100)

            assert result is False

    @pytest.mark.asyncio
    async def test_is_user_tokens_revoked_no_revocation(
        self, mock_redis: AsyncMock
    ) -> None:
        """Should return False if user has no revocation record."""
        mock_redis.get = AsyncMock(return_value=None)
        blacklist = TokenBlacklist()

        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=mock_redis)
            await blacklist.connect()
            result = await blacklist.is_user_tokens_revoked("user-123", 1000)

            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_fails_when_redis_unavailable(
        self,
    ) -> None:
        """Should return False when Redis is unavailable."""
        blacklist = TokenBlacklist()
        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=None)
            result = await blacklist.revoke_all_user_tokens("user-123")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_user_tokens_revoked_fails_open(
        self,
    ) -> None:
        """Should fail open when Redis is unavailable."""
        blacklist = TokenBlacklist()
        with patch("app.core.token_blacklist.redis_pool") as mock_pool:
            mock_pool.get_client_unsafe = AsyncMock(return_value=None)
            result = await blacklist.is_user_tokens_revoked("user-123", 1000)
            assert result is False


class TestGlobalInstance:
    """Tests for the global token_blacklist instance."""

    def test_global_instance_exists(self) -> None:
        """Global instance should be available."""
        assert token_blacklist is not None
        assert isinstance(token_blacklist, TokenBlacklist)
