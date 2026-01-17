"""Valuation engine orchestrating all valuation methods."""

from datetime import date
from decimal import Decimal
from typing import Optional

from src.config import ValuationConfig, get_settings
from src.data.loader import DataLoader
from src.exceptions import NoValidMethodsError
from src.methods.base import MethodRegistry, ValuationMethod
from src.models import (
    CompanyData,
    Confidence,
    MethodComparisonData,
    MethodComparisonItem,
    MethodName,
    MethodResult,
    MethodSkipped,
    ValuationResult,
    ValuationSummary,
)
from src.utils.math_utils import format_currency, round_decimal

# Import methods to register them
from src.methods import last_round, comps  # noqa: F401


class ValuationEngine:
    """Orchestrates valuation methods and produces final results.

    The engine:
    1. Checks prerequisites for all methods
    2. Executes applicable methods
    3. Compares results across methods
    4. Generates summary and input hash
    """

    def __init__(
        self,
        loader: Optional[DataLoader] = None,
        config: Optional[ValuationConfig] = None,
    ):
        settings = get_settings()
        self.loader = loader or DataLoader(settings)
        self.config = config or settings.valuation_config

    def run(self, company_id: str) -> ValuationResult:
        """Run valuation for a company by ID.

        Args:
            company_id: Company identifier.

        Returns:
            ValuationResult with all method results and summary.

        Raises:
            DataNotFoundError: If company not found.
            NoValidMethodsError: If no methods can be executed.
        """
        company_data = self.loader.load_company(company_id)
        return self.run_with_data(company_data)

    def run_with_data(self, company_data: CompanyData) -> ValuationResult:
        """Run valuation with provided company data.

        Args:
            company_data: Complete company data for valuation.

        Returns:
            ValuationResult with all method results and summary.

        Raises:
            NoValidMethodsError: If no methods can be executed.
        """
        # Create method instances
        methods = MethodRegistry.create_all(company_data, self.config, self.loader)

        # Run all methods
        results: list[MethodResult] = []
        skipped: list[MethodSkipped] = []

        for method in methods:
            result = method.run()
            if isinstance(result, MethodResult):
                results.append(result)
            else:
                skipped.append(result)

        # Check if we have any valid results
        if not results:
            skip_reasons = {s.method.value: s.reason for s in skipped}
            raise NoValidMethodsError(company_data.company.id, skip_reasons)

        # Compare methods and generate analysis
        cross_analysis = self._compare_methods(results) if len(results) > 1 else None

        # Generate summary
        summary = self._summarize(results, cross_analysis)

        # Create config snapshot
        config_snapshot = self.config.model_dump()
        # Convert Decimal to string for JSON serialization
        for key, value in config_snapshot.items():
            if isinstance(value, Decimal):
                config_snapshot[key] = str(value)

        return ValuationResult(
            company_id=company_data.company.id,
            company_name=company_data.company.name,
            valuation_date=date.today(),
            summary=summary,
            method_results=results,
            skipped_methods=skipped,
            cross_method_analysis=cross_analysis,
            config_snapshot=config_snapshot,
        )

    def _compare_methods(self, results: list[MethodResult]) -> str:
        """Compare results across methods and generate analysis.

        Args:
            results: List of method results.

        Returns:
            Analysis string describing cross-method comparison.
        """
        if len(results) < 2:
            return ""

        values = {r.method.value: r.value for r in results}
        min_value = min(values.values())
        max_value = max(values.values())

        # Calculate spread
        if min_value > 0:
            spread = (max_value - min_value) / min_value
        else:
            spread = Decimal("0")

        # Find which methods produced which values
        min_method = [m for m, v in values.items() if v == min_value][0]
        max_method = [m for m, v in values.items() if v == max_value][0]

        analysis_parts = [
            f"Cross-method comparison: {len(results)} methods executed.",
            f"Value range: {format_currency(min_value)} ({min_method}) to "
            f"{format_currency(max_value)} ({max_method}).",
            f"Spread: {round_decimal(spread * 100, 1)}%.",
        ]

        # Add warning for high spread
        if spread > self.config.medium_confidence_spread:
            analysis_parts.append(
                "WARNING: High spread between methods suggests significant "
                "uncertainty in valuation."
            )
        elif spread > self.config.high_confidence_spread:
            analysis_parts.append(
                "Note: Moderate spread between methods. Consider weighting "
                "towards higher-confidence method."
            )
        else:
            analysis_parts.append(
                "Low spread indicates good agreement between methods."
            )

        return " ".join(analysis_parts)

    def _summarize(
        self,
        results: list[MethodResult],
        cross_analysis: Optional[str],
    ) -> ValuationSummary:
        """Generate executive summary from results.

        Args:
            results: List of method results.
            cross_analysis: Cross-method analysis string.

        Returns:
            ValuationSummary with primary value and confidence.
        """
        # Sort by confidence (highest first)
        confidence_order = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
        sorted_results = sorted(
            results, key=lambda r: confidence_order[r.confidence]
        )

        primary = sorted_results[0]

        # Calculate range if multiple methods
        if len(results) > 1:
            all_values = [r.value for r in results]
            value_range_low = min(all_values)
            value_range_high = max(all_values)
        else:
            value_range_low = None
            value_range_high = None

        # Determine overall confidence
        overall_confidence = self._calculate_overall_confidence(results)

        # Generate summary text
        summary_parts = [
            f"Primary valuation: {format_currency(primary.value)} ",
            f"(via {primary.method.value} method, {primary.confidence.value} confidence).",
        ]

        if len(results) > 1:
            other_methods = [r for r in results if r != primary]
            method_summaries = [
                f"{r.method.value}: {format_currency(r.value)}"
                for r in other_methods
            ]
            summary_parts.append(
                f" Supporting methods: {', '.join(method_summaries)}."
            )

        # Generate method comparison data and selection reason
        method_comparison, selection_reason = self._generate_method_comparison(
            results, primary
        )

        return ValuationSummary(
            primary_value=primary.value,
            primary_method=primary.method,
            value_range_low=value_range_low,
            value_range_high=value_range_high,
            overall_confidence=overall_confidence,
            summary_text="".join(summary_parts),
            selection_reason=selection_reason,
            method_comparison=method_comparison,
        )

    def _generate_method_comparison(
        self,
        results: list[MethodResult],
        primary: MethodResult,
    ) -> tuple[MethodComparisonData, str]:
        """Generate structured method comparison and selection reason.

        Args:
            results: List of method results.
            primary: The selected primary method result.

        Returns:
            Tuple of (MethodComparisonData, selection_reason string).
        """
        # Build method comparison items
        method_items = [
            MethodComparisonItem(
                method=r.method,
                value=r.value,
                confidence=r.confidence,
                is_primary=(r.method == primary.method),
            )
            for r in results
        ]

        # Calculate spread
        spread_percent: Optional[Decimal] = None
        spread_warning: Optional[str] = None

        if len(results) > 1:
            values = [r.value for r in results]
            min_val = min(values)
            max_val = max(values)
            if min_val > 0:
                spread_percent = round_decimal((max_val - min_val) / min_val * 100, 1)

                if spread_percent > self.config.medium_confidence_spread * 100:
                    spread_warning = (
                        f"{spread_percent}% spread between methods indicates "
                        "significant uncertainty in valuation."
                    )
                elif spread_percent > self.config.high_confidence_spread * 100:
                    spread_warning = (
                        f"{spread_percent}% spread between methods indicates "
                        "moderate uncertainty."
                    )

        # Generate selection steps
        selection_steps = self._generate_selection_steps(results, primary)

        # Generate plain-language selection reason
        selection_reason = self._generate_selection_reason(results, primary, spread_percent)

        return (
            MethodComparisonData(
                methods=method_items,
                spread_percent=spread_percent,
                spread_warning=spread_warning,
                selection_steps=selection_steps,
            ),
            selection_reason,
        )

    def _generate_selection_steps(
        self,
        results: list[MethodResult],
        primary: MethodResult,
    ) -> list[str]:
        """Generate step-by-step explanation of method selection.

        Args:
            results: List of method results.
            primary: The selected primary method result.

        Returns:
            List of selection step descriptions.
        """
        steps = []

        # Step 1: List applicable methods
        method_list = ", ".join(
            f"{self._method_display_name(r.method)}"
            for r in results
        )
        steps.append(f"Ran all applicable valuation methods: {method_list}")

        # Step 2: Assess confidence
        confidence_details = []
        for r in results:
            conf_detail = f"{self._method_display_name(r.method)}: {r.confidence.value.upper()}"
            if r.warnings:
                conf_detail += f" ({r.warnings[0][:50]}...)" if len(r.warnings[0]) > 50 else f" ({r.warnings[0]})"
            confidence_details.append(conf_detail)
        steps.append(f"Assessed confidence: {'; '.join(confidence_details)}")

        # Step 3: Selection result
        steps.append(
            f"Selected {self._method_display_name(primary.method)} as primary "
            f"({primary.confidence.value} confidence)"
        )

        return steps

    def _generate_selection_reason(
        self,
        results: list[MethodResult],
        primary: MethodResult,
        spread_percent: Optional[Decimal],
    ) -> str:
        """Generate plain-language explanation of why primary method was chosen.

        Args:
            results: List of method results.
            primary: The selected primary method result.
            spread_percent: Spread between methods as percentage.

        Returns:
            Plain-language selection reason.
        """
        if len(results) == 1:
            return (
                f"Only one valuation method was applicable. "
                f"{self._method_display_name(primary.method)} was used with "
                f"{primary.confidence.value} confidence."
            )

        # Multiple methods case
        confidence_order = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
        sorted_results = sorted(
            results, key=lambda r: confidence_order[r.confidence]
        )

        parts = [
            f"We used {len(results)} valuation methods. "
            f"{self._method_display_name(primary.method)} was selected as primary "
        ]

        # Explain why this method was chosen
        other_results = [r for r in sorted_results if r.method != primary.method]

        if all(r.confidence == primary.confidence for r in results):
            # Same confidence - explain the tiebreaker
            parts.append(
                f"because it provides more direct market evidence, even though "
                f"both methods have {primary.confidence.value} confidence."
            )
        elif primary.confidence != other_results[0].confidence:
            # Higher confidence
            other_conf = other_results[0].confidence.value
            parts.append(
                f"because it has higher confidence "
                f"({primary.confidence.value.capitalize()} vs {other_conf.capitalize()})."
            )
        else:
            parts.append(f"based on confidence assessment.")

        # Add spread context
        if spread_percent is not None:
            if spread_percent > self.config.medium_confidence_spread * 100:
                parts.append(
                    f" The {spread_percent}% spread between methods indicates "
                    "significant valuation uncertainty."
                )
            elif spread_percent > self.config.high_confidence_spread * 100:
                parts.append(
                    f" The {spread_percent}% spread between methods indicates "
                    "moderate uncertainty."
                )
            else:
                parts.append(
                    f" The {spread_percent}% spread shows good agreement between methods."
                )

        return "".join(parts)

    def _method_display_name(self, method: MethodName) -> str:
        """Get display name for a method.

        Args:
            method: Method enum value.

        Returns:
            Human-readable method name.
        """
        display_names = {
            MethodName.LAST_ROUND: "Last Round",
            MethodName.COMPARABLES: "Comparables",
        }
        return display_names.get(method, method.value.replace("_", " ").title())

    def _calculate_overall_confidence(
        self, results: list[MethodResult]
    ) -> Confidence:
        """Calculate overall confidence from individual method confidences.

        Uses weighted approach:
        - If any method is HIGH and others agree within spread, HIGH
        - If methods disagree significantly, drop confidence
        """
        confidences = [r.confidence for r in results]

        # Single method case
        if len(results) == 1:
            return results[0].confidence

        # Multiple methods - check agreement
        values = [r.value for r in results]
        min_val = min(values)
        max_val = max(values)
        spread = (max_val - min_val) / min_val if min_val > 0 else Decimal("1")

        # If methods agree well
        if spread <= self.config.high_confidence_spread:
            # Boost if any is HIGH
            if Confidence.HIGH in confidences:
                return Confidence.HIGH
            return Confidence.MEDIUM

        # Moderate disagreement
        if spread <= self.config.medium_confidence_spread:
            if all(c == Confidence.HIGH for c in confidences):
                return Confidence.MEDIUM
            if Confidence.LOW in confidences:
                return Confidence.LOW
            return Confidence.MEDIUM

        # High disagreement - reduce confidence
        return Confidence.LOW
