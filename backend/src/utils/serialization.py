"""Shared JSON serialization utilities."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def make_json_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable format.

    Handles: Decimal, date, datetime, UUID, Enum, dict, list, Pydantic models.

    Args:
        obj: The object to convert.

    Returns:
        JSON-serializable representation of the object.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return make_json_serializable(obj.model_dump())
    # Fallback: convert to string
    return str(obj)
