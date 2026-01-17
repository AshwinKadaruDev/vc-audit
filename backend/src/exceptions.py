"""Custom exceptions for VC Audit Tool."""

from typing import Any, Optional


class ValuationError(Exception):
    """Base exception for valuation errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class DataNotFoundError(ValuationError):
    """Raised when requested data is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class DataValidationError(ValuationError):
    """Raised when data fails validation."""

    def __init__(self, message: str, validation_errors: Optional[list[dict]] = None):
        super().__init__(
            message=message,
            details={"validation_errors": validation_errors or []},
        )


class DataLoadError(ValuationError):
    """Raised when data cannot be loaded from source."""

    def __init__(self, source: str, reason: str):
        super().__init__(
            message=f"Failed to load data from {source}: {reason}",
            details={"source": source, "reason": reason},
        )


class InsufficientDataError(ValuationError):
    """Raised when there is insufficient data for a calculation."""

    def __init__(self, method: str, missing_data: list[str]):
        super().__init__(
            message=f"Insufficient data for {method} method",
            details={"method": method, "missing_data": missing_data},
        )


class NoValidMethodsError(ValuationError):
    """Raised when no valuation methods can be executed."""

    def __init__(self, company_id: str, skip_reasons: dict[str, str]):
        super().__init__(
            message=f"No valid valuation methods for company {company_id}",
            details={"company_id": company_id, "skip_reasons": skip_reasons},
        )


class CalculationError(ValuationError):
    """Raised when a calculation fails."""

    def __init__(self, method: str, step: str, reason: str):
        super().__init__(
            message=f"Calculation failed in {method} at step '{step}': {reason}",
            details={"method": method, "step": step, "reason": reason},
        )
