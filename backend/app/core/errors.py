"""
Standardized Error Handling System
표준화된 에러 핸들링 시스템
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from enum import Enum
from loguru import logger


class ErrorCode(str, Enum):
    """표준 에러 코드"""

    # General Errors (1000-1099)
    INTERNAL_SERVER_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    NOT_FOUND = "ERR_1002"
    ALREADY_EXISTS = "ERR_1003"
    INVALID_INPUT = "ERR_1004"

    # Authentication Errors (1100-1199)
    UNAUTHORIZED = "ERR_1100"
    INVALID_CREDENTIALS = "ERR_1101"
    TOKEN_EXPIRED = "ERR_1102"
    TOKEN_INVALID = "ERR_1103"
    PERMISSION_DENIED = "ERR_1104"

    # Database Errors (1200-1299)
    DB_CONNECTION_ERROR = "ERR_1200"
    DB_QUERY_ERROR = "ERR_1201"
    DB_CONSTRAINT_ERROR = "ERR_1202"

    # Business Logic Errors (1300-1399)
    INQUIRY_NOT_FOUND = "ERR_1300"
    RESPONSE_NOT_FOUND = "ERR_1301"
    TEMPLATE_NOT_FOUND = "ERR_1302"
    INVALID_STATUS = "ERR_1303"
    WORKFLOW_ERROR = "ERR_1304"

    # External Service Errors (1400-1499)
    OPENAI_ERROR = "ERR_1400"
    SELENIUM_ERROR = "ERR_1401"
    NETWORK_ERROR = "ERR_1402"
    WEBHOOK_DELIVERY_FAILED = "ERR_1403"

    # Rate Limiting Errors (1500-1599)
    RATE_LIMIT_EXCEEDED = "ERR_1500"
    QUOTA_EXCEEDED = "ERR_1501"

    # File/Storage Errors (1600-1699)
    FILE_NOT_FOUND = "ERR_1600"
    FILE_TOO_LARGE = "ERR_1601"
    INVALID_FILE_TYPE = "ERR_1602"
    STORAGE_ERROR = "ERR_1603"


class ErrorResponse(BaseModel):
    """표준 에러 응답 모델"""
    error: bool = True
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    timestamp: str


class AppException(Exception):
    """애플리케이션 기본 예외 클래스"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# Specific Exception Classes

class ValidationException(AppException):
    """입력 검증 예외"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class NotFoundException(AppException):
    """리소스 미발견 예외"""
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": str(resource_id)}
        )


class UnauthorizedException(AppException):
    """인증 실패 예외"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionDeniedException(AppException):
    """권한 부족 예외"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class DatabaseException(AppException):
    """데이터베이스 예외"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ErrorCode.DB_QUERY_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ExternalServiceException(AppException):
    """외부 서비스 예외"""
    def __init__(self, service: str, message: str):
        super().__init__(
            error_code=ErrorCode.NETWORK_ERROR,
            message=f"{service} error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class RateLimitException(AppException):
    """요청 제한 초과 예외"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after_seconds": retry_after}
        )


# Error Handlers

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """애플리케이션 예외 핸들러"""
    from datetime import datetime
    import uuid

    trace_id = str(uuid.uuid4())

    # Log error
    logger.error(
        f"[{trace_id}] {exc.error_code.value}: {exc.message} | "
        f"Path: {request.url.path} | Details: {exc.details}"
    )

    # Track in monitoring
    from ..services.monitoring import get_monitor
    monitor = get_monitor()
    monitor.log_exception(
        exception_type=exc.__class__.__name__,
        message=exc.message,
        error_code=exc.error_code.value,
        path=request.url.path,
        trace_id=trace_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """FastAPI 검증 예외 핸들러"""
    from datetime import datetime
    import uuid

    trace_id = str(uuid.uuid4())

    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"[{trace_id}] Validation error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "message": "Validation error",
            "details": {"errors": errors},
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP 예외 핸들러"""
    from datetime import datetime
    import uuid

    trace_id = str(uuid.uuid4())

    # Map HTTP status codes to error codes
    error_code_map = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.NOT_FOUND,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        503: ErrorCode.NETWORK_ERROR
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    logger.error(f"[{trace_id}] HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": error_code.value,
            "message": exc.detail,
            "details": {},
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 핸들러 (Catch-all)"""
    from datetime import datetime
    import uuid
    import traceback

    trace_id = str(uuid.uuid4())

    # Log full stack trace
    stack_trace = traceback.format_exc()
    logger.error(
        f"[{trace_id}] Unhandled exception: {exc.__class__.__name__}: {str(exc)}\n"
        f"Stack trace:\n{stack_trace}"
    )

    # Track in monitoring
    from ..services.monitoring import get_monitor
    monitor = get_monitor()
    monitor.log_exception(
        exception_type=exc.__class__.__name__,
        message=str(exc),
        stack_trace=stack_trace,
        path=request.url.path,
        trace_id=trace_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "Internal server error",
            "details": {"exception_type": exc.__class__.__name__},
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Helper functions

def raise_not_found(resource: str, resource_id: Any):
    """리소스 미발견 예외 발생"""
    raise NotFoundException(resource, resource_id)


def raise_validation_error(message: str, **kwargs):
    """검증 에러 발생"""
    raise ValidationException(message, details=kwargs)


def raise_permission_denied(message: str = None):
    """권한 부족 예외 발생"""
    raise PermissionDeniedException(message or "Permission denied")
