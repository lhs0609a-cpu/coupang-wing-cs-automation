"""
Error Handling Tests
에러 핸들링 테스트
"""
import pytest
from app.core.errors import (
    ValidationException,
    NotFoundException,
    UnauthorizedException,
    ErrorCode
)


@pytest.mark.unit
def test_not_found_error_format(client):
    """Test that 404 errors return standardized format"""
    response = client.get("/api/inquiries/999999")

    assert response.status_code == 404
    data = response.json()

    # Check standard error format
    assert "error" in data
    assert data["error"] is True
    assert "error_code" in data
    assert "message" in data
    assert "trace_id" in data
    assert "timestamp" in data


@pytest.mark.unit
def test_validation_error_format(client):
    """Test validation error response format"""
    # Send invalid data
    response = client.post(
        "/api/inquiries",
        json={"invalid": "data"}  # Missing required fields
    )

    assert response.status_code == 422
    data = response.json()

    assert data["error"] is True
    assert data["error_code"] == ErrorCode.VALIDATION_ERROR.value
    assert "details" in data
    assert "errors" in data["details"]


@pytest.mark.unit
def test_exception_classes():
    """Test custom exception classes"""
    # Test ValidationException
    exc = ValidationException("Invalid input", details={"field": "email"})
    assert exc.error_code == ErrorCode.VALIDATION_ERROR
    assert exc.status_code == 400
    assert "Invalid input" in str(exc)

    # Test NotFoundException
    exc = NotFoundException("Inquiry", 123)
    assert exc.error_code == ErrorCode.NOT_FOUND
    assert exc.status_code == 404
    assert exc.details["resource"] == "Inquiry"
    assert exc.details["id"] == "123"

    # Test UnauthorizedException
    exc = UnauthorizedException()
    assert exc.error_code == ErrorCode.UNAUTHORIZED
    assert exc.status_code == 401
