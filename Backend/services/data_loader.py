"""
Data loader for the Seva-AI eligibility engine.

Loads schemes from the MySQL database into ``Scheme`` model instances.
"""

from __future__ import annotations

import logging

from Backend.models.scheme import Scheme

logger = logging.getLogger(__name__)


def load_all_schemes() -> list[Scheme]:
    """
    Load all schemes from the database.

    Returns an empty list if the database is unavailable, logging a
    warning. This allows the API to start and respond even when the
    database is not yet configured.
    """
    try:
        from Backend.database.connection import SessionLocal
        from Backend.database.repository import SchemeRepository

        session = SessionLocal()
        try:
            repo = SchemeRepository(session)
            return repo.get_all()
        finally:
            session.close()
    except Exception:
        logger.warning("Database unavailable; returning empty scheme list.", exc_info=True)
        return []