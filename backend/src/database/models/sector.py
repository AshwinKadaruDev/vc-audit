"""Sector ORM model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Sector(Base):
    """Sector reference data model.

    Sectors are reference data - typically only read, rarely modified.
    They define the industries that companies operate in (e.g., 'saas', 'fintech').
    """

    __tablename__ = "sectors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
