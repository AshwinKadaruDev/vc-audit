"""Configuration management for VC Audit Tool."""

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ValuationConfig(BaseModel):
    """Frozen configuration for valuation parameters.

    All tunable parameters for valuation methods are defined here
    to ensure reproducibility and transparency.
    """

    model_config = {"frozen": True}

    # Last Round method parameters
    max_round_age_months: int = Field(
        default=18,
        description="Maximum age of last round to be considered valid"
    )
    stale_round_threshold_months: int = Field(
        default=12,
        description="Age threshold after which round is considered stale"
    )

    # Market adjustment parameters
    default_beta: Decimal = Field(
        default=Decimal("1.5"),
        description="Default beta for early-stage companies"
    )

    # Comparable method parameters
    min_comparables: int = Field(
        default=3,
        description="Minimum number of comparable companies required"
    )
    multiple_percentile: int = Field(
        default=50,
        description="Percentile to use for comparable multiple (50 = median)"
    )

    # Confidence thresholds
    high_confidence_spread: Decimal = Field(
        default=Decimal("0.15"),
        description="Max spread between methods for high confidence"
    )
    medium_confidence_spread: Decimal = Field(
        default=Decimal("0.30"),
        description="Max spread between methods for medium confidence"
    )


class Settings(BaseSettings):
    """Environment-based application settings."""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    # Database settings
    database_url: str = Field(default="")

    # Database Pool Settings
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)
    db_pool_recycle: int = Field(default=3600)
    db_connect_timeout: int = Field(default=10)
    db_command_timeout: int = Field(default=30)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="text")  # "text" or "json"

    # Rate Limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_window_seconds: int = Field(default=60)

    # Retry Configuration
    retry_max_attempts: int = Field(default=3)
    retry_base_delay: float = Field(default=0.1)
    retry_max_delay: float = Field(default=5.0)

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Application
    environment: str = Field(default="development")

    # Data paths
    data_dir: Path = Field(default=Path("data"))

    # Valuation config
    valuation_config: ValuationConfig = Field(default_factory=ValuationConfig)

    @property
    def companies_dir(self) -> Path:
        return self.data_dir / "companies"

    @property
    def market_dir(self) -> Path:
        return self.data_dir / "market"

    @property
    def comparables_dir(self) -> Path:
        return self.data_dir / "comparables"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
