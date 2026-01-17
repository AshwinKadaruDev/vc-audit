"""Valuation service for orchestrating valuation runs and database persistence."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from src.database import crud
from src.database.database import get_db_context
from src.engine.engine import ValuationEngine
from src.models import CompanyData, ValuationResult
from src.utils.serialization import make_json_serializable


def _convert_valuation_result_to_db_format(
    result: ValuationResult,
) -> dict[str, Any]:
    """Convert ValuationResult to database-compatible format.

    Args:
        result: The valuation result from the engine.

    Returns:
        Dictionary with converted data ready for database storage.
    """
    # Convert method results
    method_results_data = []
    for mr in result.method_results:
        method_results_data.append(
            {
                "method": mr.method.value,
                "value": str(mr.value),
                "confidence": mr.confidence.value,
                "audit_trail": [
                    {
                        "step_number": step.step_number,
                        "description": step.description,
                        "inputs": make_json_serializable(step.inputs),
                        "calculation": step.calculation,
                        "result": step.result,
                    }
                    for step in mr.audit_trail
                ],
                "warnings": mr.warnings,
            }
        )

    # Convert skipped methods
    skipped_methods_data = [
        {"method": sm.method.value, "reason": sm.reason} for sm in result.skipped_methods
    ]

    # Convert summary
    summary_data = {
        "primary_value": str(result.summary.primary_value),
        "primary_method": result.summary.primary_method.value,
        "value_range_low": (
            str(result.summary.value_range_low)
            if result.summary.value_range_low
            else None
        ),
        "value_range_high": (
            str(result.summary.value_range_high)
            if result.summary.value_range_high
            else None
        ),
        "overall_confidence": result.summary.overall_confidence.value,
        "summary_text": result.summary.summary_text,
        "selection_reason": result.summary.selection_reason,
    }

    if result.summary.method_comparison:
        summary_data["method_comparison"] = {
            "methods": [
                {
                    "method": m.method.value,
                    "value": str(m.value),
                    "confidence": m.confidence.value,
                    "is_primary": m.is_primary,
                }
                for m in result.summary.method_comparison.methods
            ],
            "spread_percent": (
                str(result.summary.method_comparison.spread_percent)
                if result.summary.method_comparison.spread_percent
                else None
            ),
            "spread_warning": result.summary.method_comparison.spread_warning,
            "selection_steps": result.summary.method_comparison.selection_steps,
        }

    # Convert config snapshot
    config_snapshot_data = make_json_serializable(result.config_snapshot)

    return {
        "method_results": method_results_data,
        "skipped_methods": skipped_methods_data,
        "summary": summary_data,
        "config_snapshot": config_snapshot_data,
    }


class ValuationService:
    """Service for running valuations and saving results to database.

    This service orchestrates the valuation engine and database operations,
    keeping the route handlers thin and focused on HTTP concerns.
    """

    def __init__(self, engine: ValuationEngine):
        """Initialize the valuation service.

        Args:
            engine: The valuation engine instance.
        """
        self.engine = engine

    async def run_and_save_valuation(
        self, company_data: CompanyData
    ) -> tuple[ValuationResult, UUID]:
        """Run valuation engine and persist to database.

        This method:
        1. Runs the valuation engine with the provided company data
        2. Gets or creates a portfolio company record
        3. Saves the valuation result to the database
        4. Returns both the result and the saved valuation ID

        Args:
            company_data: The company data to value.

        Returns:
            Tuple of (ValuationResult, saved_valuation_id).

        Raises:
            NoValidMethodsError: If no valuation methods can be executed.
            ValuationError: If valuation fails.
        """
        # Step 1: Run the valuation engine (pure business logic, no DB)
        result = self.engine.run_with_data(company_data)

        # Step 2 & 3: Save to database
        async with get_db_context() as db:
            # Get or create portfolio company
            # First, try to find existing company by name
            companies = await crud.list_portfolio_companies(db, limit=100)
            portfolio_company = next(
                (c for c in companies if c.name == company_data.company.name), None
            )

            if portfolio_company is None:
                # Create a new portfolio company
                portfolio_company = await crud.create_portfolio_company(
                    db=db,
                    name=company_data.company.name,
                    sector_id=company_data.company.sector,
                    stage=company_data.company.stage.value,
                    founded_date=None,
                    financials=(
                        company_data.financials.model_dump(mode="json")
                        if company_data.financials
                        else {}
                    ),
                    last_round=(
                        company_data.last_round.model_dump(mode="json")
                        if company_data.last_round
                        else None
                    ),
                    adjustments=[
                        a.model_dump(mode="json") for a in company_data.adjustments
                    ],
                )

            # Convert valuation result to database format
            db_data = _convert_valuation_result_to_db_format(result)

            # Save the valuation
            saved_valuation = await crud.create_valuation(
                db=db,
                portfolio_company_id=portfolio_company.id,
                company_name=result.company_name,
                input_snapshot=company_data.model_dump(mode="json"),
                input_hash="",  # Hash removed from application logic
                primary_value=Decimal(str(result.summary.primary_value)),
                primary_method=result.summary.primary_method.value,
                value_range_low=(
                    Decimal(str(result.summary.value_range_low))
                    if result.summary.value_range_low
                    else None
                ),
                value_range_high=(
                    Decimal(str(result.summary.value_range_high))
                    if result.summary.value_range_high
                    else None
                ),
                overall_confidence=result.summary.overall_confidence.value,
                summary=db_data["summary"],
                method_results=db_data["method_results"],
                skipped_methods=db_data["skipped_methods"],
                config_snapshot=db_data["config_snapshot"],
            )

            return result, saved_valuation.id
