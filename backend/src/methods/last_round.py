"""Last Round valuation method."""

from datetime import date
from decimal import Decimal
from typing import Optional

from src.config import ValuationConfig
from src.data.loader import DataLoader
from src.models import (
    CompanyData,
    Confidence,
    MethodName,
    MethodResult,
)
from src.utils.math_utils import format_currency, round_decimal

from .base import MethodRegistry, ValuationMethod


@MethodRegistry.register
class LastRoundMethod(ValuationMethod):
    """Values company based on last funding round with market adjustment."""

    method_name = MethodName.LAST_ROUND

    def __init__(
        self,
        company_data: CompanyData,
        config: ValuationConfig,
        loader: DataLoader,
    ):
        super().__init__(company_data, config, loader)
        self._index_name = "NASDAQ"

    def check_prerequisites(self) -> Optional[str]:
        """Check if Last Round method can be applied."""
        if self.company_data.last_round is None:
            return "No last funding round data available"

        round_date = self.company_data.last_round.date
        today = date.today()
        months_old = (today.year - round_date.year) * 12 + (today.month - round_date.month)

        if months_old > self.config.max_round_age_months:
            return (
                f"Last round is too old ({months_old} months). "
                f"Maximum allowed: {self.config.max_round_age_months} months"
            )

        try:
            index_data = self.loader.get_index(self._index_name)
            if not index_data:
                return f"No {self._index_name} index data available"
        except Exception as e:
            return f"Cannot load market index data: {e}"

        return None

    def execute(self) -> MethodResult:
        """Execute Last Round valuation."""
        last_round = self.company_data.last_round
        assert last_round is not None

        # Step 1: Establish Anchor Value
        anchor_value = last_round.valuation_post
        round_date_str = last_round.date.strftime("%B %d, %Y")

        self._add_step(
            description="Starting Point: Last Funding Round",
            inputs={
                "type": "funding_round",
                "round_date": round_date_str,
                "pre_money_valuation": format_currency(last_round.valuation_pre),
                "amount_raised": format_currency(last_round.amount_raised),
                "post_money_valuation": format_currency(last_round.valuation_post),
                "lead_investor": last_round.lead_investor or "Not disclosed",
            },
            result=f"Starting valuation: {format_currency(anchor_value)}",
        )

        # Check for stale round warning
        today = date.today()
        months_old = (today.year - last_round.date.year) * 12 + (
            today.month - last_round.date.month
        )
        if months_old > self.config.stale_round_threshold_months:
            self._add_warning(
                f"This funding round is {months_old} months old. Market conditions "
                "may have changed significantly since then."
            )

        # Step 2: Calculate Market Adjustment with detailed breakdown
        index_data = self.loader.get_index(self._index_name)
        round_index = self._get_closest_index_value(index_data, last_round.date)
        today_index = self._get_closest_index_value(index_data, today)

        market_return = (today_index - round_index) / round_index
        market_return_pct = market_return * 100

        # Direction text
        if market_return > 0:
            direction = "increased"
            direction_symbol = "+"
        elif market_return < 0:
            direction = "decreased"
            direction_symbol = ""
        else:
            direction = "remained flat"
            direction_symbol = ""

        beta = self.config.default_beta
        adjusted_return = beta * market_return
        market_adjustment = Decimal("1.0") + adjusted_return
        market_adjusted_value = anchor_value * market_adjustment

        self._add_step(
            description="Market Adjustment: How Has the Market Moved?",
            inputs={
                "type": "market_adjustment",
                "index_name": self._index_name,
                "round_date": round_date_str,
                "round_index_value": f"{round_decimal(round_index, 2):,}",
                "today_date": today.strftime("%B %d, %Y"),
                "today_index_value": f"{round_decimal(today_index, 2):,}",
                "market_change_percent": f"{direction_symbol}{round_decimal(market_return_pct, 1)}%",
                "market_direction": direction,
                "volatility_factor": str(beta),
                "volatility_explanation": (
                    f"Early-stage companies are more volatile than public markets. "
                    f"We apply a {beta}x factor, meaning if the market moves 10%, "
                    f"we adjust the valuation by {round_decimal(beta * 10, 0)}%."
                ),
                "adjusted_change_percent": f"{direction_symbol}{round_decimal(adjusted_return * 100, 1)}%",
            },
            calculation=(
                f"The {self._index_name} {direction} by {abs(round_decimal(market_return_pct, 1))}% "
                f"since the funding round. Applying the {beta}x volatility factor, "
                f"we adjust the valuation by {direction_symbol}{round_decimal(adjusted_return * 100, 1)}%."
            ),
            result=f"Market-adjusted valuation: {format_currency(market_adjusted_value)}",
        )

        # Step 3: Apply Company-Specific Adjustments
        final_value = market_adjusted_value
        if self.company_data.adjustments:
            combined_factor = Decimal("1.0")
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

            final_value = market_adjusted_value * combined_factor
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
                    f"applied to market-adjusted value."
                ),
                result=f"Final valuation: {format_currency(final_value)}",
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
                result=f"Final valuation: {format_currency(final_value)}",
            )

        confidence = self._determine_confidence(months_old)

        return MethodResult(
            method=self.method_name,
            value=round_decimal(final_value, 0),
            confidence=confidence,
            audit_trail=self._audit_steps,
            warnings=self._warnings,
        )

    def _get_closest_index_value(self, index_data: list, target_date: date) -> Decimal:
        """Get index value closest to target date."""
        closest = min(index_data, key=lambda x: abs((x.date - target_date).days))
        return closest.value

    def _determine_confidence(self, months_old: int) -> Confidence:
        """Determine confidence based on round age."""
        if months_old <= 6:
            return Confidence.HIGH
        if months_old <= self.config.stale_round_threshold_months:
            return Confidence.MEDIUM
        return Confidence.LOW
