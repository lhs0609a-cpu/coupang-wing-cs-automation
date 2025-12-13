"""
Caching System
캐싱 시스템
"""
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
import json
import hashlib
from loguru import logger


class InMemoryCache:
    """
    Simple in-memory cache with TTL support
    TTL을 지원하는 간단한 인메모리 캐시
    """

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: Default time-to-live in seconds (기본 만료 시간, 초)
        """
        self.cache = {}
        self.expiry = {}
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        # Check if key exists and not expired
        if key in self.cache:
            if key in self.expiry:
                if datetime.utcnow() > self.expiry[key]:
                    # Expired
                    self.delete(key)
                    self.stats["misses"] += 1
                    return None

            self.stats["hits"] += 1
            logger.debug(f"Cache HIT: {key}")
            return self.cache[key]

        self.stats["misses"] += 1
        logger.debug(f"Cache MISS: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """캐시에 값 저장"""
        self.cache[key] = value

        if ttl is None:
            ttl = self.default_ttl

        if ttl > 0:
            self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)

        self.stats["sets"] += 1
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")

    def delete(self, key: str):
        """캐시에서 삭제"""
        if key in self.cache:
            del self.cache[key]
        if key in self.expiry:
            del self.expiry[key]
        self.stats["deletes"] += 1
        logger.debug(f"Cache DELETE: {key}")

    def clear(self):
        """모든 캐시 삭제"""
        count = len(self.cache)
        self.cache.clear()
        self.expiry.clear()
        logger.info(f"Cache cleared: {count} items removed")

    def get_stats(self) -> dict:
        """캐시 통계"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 4),
            "size": len(self.cache)
        }

    def cleanup_expired(self):
        """만료된 항목 정리"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, expiry_time in self.expiry.items()
            if now > expiry_time
        ]

        for key in expired_keys:
            self.delete(key)

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


# Global cache instance
_cache: Optional[InMemoryCache] = None


def get_cache() -> InMemoryCache:
    """Get global cache instance"""
    global _cache
    if _cache is None:
        _cache = InMemoryCache(default_ttl=300)  # 5 minutes default
    return _cache


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    함수 인자로부터 캐시 키 생성
    """
    # Create a string representation of args and kwargs
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

    key_string = ":".join(key_parts)

    # Hash for consistent length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    함수 결과를 캐싱하는 데코레이터

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key

    Example:
        @cached(ttl=600, key_prefix="user")
        def get_user(user_id: int):
            return db.query(User).get(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            func_name = func.__name__
            args_key = cache_key(*args, **kwargs)
            full_key = f"{key_prefix}:{func_name}:{args_key}" if key_prefix else f"{func_name}:{args_key}"

            # Try to get from cache
            result = cache.get(full_key)

            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(full_key, result, ttl=ttl)

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: get_cache().clear()
        wrapper.cache_stats = lambda: get_cache().get_stats()

        return wrapper

    return decorator


def cache_invalidate(key_prefix: str):
    """
    Invalidate cache entries with given prefix
    특정 prefix를 가진 캐시 항목 무효화
    """
    cache = get_cache()

    # Find and delete matching keys
    keys_to_delete = [
        key for key in cache.cache.keys()
        if key.startswith(key_prefix)
    ]

    for key in keys_to_delete:
        cache.delete(key)

    logger.info(f"Invalidated {len(keys_to_delete)} cache entries with prefix '{key_prefix}'")
    return len(keys_to_delete)


# Specialized cache decorators

def cache_template(ttl: int = 3600):
    """Cache template data (1 hour default)"""
    return cached(ttl=ttl, key_prefix="template")


def cache_inquiry(ttl: int = 300):
    """Cache inquiry data (5 minutes default)"""
    return cached(ttl=ttl, key_prefix="inquiry")


def cache_response(ttl: int = 300):
    """Cache response data (5 minutes default)"""
    return cached(ttl=ttl, key_prefix="response")


def cache_stats(ttl: int = 60):
    """Cache statistics (1 minute default)"""
    return cached(ttl=ttl, key_prefix="stats")


# Cache warming utilities

async def warm_cache():
    """
    Warm up cache with frequently accessed data
    자주 접근하는 데이터로 캐시 예열
    """
    logger.info("Starting cache warm-up...")

    # This would be implemented based on your most frequently accessed data
    # For example:
    # - Popular templates
    # - Recent inquiries
    # - System statistics

    logger.info("Cache warm-up completed")


# Background task for cleanup

async def cache_cleanup_task():
    """Background task to clean up expired cache entries"""
    import asyncio

    cache = get_cache()

    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            cache.cleanup_expired()
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")


# Response caching for FastAPI

class ResponseCache:
    """
    HTTP response caching
    HTTP 응답 캐싱
    """

    def __init__(self, ttl: int = 60):
        self.cache = get_cache()
        self.ttl = ttl

    def get_response_key(self, method: str, path: str, query_params: str) -> str:
        """Generate cache key for HTTP response"""
        return f"response:{method}:{path}:{query_params}"

    def get(self, method: str, path: str, query_params: str) -> Optional[dict]:
        """Get cached response"""
        key = self.get_response_key(method, path, query_params)
        return self.cache.get(key)

    def set(self, method: str, path: str, query_params: str, response: dict):
        """Cache response"""
        key = self.get_response_key(method, path, query_params)
        self.cache.set(key, response, ttl=self.ttl)

    def invalidate(self, path_prefix: str):
        """Invalidate responses for path prefix"""
        cache_invalidate(f"response:GET:{path_prefix}")
        cache_invalidate(f"response:POST:{path_prefix}")


def cache_response_decorator(ttl: int = 60):
    """
    Decorator to cache FastAPI endpoint responses

    Example:
        @app.get("/api/stats")
        @cache_response_decorator(ttl=120)
        async def get_stats():
            return compute_expensive_stats()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import Request

            # Get request from kwargs
            request = kwargs.get('request') or (args[0] if args and isinstance(args[0], Request) else None)

            if request:
                response_cache = ResponseCache(ttl=ttl)

                # Try to get cached response
                cached_response = response_cache.get(
                    request.method,
                    request.url.path,
                    str(request.query_params)
                )

                if cached_response:
                    logger.debug(f"Serving cached response for {request.url.path}")
                    return cached_response

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if request:
                response_cache.set(
                    request.method,
                    request.url.path,
                    str(request.query_params),
                    result
                )

            return result

        return wrapper

    return decorator
