"""Integration tests for the valuation engine."""

import pytest

from src.valuation.engine import ValuationEngine
from src.exceptions import NoValidMethodsError
from src.models import Confidence, MethodName


class TestValuationEngine:
    """Test valuation engine with different company scenarios."""

    def test_basis_ai_both_methods_run(self, engine: ValuationEngine):
        """Test that both methods run for a company with revenue and recent round."""
        result = engine.run("basis_ai")

        assert result.company_id == "basis_ai"
        assert result.company_name == "Basis AI"
        assert len(result.method_results) == 2

        methods = {r.method for r in result.method_results}
        assert MethodName.LAST_ROUND in methods
        assert MethodName.COMPARABLES in methods

        # Should have cross-method analysis
        assert result.cross_method_analysis is not None
        assert len(result.cross_method_analysis) > 0

    def test_techstart_only_last_round(self, engine: ValuationEngine):
        """Test pre-revenue company only gets Last Round method."""
        result = engine.run("techstart")

        assert result.company_id == "techstart"
        assert len(result.method_results) == 1
        assert result.method_results[0].method == MethodName.LAST_ROUND

        # Comps should be skipped
        assert len(result.skipped_methods) == 1
        assert result.skipped_methods[0].method == MethodName.COMPARABLES
        assert "pre-revenue" in result.skipped_methods[0].reason.lower()

    def test_growthco_stale_round_warning(self, engine: ValuationEngine):
        """Test that stale round produces warning but still runs."""
        result = engine.run("growthco")

        assert result.company_id == "growthco"
        assert len(result.method_results) == 2

        # Find last round result
        last_round_result = next(
            r for r in result.method_results if r.method == MethodName.LAST_ROUND
        )

        # Should have a stale round warning
        assert any("months old" in w for w in last_round_result.warnings)

    def test_prerevenue_no_round_fails(self, engine: ValuationEngine):
        """Test that company with no revenue and no round fails."""
        with pytest.raises(NoValidMethodsError) as exc_info:
            engine.run("prerevenue_no_round")

        assert exc_info.value.details["company_id"] == "prerevenue_no_round"
        skip_reasons = exc_info.value.details["skip_reasons"]
        assert "last_round" in skip_reasons
        assert "comparables" in skip_reasons

    def test_old_round_only_comps(self, engine: ValuationEngine):
        """Test company with old round only gets Comparables method."""
        result = engine.run("old_round")

        assert result.company_id == "old_round"
        assert len(result.method_results) == 1
        assert result.method_results[0].method == MethodName.COMPARABLES

        # Last Round should be skipped due to age
        assert len(result.skipped_methods) == 1
        assert result.skipped_methods[0].method == MethodName.LAST_ROUND
        assert "too old" in result.skipped_methods[0].reason.lower()

    def test_input_hash_reproducibility(self, engine: ValuationEngine):
        """Test that same inputs produce same hash."""
        result1 = engine.run("basis_ai")
        result2 = engine.run("basis_ai")

        # Hashes should match for same inputs on same day
        assert result1.input_hash == result2.input_hash

    def test_config_snapshot_included(self, engine: ValuationEngine):
        """Test that config snapshot is included in result."""
        result = engine.run("basis_ai")

        assert result.config_snapshot is not None
        assert "max_round_age_months" in result.config_snapshot
        assert "min_comparables" in result.config_snapshot
        assert "default_beta" in result.config_snapshot

    def test_audit_trail_present(self, engine: ValuationEngine):
        """Test that audit trail is present for each method."""
        result = engine.run("basis_ai")

        for method_result in result.method_results:
            assert len(method_result.audit_trail) > 0
            # Each step should have required fields
            for step in method_result.audit_trail:
                assert step.step_number > 0
                assert len(step.description) > 0

    def test_summary_generation(self, engine: ValuationEngine):
        """Test that summary is properly generated."""
        result = engine.run("basis_ai")

        assert result.summary.primary_value
        assert result.summary.primary_method in [MethodName.LAST_ROUND, MethodName.COMPARABLES]
        assert result.summary.overall_confidence in [
            Confidence.HIGH,
            Confidence.MEDIUM,
            Confidence.LOW,
        ]
        assert len(result.summary.summary_text) > 0

        # Should have value range when multiple methods
        if len(result.method_results) > 1:
            assert result.summary.value_range_low is not None
            assert result.summary.value_range_high is not None
