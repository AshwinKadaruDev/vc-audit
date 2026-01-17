"""SQLAlchemy base classes and mixins."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    # Enable better type checking and IDE support
    type_annotation_map = {
        # Python types -> SQLAlchemy types mapping
        # Defaults are usually sufficient, but can be customized here
    }


class IdMixin:
    """Mixin for models with UUID primary keys."""

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Mixin for models with created_at timestamp."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
