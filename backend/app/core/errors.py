from typing import Any, Optional


class ApplicationError(Exception):
    """Base domain exception for DealFlow360.
    Subclasses in future phases (e.g. ValidationError, RuleError) can inherit from this.
    """

    def __init__(
        self,
        message: str = "An application error occurred",
        code: str = "APPLICATION_ERROR",
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(ApplicationError):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class ConflictError(ApplicationError):
    def __init__(self, message: str = "Resource already exists", details: Optional[Any] = None):
        super().__init__(message=message, code="CONFLICT", status_code=409, details=details)


class ValidationError(ApplicationError):
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class PermissionDeniedError(ApplicationError):
    def __init__(self, message: str = "Permission denied", details: Optional[Any] = None):
        super().__init__(message=message, code="PERMISSION_DENIED", status_code=403, details=details)


ForbiddenError = PermissionDeniedError
