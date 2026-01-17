"""Tests for Pydantic model validators."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models import Adjustment, Financials, LastRound


class TestFinancialsValidation:
    """Tests for Financials model validators."""

    def test_positive_revenue_ttm(self):
        """Test that positive revenue_ttm is accepted."""
        financials = Financials(revenue_ttm=Decimal("1000000"))
        assert financials.revenue_ttm == Decimal("1000000")

    def test_negative_revenue_ttm_rejected(self):
        """Test that negative revenue_ttm is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Financials(revenue_ttm=Decimal("-1000"))
        assert "Must be positive" in str(exc_info.value)

    def test_positive_burn_rate(self):
        """Test that positive burn_rate is accepted."""
        financials = Financials(burn_rate=Decimal("50000"))
        assert financials.burn_rate == Decimal("50000")

    def test_negative_burn_rate_rejected(self):
        """Test that negative burn_rate is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Financials(burn_rate=Decimal("-10000"))
        assert "Must be positive" in str(exc_info.value)

    def test_valid_gross_margin(self):
        """Test that valid gross_margin (0-1) is accepted."""
        financials = Financials(gross_margin=Decimal("0.75"))
        assert financials.gross_margin == Decimal("0.75")

    def test_gross_margin_at_boundaries(self):
        """Test gross_margin at 0 and 1."""
        financials_zero = Financials(gross_margin=Decimal("0"))
        assert financials_zero.gross_margin == Decimal("0")

        financials_one = Financials(gross_margin=Decimal("1"))
        assert financials_one.gross_margin == Decimal("1")

    def test_gross_margin_too_low_rejected(self):
        """Test that gross_margin < 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Financials(gross_margin=Decimal("-0.1"))
        assert "between 0 and 1" in str(exc_info.value)

    def test_gross_margin_too_high_rejected(self):
        """Test that gross_margin > 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Financials(gross_margin=Decimal("1.5"))
        assert "between 0 and 1" in str(exc_info.value)

    def test_none_values_accepted(self):
        """Test that None values are accepted for optional fields."""
        financials = Financials(
            revenue_ttm=None,
            burn_rate=None,
            gross_margin=None,
        )
        assert financials.revenue_ttm is None
        assert financials.burn_rate is None
        assert financials.gross_margin is None


class TestLastRoundValidation:
    """Tests for LastRound model validators."""

    def test_positive_valuations(self):
        """Test that positive valuations are accepted."""
        last_round = LastRound(
            date=date(2024, 1, 1),
            valuation_pre=Decimal("10000000"),
            valuation_post=Decimal("12500000"),
            amount_raised=Decimal("2500000"),
        )
        assert last_round.valuation_pre == Decimal("10000000")
        assert last_round.valuation_post == Decimal("12500000")

    def test_negative_valuation_pre_rejected(self):
        """Test that negative valuation_pre is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LastRound(
                date=date(2024, 1, 1),
                valuation_pre=Decimal("-1000000"),
                valuation_post=Decimal("1000000"),
                amount_raised=Decimal("2000000"),
            )
        assert "Must be positive" in str(exc_info.value)

    def test_zero_valuation_rejected(self):
        """Test that zero valuations are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LastRound(
                date=date(2024, 1, 1),
                valuation_pre=Decimal("0"),
                valuation_post=Decimal("1000000"),
                amount_raised=Decimal("1000000"),
            )
        assert "Must be positive" in str(exc_info.value)

    def test_past_date_accepted(self):
        """Test that past dates are accepted."""
        past_date = date.today() - timedelta(days=30)
        last_round = LastRound(
            date=past_date,
            valuation_pre=Decimal("10000000"),
            valuation_post=Decimal("12500000"),
            amount_raised=Decimal("2500000"),
        )
        assert last_round.date == past_date

    def test_future_date_rejected(self):
        """Test that future dates are rejected."""
        future_date = date.today() + timedelta(days=30)
        with pytest.raises(ValidationError) as exc_info:
            LastRound(
                date=future_date,
                valuation_pre=Decimal("10000000"),
                valuation_post=Decimal("12500000"),
                amount_raised=Decimal("2500000"),
            )
        assert "cannot be in the future" in str(exc_info.value)

    def test_valid_post_money_calculation(self):
        """Test that correct post-money calculation is accepted."""
        last_round = LastRound(
            date=date(2024, 1, 1),
            valuation_pre=Decimal("10000000"),
            valuation_post=Decimal("12500000"),
            amount_raised=Decimal("2500000"),
        )
        assert last_round.valuation_post == Decimal("12500000")

    def test_invalid_post_money_calculation_rejected(self):
        """Test that incorrect post-money calculation is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LastRound(
                date=date(2024, 1, 1),
                valuation_pre=Decimal("10000000"),
                valuation_post=Decimal("15000000"),  # Should be 12.5M
                amount_raised=Decimal("2500000"),
            )
        assert "Post-money must equal pre-money + amount raised" in str(exc_info.value)

    def test_post_money_calculation_with_tolerance(self):
        """Test that small rounding errors in post-money are tolerated."""
        # Within 0.01 tolerance should pass
        last_round = LastRound(
            date=date(2024, 1, 1),
            valuation_pre=Decimal("10000000"),
            valuation_post=Decimal("12500000.005"),  # Tiny difference
            amount_raised=Decimal("2500000"),
        )
        assert last_round is not None


class TestAdjustmentValidation:
    """Tests for Adjustment model validators."""

    def test_positive_factor(self):
        """Test that positive adjustment factor is accepted."""
        adjustment = Adjustment(
            name="Market Leader",
            factor=Decimal("1.2"),
            reason="Strong competitive position",
        )
        assert adjustment.factor == Decimal("1.2")

    def test_factor_one_accepted(self):
        """Test that factor of 1.0 (no change) is accepted."""
        adjustment = Adjustment(
            name="Neutral",
            factor=Decimal("1.0"),
            reason="No adjustment needed",
        )
        assert adjustment.factor == Decimal("1.0")

    def test_negative_factor_rejected(self):
        """Test that negative factor is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Adjustment(
                name="Invalid",
                factor=Decimal("-0.5"),
                reason="Should fail",
            )
        assert "must be positive" in str(exc_info.value)

    def test_zero_factor_rejected(self):
        """Test that zero factor is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Adjustment(
                name="Invalid",
                factor=Decimal("0"),
                reason="Should fail",
            )
        assert "must be positive" in str(exc_info.value)

    def test_reasonable_high_factor(self):
        """Test that reasonable high factors are accepted."""
        adjustment = Adjustment(
            name="Exceptional Growth",
            factor=Decimal("5.0"),
            reason="Exceptional market opportunity",
        )
        assert adjustment.factor == Decimal("5.0")

    def test_unreasonably_high_factor_rejected(self):
        """Test that unreasonably high factors are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Adjustment(
                name="Too High",
                factor=Decimal("15.0"),
                reason="Should fail",
            )
        assert "unreasonably high" in str(exc_info.value)

    def test_factor_at_boundary(self):
        """Test factor at the upper boundary (10)."""
        adjustment = Adjustment(
            name="Max",
            factor=Decimal("10.0"),
            reason="At the limit",
        )
        assert adjustment.factor == Decimal("10.0")
