"""Tests for serialization utilities."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import pytest

from src.utils.serialization import make_json_serializable


class TestEnum(str, Enum):
    """Test enum for serialization."""
    OPTION_A = "option_a"
    OPTION_B = "option_b"


def test_none_value():
    """Test serialization of None."""
    assert make_json_serializable(None) is None


def test_primitive_types():
    """Test serialization of primitive types."""
    assert make_json_serializable("test") == "test"
    assert make_json_serializable(42) == 42
    assert make_json_serializable(3.14) == 3.14
    assert make_json_serializable(True) is True
    assert make_json_serializable(False) is False


def test_decimal():
    """Test serialization of Decimal values."""
    assert make_json_serializable(Decimal("123.45")) == "123.45"
    assert make_json_serializable(Decimal("0")) == "0"
    assert make_json_serializable(Decimal("-99.99")) == "-99.99"


def test_date():
    """Test serialization of date values."""
    test_date = date(2024, 1, 15)
    assert make_json_serializable(test_date) == "2024-01-15"


def test_datetime():
    """Test serialization of datetime values."""
    test_dt = datetime(2024, 1, 15, 10, 30, 45)
    assert make_json_serializable(test_dt) == "2024-01-15T10:30:45"


def test_uuid():
    """Test serialization of UUID values."""
    test_uuid = uuid4()
    assert make_json_serializable(test_uuid) == str(test_uuid)


def test_enum():
    """Test serialization of Enum values."""
    assert make_json_serializable(TestEnum.OPTION_A) == "option_a"
    assert make_json_serializable(TestEnum.OPTION_B) == "option_b"


def test_dict():
    """Test serialization of dict values."""
    test_dict = {
        "name": "test",
        "amount": Decimal("100.50"),
        "created": date(2024, 1, 15),
    }
    result = make_json_serializable(test_dict)
    assert result == {
        "name": "test",
        "amount": "100.50",
        "created": "2024-01-15",
    }


def test_list():
    """Test serialization of list values."""
    test_list = [
        "string",
        42,
        Decimal("10.5"),
        date(2024, 1, 15),
    ]
    result = make_json_serializable(test_list)
    assert result == [
        "string",
        42,
        "10.5",
        "2024-01-15",
    ]


def test_tuple():
    """Test serialization of tuple values."""
    test_tuple = ("test", Decimal("99.99"))
    result = make_json_serializable(test_tuple)
    assert result == ["test", "99.99"]


def test_nested_structures():
    """Test serialization of nested data structures."""
    test_data = {
        "company": {
            "id": uuid4(),
            "metrics": [
                {"value": Decimal("100"), "date": date(2024, 1, 1)},
                {"value": Decimal("200"), "date": date(2024, 2, 1)},
            ],
        },
        "status": TestEnum.OPTION_A,
    }
    result = make_json_serializable(test_data)

    # Verify structure is preserved
    assert "company" in result
    assert "metrics" in result["company"]
    assert len(result["company"]["metrics"]) == 2
    assert result["company"]["metrics"][0]["value"] == "100"
    assert result["company"]["metrics"][0]["date"] == "2024-01-01"
    assert result["status"] == "option_a"


def test_pydantic_model():
    """Test serialization of Pydantic models."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str
        amount: Decimal
        created: date

    model = TestModel(
        name="test",
        amount=Decimal("123.45"),
        created=date(2024, 1, 15),
    )

    result = make_json_serializable(model)
    assert result == {
        "name": "test",
        "amount": "123.45",
        "created": "2024-01-15",
    }


def test_unknown_object():
    """Test serialization falls back to string for unknown types."""
    class CustomClass:
        def __str__(self):
            return "custom_object"

    obj = CustomClass()
    result = make_json_serializable(obj)
    assert result == "custom_object"
