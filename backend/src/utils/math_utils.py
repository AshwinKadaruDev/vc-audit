"""Mathematical utility functions for valuation calculations."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence


def median(values: Sequence[Decimal]) -> Decimal:
    """Calculate median of a sequence of Decimal values.

    Args:
        values: Sequence of Decimal values.

    Returns:
        Median value.

    Raises:
        ValueError: If sequence is empty.
    """
    if not values:
        raise ValueError("Cannot calculate median of empty sequence")

    sorted_values = sorted(values)
    n = len(sorted_values)
    mid = n // 2

    if n % 2 == 0:
        return (sorted_values[mid - 1] + sorted_values[mid]) / 2
    return sorted_values[mid]


def percentile(values: Sequence[Decimal], p: int) -> Decimal:
    """Calculate percentile of a sequence of Decimal values.

    Uses linear interpolation between closest ranks.

    Args:
        values: Sequence of Decimal values.
        p: Percentile to calculate (0-100).

    Returns:
        Percentile value.

    Raises:
        ValueError: If sequence is empty or percentile is invalid.
    """
    if not values:
        raise ValueError("Cannot calculate percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError(f"Percentile must be between 0 and 100, got {p}")

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n == 1:
        return sorted_values[0]

    # Calculate rank
    rank = (p / 100) * (n - 1)
    lower_idx = int(rank)
    upper_idx = min(lower_idx + 1, n - 1)
    fraction = Decimal(str(rank - lower_idx))

    lower_val = sorted_values[lower_idx]
    upper_val = sorted_values[upper_idx]

    return lower_val + fraction * (upper_val - lower_val)


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to specified decimal places.

    Args:
        value: Decimal value to round.
        places: Number of decimal places.

    Returns:
        Rounded Decimal value.
    """
    quantize_str = "0." + "0" * places if places > 0 else "0"
    return value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


def format_currency(value: Decimal, symbol: str = "$") -> str:
    """Format a Decimal as currency string.

    Args:
        value: Decimal value to format.
        symbol: Currency symbol to use.

    Returns:
        Formatted currency string.
    """
    if value >= 1_000_000_000:
        return f"{symbol}{round_decimal(value / 1_000_000_000, 2)}B"
    if value >= 1_000_000:
        return f"{symbol}{round_decimal(value / 1_000_000, 2)}M"
    if value >= 1_000:
        return f"{symbol}{round_decimal(value / 1_000, 2)}K"
    return f"{symbol}{round_decimal(value, 2)}"
