"""
Central configuration for the Seva-AI data pipeline.

MySQL credentials are loaded from environment variables (or a .env file in the
project root). Paths to CSV files are resolved relative to the repository root.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Repository root: backend/data_pipeline/config.py -> backend -> repo root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env from project root when present
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# MySQL connection (override via environment / .env)
# ---------------------------------------------------------------------------
MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "seva_ai")

# ---------------------------------------------------------------------------
# Data file paths
# ---------------------------------------------------------------------------
RAW_CSV_PATH: Path = PROJECT_ROOT / "Data" / "indian_government_schemes.csv"
CLEANED_CSV_PATH: Path = PROJECT_ROOT / "Data" / "cleaned_schemes.csv"
SCHEMA_SQL_PATH: Path = Path(__file__).resolve().parent / "schema.sql"

# Batch size for MySQL inserts
INSERT_BATCH_SIZE: int = int(os.getenv("INSERT_BATCH_SIZE", "500"))


def mysql_url(include_database: bool = True) -> str:
    """Build a SQLAlchemy MySQL connection URL."""
    auth = f"{MYSQL_USER}:{MYSQL_PASSWORD}" if MYSQL_PASSWORD else MYSQL_USER
    host = f"{MYSQL_HOST}:{MYSQL_PORT}"
    if include_database:
        return f"mysql+pymysql://{auth}@{host}/{MYSQL_DATABASE}?charset=utf8mb4"
    return f"mysql+pymysql://{auth}@{host}/?charset=utf8mb4"
