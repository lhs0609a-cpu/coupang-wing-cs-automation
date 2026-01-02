"""
Custom exceptions for the application
"""


class BaseAppException(Exception):
    """Base exception for all application exceptions"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(BaseAppException):
    """Resource not found"""
    pass


class ValidationError(BaseAppException):
    """Validation error"""
    pass


class APIError(BaseAppException):
    """External API error"""
    pass


class DatabaseError(BaseAppException):
    """Database operation error"""
    pass


class AuthenticationError(BaseAppException):
    """Authentication failed"""
    pass
