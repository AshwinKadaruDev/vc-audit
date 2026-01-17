"""API routes for VC Audit Tool."""

import random
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    BatchValuationRequest,
    CompanyListItem,
    ErrorResponse,
    HealthResponse,
    PortfolioCompanyResponse,
    SavedValuationResponse,
    ValuationDetail,
    ValuationListItem,
    ValuationRequest,
)
from src.config import get_settings
from src.data.loader import DataLoader
from src.database import crud
from src.database.database import get_db
from src.engine.engine import ValuationEngine
from src.exceptions import (
    DataNotFoundError,
    NoValidMethodsError,
    ValuationError,
)
from src.models import ComparableSet, CompanyData, ValuationResult
from src.services.portfolio_companies import PortfolioCompanyService
from src.services.valuations import ValuationService
from src.utils.serialization import make_json_serializable

router = APIRouter()


# Dependency injection functions
def get_data_loader(settings: Any = Depends(get_settings)) -> DataLoader:
    """Get DataLoader instance."""
    return DataLoader(settings)


def get_valuation_engine(
    loader: DataLoader = Depends(get_data_loader),
    settings: Any = Depends(get_settings),
) -> ValuationEngine:
    """Get ValuationEngine instance."""
    return ValuationEngine(loader, settings.valuation_config)


def get_valuation_service(
    engine: ValuationEngine = Depends(get_valuation_engine),
) -> ValuationService:
    """Get ValuationService instance."""
    return ValuationService(engine)


def get_portfolio_service() -> PortfolioCompanyService:
    """Get PortfolioCompanyService instance."""
    return PortfolioCompanyService()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@router.get("/companies", response_model=list[CompanyListItem])
def list_companies(loader: DataLoader = Depends(get_data_loader)) -> list[CompanyListItem]:
    """List all available companies."""
    companies = loader.list_companies()
    return [CompanyListItem(**c) for c in companies]


@router.get("/sectors", response_model=list[str])
def list_sectors(loader: DataLoader = Depends(get_data_loader)) -> list[str]:
    """List all available comparable sectors."""
    return loader.list_sectors()


@router.get("/indices", response_model=list[str])
def list_indices(loader: DataLoader = Depends(get_data_loader)) -> list[str]:
    """List all available market indices."""
    indices = loader.load_indices()
    return list(indices.keys())


@router.post("/valuations", response_model=ValuationResult)
def run_valuation(
    request: ValuationRequest,
    engine: ValuationEngine = Depends(get_valuation_engine),
) -> ValuationResult:
    """Run valuation for a single company by ID.

    Returns:
        ValuationResult with all method results and summary.

    Raises:
        404: Company not found.
        422: No valid valuation methods could be executed.
        400: Other valuation errors.
    """
    try:
        return engine.run(request.company_id)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except NoValidMethodsError as e:
        raise HTTPException(status_code=422, detail=e.to_dict())
    except ValuationError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/valuations/custom", response_model=ValuationResult)
def run_custom_valuation(
    company_data: CompanyData,
    engine: ValuationEngine = Depends(get_valuation_engine),
) -> ValuationResult:
    """Run valuation with custom company data.

    Accepts full company data directly instead of loading from file.

    Returns:
        ValuationResult with all method results and summary.

    Raises:
        422: No valid valuation methods could be executed.
        400: Other valuation errors.
    """
    try:
        return engine.run_with_data(company_data)
    except NoValidMethodsError as e:
        raise HTTPException(status_code=422, detail=e.to_dict())
    except ValuationError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/valuations/batch", response_model=list[ValuationResult | ErrorResponse])
def run_batch_valuation(
    request: BatchValuationRequest,
    engine: ValuationEngine = Depends(get_valuation_engine),
) -> list[ValuationResult | ErrorResponse]:
    """Run valuation for multiple companies.

    Returns results for each company, with errors inline for failed valuations.
    """
    results: list[ValuationResult | ErrorResponse] = []

    for company_id in request.company_ids:
        try:
            result = engine.run(company_id)
            results.append(result)
        except ValuationError as e:
            results.append(
                ErrorResponse(
                    error_type=e.__class__.__name__,
                    message=e.message,
                    details=e.details,
                )
            )

    return results


@router.get("/companies/{company_id}", response_model=CompanyData)
def get_company(
    company_id: str,
    loader: DataLoader = Depends(get_data_loader),
) -> CompanyData:
    """Get raw company data (debug endpoint).

    Args:
        company_id: Company identifier.

    Returns:
        CompanyData with all company information.

    Raises:
        404: Company not found.
    """
    try:
        return loader.load_company(company_id)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.get("/comparables/{sector}", response_model=ComparableSet)
def get_comparables(
    sector: str,
    loader: DataLoader = Depends(get_data_loader),
) -> ComparableSet:
    """Get comparable companies for a sector (debug endpoint).

    Args:
        sector: Sector name.

    Returns:
        ComparableSet with list of comparable companies.

    Raises:
        404: Sector not found.
    """
    try:
        return loader.load_comparables(sector)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


# =============================================================================
# New endpoints for saved valuations and portfolio companies
# =============================================================================


@router.get("/valuations/saved", response_model=list[ValuationListItem])
async def list_saved_valuations(
    limit: int = 50, db: AsyncSession = Depends(get_db)
) -> list[ValuationListItem]:
    """List all saved valuations.

    Returns:
        List of ValuationListItem objects, most recent first.
    """
    valuations = await crud.list_recent_valuations(db, limit=limit)

    return [
        ValuationListItem(
            id=v.id,
            company_name=v.company_name,
            primary_value=v.primary_value,
            primary_method=v.primary_method,
            overall_confidence=v.overall_confidence,
            valuation_date=v.valuation_date,
            created_at=v.created_at,
        )
        for v in valuations
    ]


