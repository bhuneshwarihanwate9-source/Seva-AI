"""
Database connection management for the Seva-AI backend.

Provides a SQLAlchemy engine and session factory bound to the MySQL
database configured via environment variables (see
``backend.data_pipeline.config``).
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.data_pipeline.config import mysql_url

logger = logging.getLogger(__name__)

engine = create_engine(
    mysql_url(include_database=True),
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """
    FastAPI dependency that yields a database session.

    The session is closed automatically after the request completes.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()