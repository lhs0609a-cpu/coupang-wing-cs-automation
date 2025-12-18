"""
Rate Limiting Middleware
요청 제한 미들웨어
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
from loguru import logger


def add_cors_headers(response: Response) -> Response:
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response


class RateLimiter:
    """
    Rate limiter using sliding window algorithm
    슬라이딩 윈도우 알고리즘을 사용한 요청 제한기
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        self.limits = {
            'minute': requests_per_minute,
            'hour': requests_per_hour,
            'day': requests_per_day
        }

        # Store request timestamps per client
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())

        # Blocked clients (IP -> unblock_time)
        self.blocked: Dict[str, datetime] = {}

    def is_allowed(self, client_id: str) -> tuple[bool, Optional[Dict]]:
        """
        Check if request is allowed

        Returns:
            (allowed: bool, info: dict)
        """
        now = datetime.utcnow()

        # Check if blocked
        if client_id in self.blocked:
            if now < self.blocked[client_id]:
                retry_after = int((self.blocked[client_id] - now).total_seconds())
                return False, {
                    "reason": "blocked",
                    "retry_after_seconds": retry_after
                }
            else:
                # Unblock
                del self.blocked[client_id]

        # Clean old requests
        self._clean_old_requests(client_id, now)

        # Get request counts
        minute_count = self._count_requests(client_id, now, minutes=1)
        hour_count = self._count_requests(client_id, now, minutes=60)
        day_count = self._count_requests(client_id, now, minutes=1440)

        # Check limits
        if minute_count >= self.limits['minute']:
            self._block_client(client_id, minutes=1)
            return False, {
                "reason": "rate_limit_minute",
                "limit": self.limits['minute'],
                "window": "1 minute",
                "retry_after_seconds": 60
            }

        if hour_count >= self.limits['hour']:
            self._block_client(client_id, minutes=5)
            return False, {
                "reason": "rate_limit_hour",
                "limit": self.limits['hour'],
                "window": "1 hour",
                "retry_after_seconds": 300
            }

        if day_count >= self.limits['day']:
            self._block_client(client_id, minutes=30)
            return False, {
                "reason": "rate_limit_day",
                "limit": self.limits['day'],
                "window": "1 day",
                "retry_after_seconds": 1800
            }

        # Record request
        self.requests[client_id].append(now)

        return True, {
            "remaining_minute": self.limits['minute'] - minute_count - 1,
            "remaining_hour": self.limits['hour'] - hour_count - 1,
            "remaining_day": self.limits['day'] - day_count - 1
        }

    def _clean_old_requests(self, client_id: str, now: datetime):
        """Remove requests older than 24 hours"""
        cutoff = now - timedelta(days=1)

        while self.requests[client_id] and self.requests[client_id][0] < cutoff:
            self.requests[client_id].popleft()

    def _count_requests(self, client_id: str, now: datetime, minutes: int) -> int:
        """Count requests in the last N minutes"""
        cutoff = now - timedelta(minutes=minutes)
        return sum(1 for ts in self.requests[client_id] if ts >= cutoff)

    def _block_client(self, client_id: str, minutes: int):
        """Block client for N minutes"""
        self.blocked[client_id] = datetime.utcnow() + timedelta(minutes=minutes)
        logger.warning(f"Rate limit: Blocked client {client_id} for {minutes} minutes")

    def get_stats(self, client_id: str) -> Dict:
        """Get rate limit stats for client"""
        now = datetime.utcnow()
        self._clean_old_requests(client_id, now)

        return {
            "requests_last_minute": self._count_requests(client_id, now, 1),
            "requests_last_hour": self._count_requests(client_id, now, 60),
            "requests_last_day": self._count_requests(client_id, now, 1440),
            "is_blocked": client_id in self.blocked,
            "limits": self.limits
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.rate_limiter = RateLimiter(**kwargs)

        # Paths to exclude from rate limiting
        self.excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/promotion/progress",  # Progress polling endpoint
            "/api/automation/stats",    # Dashboard stats polling
            "/api/system/stats",        # System stats polling
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)

        # Check rate limit
        allowed, info = self.rate_limiter.is_allowed(client_id)

        if not allowed:
            # Track in monitoring
            from ..services.monitoring import get_monitor
            monitor = get_monitor()
            monitor.log_user_action(
                user_id=client_id,
                action="rate_limit_exceeded",
                path=request.url.path,
                reason=info.get("reason")
            )

            # Return response directly with CORS headers instead of raising exception
            retry_after = info.get("retry_after_seconds", 60)
            response = JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "error_code": "ERR_1500",
                    "message": "Rate limit exceeded",
                    "details": {"retry_after_seconds": retry_after}
                }
            )
            response.headers["Retry-After"] = str(retry_after)
            return add_cors_headers(response)

        # Add rate limit headers to response
        response = await call_next(request)

        if info and "remaining_minute" in info:
            response.headers["X-RateLimit-Limit-Minute"] = str(self.rate_limiter.limits['minute'])
            response.headers["X-RateLimit-Remaining-Minute"] = str(info['remaining_minute'])
            response.headers["X-RateLimit-Limit-Hour"] = str(self.rate_limiter.limits['hour'])
            response.headers["X-RateLimit-Remaining-Hour"] = str(info['remaining_hour'])

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Use IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP 화이트리스트 미들웨어"""

    def __init__(self, app, whitelist: Optional[list] = None):
        super().__init__(app)
        self.whitelist = set(whitelist or [])

        # Add localhost by default
        self.whitelist.update(["127.0.0.1", "localhost", "::1"])

    async def dispatch(self, request: Request, call_next):
        # Skip for health checks
        if request.url.path in ["/health", "/docs", "/redoc"]:
            return await call_next(request)

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(',')[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Check whitelist (empty whitelist = allow all)
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")

            # Return response directly with CORS headers instead of raising exception
            response = JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "error_code": "ERR_1104",
                    "message": "Access denied: IP not whitelisted",
                    "details": {}
                }
            )
            return add_cors_headers(response)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers (API 서버용 - CSP 완화)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"  # DENY -> SAMEORIGIN으로 완화
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # CSP 제거 - API 서버에서는 불필요하며 CORS를 방해할 수 있음
        # response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """요청 ID 추적 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        import uuid

        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        import time

        start_time = time.time()

        # Log request
        from ..services.monitoring import get_monitor
        monitor = get_monitor()

        monitor.log_api_request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            client=request.client.host if request.client else "unknown"
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            monitor.log_api_response(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_ms=duration_ms
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            monitor.log_api_response(
                method=request.method,
                url=str(request.url),
                status_code=500,
                duration_ms=duration_ms,
                error=str(e)
            )

            raise
