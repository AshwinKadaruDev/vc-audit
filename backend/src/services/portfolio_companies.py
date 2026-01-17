"""Portfolio company service for business logic."""

import random
from typing import Optional

from src.database import crud
from src.database.database import get_db_context
from src.database.models import PortfolioCompany


class PortfolioCompanyService:
    """Service for portfolio company operations."""

    async def get_random_company(self) -> Optional[PortfolioCompany]:
        """Get a random portfolio company.

        Used for form filling - selects a random company from the database.

        Returns:
            Random PortfolioCompany or None if no companies exist.
        """
        async with get_db_context() as db:
            companies = await crud.list_portfolio_companies(db, limit=100)

            if not companies:
                return None

            return random.choice(companies)
