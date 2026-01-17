"""Base classes for valuation methods."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Type

from src.config import ValuationConfig
from src.data.loader import DataLoader
from src.models import (
    AuditStep,
    CompanyData,
    Confidence,
    MethodName,
    MethodResult,
    MethodSkipped,
)


class ValuationMethod(ABC):
    """Abstract base class for valuation methods.

    Each valuation method must:
    1. Check prerequisites to determine if it can run
    2. Execute the valuation with a detailed audit trail
    """

    method_name: MethodName

    def __init__(
        self,
        company_data: CompanyData,
        config: ValuationConfig,
        loader: DataLoader,
    ):
        self.company_data = company_data
        self.config = config
        self.loader = loader
        self._audit_steps: list[AuditStep] = []
        self._step_counter = 0
        self._warnings: list[str] = []

    def _add_step(
        self,
        description: str,
        inputs: Optional[dict[str, Any]] = None,
        calculation: Optional[str] = None,
        result: Optional[str] = None,
    ) -> None:
        """Add a step to the audit trail.

        Args:
            description: Human-readable description of the step.
            inputs: Dictionary of input values used in this step.
            calculation: Formula or calculation performed.
            result: Result of the calculation.
        """
        self._step_counter += 1
        self._audit_steps.append(
            AuditStep(
                step_number=self._step_counter,
                description=description,
                inputs=inputs or {},
                calculation=calculation,
                result=result,
            )
        )

    def _add_warning(self, warning: str) -> None:
        """Add a warning to the result.

        Args:
            warning: Warning message.
        """
        self._warnings.append(warning)

    @abstractmethod
    def check_prerequisites(self) -> Optional[str]:
        """Check if the method can be executed.

        Returns:
            None if prerequisites are met, otherwise a string
            explaining why the method cannot run.
        """
        pass

    @abstractmethod
    def execute(self) -> MethodResult:
        """Execute the valuation method.

        Should only be called after check_prerequisites returns None.

        Returns:
            MethodResult with value, confidence, and audit trail.
        """
        pass

    def run(self) -> MethodResult | MethodSkipped:
        """Run the method, checking prerequisites first.

        Returns:
            MethodResult if successful, MethodSkipped if prerequisites not met.
        """
        skip_reason = self.check_prerequisites()
        if skip_reason:
            return MethodSkipped(
                method=self.method_name,
                reason=skip_reason,
            )
        return self.execute()


class MethodRegistry:
    """Registry for valuation methods.

    Provides a decorator-based registration pattern for adding
    new valuation methods.
    """

    _methods: dict[MethodName, Type[ValuationMethod]] = {}

    @classmethod
    def register(cls, method_class: Type[ValuationMethod]) -> Type[ValuationMethod]:
        """Decorator to register a valuation method.

        Usage:
            @MethodRegistry.register
            class MyMethod(ValuationMethod):
                method_name = MethodName.MY_METHOD
                ...

        Args:
            method_class: The ValuationMethod subclass to register.

        Returns:
            The same class (unchanged).
        """
        if not hasattr(method_class, "method_name"):
            raise ValueError(
                f"Method class {method_class.__name__} must have method_name attribute"
            )
        cls._methods[method_class.method_name] = method_class
        return method_class

    @classmethod
    def get_methods(cls) -> dict[MethodName, Type[ValuationMethod]]:
        """Get all registered methods.

        Returns:
            Dict mapping MethodName to method class.
        """
        return cls._methods.copy()

    @classmethod
    def get_method(cls, name: MethodName) -> Optional[Type[ValuationMethod]]:
        """Get a specific method by name.

        Args:
            name: The MethodName to look up.

        Returns:
            The method class, or None if not found.
        """
        return cls._methods.get(name)

    @classmethod
    def create_all(
        cls,
        company_data: CompanyData,
        config: ValuationConfig,
        loader: DataLoader,
    ) -> list[ValuationMethod]:
        """Create instances of all registered methods.

        Args:
            company_data: Company data to value.
            config: Valuation configuration.
            loader: Data loader instance.

        Returns:
            List of instantiated ValuationMethod objects.
        """
        return [
            method_class(company_data, config, loader)
            for method_class in cls._methods.values()
        ]
