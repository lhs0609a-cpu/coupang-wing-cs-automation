"""
Caching System Tests
캐싱 시스템 테스트
"""
import pytest
import time
from app.core.cache import InMemoryCache, cached, cache_invalidate


@pytest.mark.unit
def test_cache_set_get():
    """Test basic cache set and get"""
    cache = InMemoryCache()

    cache.set("test_key", "test_value")
    value = cache.get("test_key")

    assert value == "test_value"


@pytest.mark.unit
def test_cache_expiry():
    """Test cache expiry (TTL)"""
    cache = InMemoryCache(default_ttl=1)

    cache.set("expiring_key", "value", ttl=1)

    # Should exist initially
    assert cache.get("expiring_key") == "value"

    # Wait for expiry
    time.sleep(1.1)

    # Should be None after expiry
    assert cache.get("expiring_key") is None


@pytest.mark.unit
def test_cache_delete():
    """Test cache deletion"""
    cache = InMemoryCache()

    cache.set("key_to_delete", "value")
    assert cache.get("key_to_delete") == "value"

    cache.delete("key_to_delete")
    assert cache.get("key_to_delete") is None


@pytest.mark.unit
def test_cache_stats():
    """Test cache statistics"""
    cache = InMemoryCache()

    # Generate some hits and misses
    cache.set("key1", "value1")
    cache.get("key1")  # Hit
    cache.get("key1")  # Hit
    cache.get("nonexistent")  # Miss

    stats = cache.get_stats()

    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["sets"] == 1
    assert stats["size"] == 1
    assert stats["hit_rate"] == 2/3


@pytest.mark.unit
def test_cached_decorator():
    """Test @cached decorator"""
    call_count = {"count": 0}

    @cached(ttl=60, key_prefix="test")
    def expensive_function(x):
        call_count["count"] += 1
        return x * 2

    # First call - should execute function
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_count["count"] == 1

    # Second call - should use cache
    result2 = expensive_function(5)
    assert result2 == 10
    assert call_count["count"] == 1  # Not incremented

    # Different argument - should execute function
    result3 = expensive_function(10)
    assert result3 == 20
    assert call_count["count"] == 2


@pytest.mark.unit
def test_cache_cleanup():
    """Test cache cleanup of expired entries"""
    cache = InMemoryCache(default_ttl=1)

    cache.set("key1", "value1", ttl=1)
    cache.set("key2", "value2", ttl=10)

    time.sleep(1.1)

    # Cleanup should remove key1 but keep key2
    cleaned = cache.cleanup_expired()
    assert cleaned == 1
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"


@pytest.mark.unit
def test_cache_invalidate():
    """Test cache invalidation by prefix"""
    from app.core.cache import get_cache

    cache = get_cache()
    cache.clear()

    # Set multiple keys with prefix
    cache.set("user:1", "data1")
    cache.set("user:2", "data2")
    cache.set("product:1", "data3")

    # Invalidate user keys
    invalidated = cache_invalidate("user:")

    assert invalidated == 2
    assert cache.get("user:1") is None
    assert cache.get("user:2") is None
    assert cache.get("product:1") == "data3"
