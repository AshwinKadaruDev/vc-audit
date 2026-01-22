"""Comparable Companies valuation method."""

from datetime import date
from decimal import Decimal
from typing import Optional

from src.config import ValuationConfig
from src.database.loader import DataLoader
from src.models import (
    ComparableCompany,
    ComparableSet,
    CompanyData,
    Confidence,
    MethodName,
    MethodResult,
)
from src.utils.math_utils import format_currency, median, percentile, round_decimal

from .base import MethodRegistry, ValuationMethod


@MethodRegistry.register
class ComparablesMethod(ValuationMethod):
    """Values company based on comparable public company multiples."""

    method_name = MethodName.COMPARABLES

    def check_prerequisites(self) -> Optional[str]:
        """Check if Comparables method can be applied."""
        if self.company_data.financials.revenue_ttm is None:
            return "Company has no revenue data (pre-revenue)"

        if self.company_data.financials.revenue_ttm <= 0:
            return "Company revenue must be positive"

        sector = self.company_data.company.sector
        try:
            comps = self.loader.load_comparables(sector)
            if len(comps.companies) < self.config.min_comparables:
                return (
                    f"Insufficient comparables for sector '{sector}'. "
                    f"Found {len(comps.companies)}, need {self.config.min_comparables}"
                )
        except Exception as e:
            return f"Cannot load comparables for sector '{sector}': {e}"

        return None

    def execute(self) -> MethodResult:
        """Execute Comparables valuation."""
        financials = self.company_data.financials
        sector = self.company_data.company.sector
        revenue = financials.revenue_ttm
        assert revenue is not None

        # Step 1: Target Company Metrics
        growth_str = (
            f"{round_decimal(financials.revenue_growth_yoy * 100, 0)}%"
            if financials.revenue_growth_yoy
            else "Not available"
        )
        margin_str = (
            f"{round_decimal(financials.gross_margin * 100, 0)}%"
            if financials.gross_margin
            else "Not available"
        )

        self._add_step(
            description="Target Company Financial Metrics",
            inputs={
                "type": "target_metrics",
                "annual_revenue": format_currency(revenue),
                "revenue_growth": growth_str,
                "gross_margin": margin_str,
                "sector": sector.replace("_", " ").title(),
            },
            result=f"Annual revenue of {format_currency(revenue)} in the {sector.replace('_', ' ').title()} sector",
        )

        # Step 2: Load and display comparable companies
        comps = self.loader.load_comparables(sector)

        comparable_list = []
        for c in comps.companies:
            growth = (
                f"{round_decimal(c.revenue_growth_yoy * 100, 0)}%"
                if c.revenue_growth_yoy
                else "N/A"
            )
            comparable_list.append({
                "ticker": c.ticker,
                "name": c.name,
                "revenue": format_currency(c.revenue_ttm),
                "market_cap": format_currency(c.market_cap),
                "revenue_multiple": f"{round_decimal(c.ev_revenue_multiple, 1)}x",
                "growth": growth,
            })

        # Build data source info for citation
        data_source_info = {}
        if comps.source:
            data_source_info = {
                "name": comps.source.name,
                "retrieved_at": comps.source.retrieved_at.isoformat(),
                "citation": f"Public comparable data from {comps.source.name}",
            }

        self._add_step(
            description="Comparable Public Companies",
            inputs={
                "type": "comparable_companies",
                "sector": sector.replace("_", " ").title(),
                "data_as_of": comps.as_of_date.strftime("%B %d, %Y"),
                "companies": comparable_list,
                "data_source": data_source_info,
            },
            result=f"Found {len(comps.companies)} comparable public companies",
        )

        # Step 3: Calculate multiple statistics
        multiples = [c.ev_revenue_multiple for c in comps.companies]
        median_multiple = median(multiples)
        min_multiple = min(multiples)
        max_multiple = max(multiples)
        p25_multiple = percentile(multiples, 25)
        p75_multiple = percentile(multiples, 75)

        self._add_step(
            description="Revenue Multiple Analysis",
            inputs={
                "type": "multiple_statistics",
                "lowest": f"{round_decimal(min_multiple, 1)}x",
                "percentile_25": f"{round_decimal(p25_multiple, 1)}x",
                "median": f"{round_decimal(median_multiple, 1)}x",
                "percentile_75": f"{round_decimal(p75_multiple, 1)}x",
                "highest": f"{round_decimal(max_multiple, 1)}x",
                "explanation": (
                    "Revenue multiples show how much investors pay per dollar of revenue. "
                    "Higher multiples typically reflect faster growth or better margins."
                ),
            },
            calculation=(
                f"The median revenue multiple among comparable companies is "
                f"{round_decimal(median_multiple, 1)}x, ranging from "
                f"{round_decimal(min_multiple, 1)}x to {round_decimal(max_multiple, 1)}x."
            ),
            result=f"Using median multiple of {round_decimal(median_multiple, 1)}x",
        )

        # Step 4: Apply private company discount
        selected_multiple = self._select_multiple(comps, median_multiple)
        discount = self._calculate_private_discount()
        discount_pct = round_decimal(discount * 100, 0)
        adjusted_multiple = selected_multiple * (Decimal("1") - discount)

        stage_name = self.company_data.company.stage.value.replace("_", " ").title()

        self._add_step(
            description="Private Company Discount",
            inputs={
                "type": "private_discount",
                "public_multiple": f"{round_decimal(selected_multiple, 1)}x",
                "discount_percent": f"{discount_pct}%",
                "company_stage": stage_name,
                "adjusted_multiple": f"{round_decimal(adjusted_multiple, 2)}x",
                "explanation": (
                    f"Private companies trade at a discount to public companies because "
                    f"their shares cannot be easily sold. As a {stage_name} company, "
                    f"we apply a {discount_pct}% discount to reflect this illiquidity."
                ),
            },
            calculation=(
                f"Starting with the {round_decimal(selected_multiple, 1)}x public multiple, "
                f"we apply a {discount_pct}% private company discount."
            ),
            result=f"Adjusted multiple: {round_decimal(adjusted_multiple, 2)}x",
        )

        # Step 5: Calculate base value from multiples
        base_value = revenue * adjusted_multiple

        self._add_step(
            description="Base Valuation Calculation",
            inputs={
                "type": "final_calculation",
                "revenue": format_currency(revenue),
                "multiple": f"{round_decimal(adjusted_multiple, 2)}x",
            },
            calculation=(
                f"{format_currency(revenue)} revenue × {round_decimal(adjusted_multiple, 2)}x multiple"
            ),
            result=f"Base value: {format_currency(base_value)}",
        )

        # Step 6: Apply Company-Specific Adjustments
        final_value, combined_factor, adjustment_derivation_parts = (
            self._apply_company_adjustments(base_value, "base value")
        )

        # Step 7: Final Formula Summary
        # Build variable derivations
        revenue_derivation = f"Trailing twelve months revenue for {self.company_data.company.name}"

        multiple_derivation = (
            f"Median multiple ({round_decimal(median_multiple, 1)}x) with {discount_pct}% private discount"
        )

        if adjustment_derivation_parts:
            company_adj_derivation = f"Product of: {', '.join(adjustment_derivation_parts)}"
        else:
            company_adj_derivation = "No adjustments applied (factor = 1.0)"

        self._add_step(
            description="Final Formula Summary",
            inputs={
                "type": "final_formula",
                "formula_template": "V = R × M × C",
                "formula_display": "Final Value = Revenue × Adjusted Multiple × Company Adjustments",
                "formula_with_values": (
                    f"{format_currency(revenue)} × {round_decimal(adjusted_multiple, 2)}x × "
                    f"{round_decimal(combined_factor, 3)} = {format_currency(final_value)}"
                ),
                "variables": [
                    {
                        "name": "Annual Revenue",
                        "symbol": "R",
                        "value": format_currency(revenue),
                        "derivation": revenue_derivation,
                    },
                    {
                        "name": "Adjusted Multiple",
                        "symbol": "M",
                        "value": f"{round_decimal(adjusted_multiple, 2)}x",
                        "derivation": multiple_derivation,
                    },
                    {
                        "name": "Company Adjustments",
                        "symbol": "C",
                        "value": str(round_decimal(combined_factor, 3)),
                        "derivation": company_adj_derivation,
                    },
                ],
                "final_value": format_currency(final_value),
                "method_name": "Comparables",
            },
            result=f"Final valuation: {format_currency(final_value)}",
        )

        confidence, confidence_explanation = self._determine_confidence(multiples, median_multiple)

        return MethodResult(
            method=self.method_name,
            value=round_decimal(final_value, 0),
            confidence=confidence,
            confidence_explanation=confidence_explanation,
            audit_trail=self._audit_steps,
            warnings=self._warnings,
        )

    def _select_multiple(
        self, comps: ComparableSet, median_multiple: Decimal
    ) -> Decimal:
        """Select appropriate multiple based on company characteristics."""
        multiples = [c.ev_revenue_multiple for c in comps.companies]

        if self.config.multiple_percentile == 50:
            return median_multiple

        return percentile(multiples, self.config.multiple_percentile)

    def _calculate_private_discount(self) -> Decimal:
        """Calculate illiquidity discount for private company."""
        stage = self.company_data.company.stage

        stage_discounts = {
            "seed": Decimal("0.35"),
            "series_a": Decimal("0.30"),
            "series_b": Decimal("0.25"),
            "series_c": Decimal("0.20"),
            "growth": Decimal("0.15"),
        }

        return stage_discounts.get(stage.value, Decimal("0.25"))

    def _determine_confidence(
        self, multiples: list[Decimal], median_multiple: Decimal
    ) -> tuple[Confidence, str]:
        """Determine confidence based on multiple dispersion.

        Returns:
            Tuple of (confidence level, explanation string).
        """
        if not multiples or median_multiple == 0:
            explanation = (
                "LOW confidence: Insufficient comparable data available to calculate "
                "statistical confidence in the multiple selection."
            )
            return Confidence.LOW, explanation

        mean = sum(multiples) / len(multiples)
        variance = sum((m - mean) ** 2 for m in multiples) / len(multiples)
        std_dev = variance ** Decimal("0.5")
        cv = std_dev / mean if mean > 0 else Decimal("1")

        min_multiple = min(multiples)
        max_multiple = max(multiples)

        if cv < Decimal("0.3"):
            explanation = (
                f"HIGH confidence: The comparable companies have consistent multiples "
                f"(CV = {cv:.2f}, below 0.30 threshold). "
                f"Multiples range from {min_multiple:.1f}x to {max_multiple:.1f}x "
                f"with median {median_multiple:.1f}x."
            )
            return Confidence.HIGH, explanation

        if cv < Decimal("0.5"):
            explanation = (
                f"MEDIUM confidence: The comparable multiples have moderate spread "
                f"(CV = {cv:.2f}). Multiples range from {min_multiple:.1f}x to {max_multiple:.1f}x. "
                f"A CV below 0.30 would indicate HIGH confidence (tight clustering), "
                f"while above 0.50 would be LOW confidence."
            )
            return Confidence.MEDIUM, explanation

        explanation = (
            f"LOW confidence: The comparable multiples have high dispersion "
            f"(CV = {cv:.2f}, above 0.50 threshold). "
            f"Multiples range from {min_multiple:.1f}x to {max_multiple:.1f}x, "
            f"indicating significant variation among comparable companies. "
            f"Consider narrowing the peer group for better comparability."
        )
        return Confidence.LOW, explanation
