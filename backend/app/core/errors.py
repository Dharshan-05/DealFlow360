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