@router.get("/valuations/saved/{valuation_id}", response_model=ValuationDetail)
async def get_saved_valuation(
    valuation_id: UUID, db: AsyncSession = Depends(get_db)
) -> ValuationDetail:
    """Get a single saved valuation by ID.

    Args:
        valuation_id: The valuation UUID.

    Returns:
        Full valuation detail with audit trail.

    Raises:
        404: Valuation not found.
    """
    valuation = await crud.get_valuation_by_id(db, valuation_id)

    if valuation is None:
        raise HTTPException(status_code=404, detail="Valuation not found")

    return ValuationDetail(
        id=valuation.id,
        portfolio_company_id=valuation.portfolio_company_id,
        company_name=valuation.company_name,
        input_snapshot=valuation.input_snapshot,
        primary_value=valuation.primary_value,
        primary_method=valuation.primary_method,
        value_range_low=valuation.value_range_low,
        value_range_high=valuation.value_range_high,
        overall_confidence=valuation.overall_confidence,
        summary=valuation.summary,
        method_results=valuation.method_results,
        skipped_methods=valuation.skipped_methods,
        config_snapshot=valuation.config_snapshot,
        valuation_date=valuation.valuation_date,
        created_at=valuation.created_at,
    )


@router.delete("/valuations/saved/{valuation_id}", status_code=204)
async def delete_saved_valuation(
    valuation_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a saved valuation.

    Args:
        valuation_id: The valuation UUID to delete.

    Returns:
        No content on success.

    Raises:
        404: Valuation not found.
    """
    deleted = await crud.delete_valuation(db, valuation_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Valuation not found")


@router.get("/portfolio-companies", response_model=list[PortfolioCompanyResponse])
async def list_portfolio_companies(
    limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)
) -> list[PortfolioCompanyResponse]:
    """List all portfolio companies.

    Returns:
        List of PortfolioCompany objects, most recent first.
    """
    companies = await crud.list_portfolio_companies(db, limit=limit, offset=offset)

    return [
        PortfolioCompanyResponse(
            id=c.id,
            name=c.name,
            sector_id=c.sector_id,
            stage=c.stage,
            founded_date=c.founded_date,
            financials=c.financials,
            last_round=c.last_round,
            adjustments=c.adjustments,
            created_at=c.created_at,
        )
        for c in companies
    ]


@router.get("/portfolio-companies/random", response_model=PortfolioCompanyResponse)
async def get_random_portfolio_company(
    service: PortfolioCompanyService = Depends(get_portfolio_service),
) -> PortfolioCompanyResponse:
    """Get a random portfolio company for form filling.

    Returns:
        A random PortfolioCompany.

    Raises:
        404: No companies available.
    """
    company = await service.get_random_company()

    if company is None:
        raise HTTPException(status_code=404, detail="No portfolio companies available")

    return PortfolioCompanyResponse(
        id=company.id,
        name=company.name,
        sector_id=company.sector_id,
        stage=company.stage,
        founded_date=company.founded_date,
        financials=company.financials,
        last_round=company.last_round,
        adjustments=company.adjustments,
        created_at=company.created_at,
    )


@router.post("/valuations/run-and-save", response_model=SavedValuationResponse)
async def run_and_save_valuation(
    company_data: CompanyData,
    service: ValuationService = Depends(get_valuation_service),
) -> SavedValuationResponse:
    """Run valuation with custom company data and save to database.

    This endpoint runs the valuation engine and persists the result
    to the database for later retrieval.

    Args:
        company_data: Full company data for valuation.

    Returns:
        SavedValuationResponse with the generated valuation ID.

    Raises:
        422: No valid valuation methods could be executed.
        400: Other valuation errors.
    """
    try:
        # Use the valuation service to run and save
        result, saved_valuation_id = await service.run_and_save_valuation(
            company_data
        )

        # Convert result to response format
        method_results_data = []
        for mr in result.method_results:
            method_results_data.append(
                {
                    "method": mr.method,
                    "value": str(mr.value),
                    "confidence": mr.confidence,
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

        skipped_methods_data = [
            {"method": sm.method, "reason": sm.reason} for sm in result.skipped_methods
        ]

        summary_data = {
            "primary_value": str(result.summary.primary_value),
            "primary_method": result.summary.primary_method,
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
            "overall_confidence": result.summary.overall_confidence,
            "summary_text": result.summary.summary_text,
            "selection_reason": result.summary.selection_reason,
        }

        if result.summary.method_comparison:
            summary_data["method_comparison"] = {
                "methods": [
                    {
                        "method": m.method,
                        "value": str(m.value),
                        "confidence": m.confidence,
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

        config_snapshot_data = make_json_serializable(result.config_snapshot)

        return SavedValuationResponse(
            id=saved_valuation_id,
            company_id=result.company_id,
            company_name=result.company_name,
            valuation_date=result.valuation_date,
            summary=summary_data,
            method_results=method_results_data,
            skipped_methods=skipped_methods_data,
            cross_method_analysis=result.cross_method_analysis,
            config_snapshot=config_snapshot_data,
        )

    except NoValidMethodsError as e:
        raise HTTPException(status_code=422, detail=e.to_dict())
    except ValuationError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
