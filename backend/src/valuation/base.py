"""Base classes for valuation methods."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Type

from src.config import ValuationConfig
from src.database.loader import DataLoader
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

    def _apply_company_adjustments(
        self, base_value: "Decimal", value_label: str = "base value"
    ) -> tuple["Decimal", "Decimal", list[str]]:
        """Apply company-specific adjustments and add audit step.

        Args:
            base_value: The value to apply adjustments to.
            value_label: Label for the base value in audit trail (e.g., "base value", "market-adjusted value").

        Returns:
            Tuple of (final_value, combined_factor, adjustment_derivation_parts).
        """
        from decimal import Decimal
        from src.utils.math_utils import format_currency, round_decimal

        final_value = base_value
        combined_factor = Decimal("1.0")
        adjustment_derivation_parts: list[str] = []

        if self.company_data.adjustments:
            adjustment_list = []

            for adj in self.company_data.adjustments:
                combined_factor *= adj.factor
                pct_change = (adj.factor - 1) * 100
                sign = "+" if pct_change >= 0 else ""
                adjustment_list.append({
                    "name": adj.name,
                    "impact": f"{sign}{round_decimal(pct_change, 0)}%",
                    "reason": adj.reason,
                })
                adjustment_derivation_parts.append(
                    f"{adj.name} ({sign}{round_decimal(pct_change, 0)}%)"
                )

            final_value = base_value * combined_factor
            total_adjustment_pct = (combined_factor - 1) * 100
            total_sign = "+" if total_adjustment_pct >= 0 else ""

            self._add_step(
                description="Company-Specific Adjustments",
                inputs={
                    "type": "company_adjustments",
                    "adjustments": adjustment_list,
                    "total_adjustment": f"{total_sign}{round_decimal(total_adjustment_pct, 1)}%",
                },
                calculation=(
                    f"Combined adjustment of {total_sign}{round_decimal(total_adjustment_pct, 1)}% "
                    f"applied to {value_label}."
                ),
                result=f"Adjusted valuation: {format_currency(final_value)}",
            )
        else:
            self._add_step(
                description="Company-Specific Adjustments",
                inputs={
                    "type": "company_adjustments",
                    "adjustments": [],
                    "total_adjustment": "0%",
                },
                calculation="No company-specific adjustments applied.",
                result=f"Adjusted valuation: {format_currency(final_value)}",
            )

        return final_value, combined_factor, adjustment_derivation_parts

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
