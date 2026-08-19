"""
Scheme repository for the Seva-AI backend.

Provides data-access methods for the ``schemes`` table in MySQL.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from Backend.models.scheme import Scheme

logger = logging.getLogger(__name__)

SELECT_ALL_SQL = text(
    """
    SELECT
        scheme_id,
        scheme_name,
        state,
        category,
        benefit_summary,
        eligibility_text_clean,
        gender,
        min_age,
        max_age,
        max_annual_income,
        occupation_tokens,
        allowed_social_categories,
        required_disability_status,
        benefit_value_numeric,
        confidence_score,
        application_url,
        official_source_url
    FROM schemes
    """
)


class SchemeRepository:
    """Data access for the ``schemes`` table."""

    def __init__(self, session: Session):
        self._session = session

    def get_all(self) -> list[Scheme]:
        """Return all schemes as ``Scheme`` model instances."""
        rows = self._session.execute(SELECT_ALL_SQL).mappings().all()
        return [Scheme.from_row(dict(row)) for row in rows]

    def get_by_id(self, scheme_id: str) -> Scheme | None:
        """Return a single scheme by its primary key, or ``None``."""
        row = self._session.execute(
            text(f"{SELECT_ALL_SQL.text} WHERE scheme_id = :scheme_id"),
            {"scheme_id": scheme_id},
        ).mappings().first()
        return Scheme.from_row(dict(row)) if row else None