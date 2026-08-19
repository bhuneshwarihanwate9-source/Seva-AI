"""
Load cleaned scheme data into MySQL (database: seva_ai).

Usage (from project root):
    python backend/data_pipeline/load_to_mysql.py

Prerequisites:
    1. MySQL server running
    2. .env configured (see README)
    3. cleaned_schemes.csv generated via clean_data.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Backend.data_pipeline.config import (
    CLEANED_CSV_PATH,
    INSERT_BATCH_SIZE,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    SCHEMA_SQL_PATH,
    mysql_url,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

INSERT_SQL = """
INSERT INTO schemes (
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
) VALUES (
    %(scheme_id)s,
    %(scheme_name)s,
    %(state)s,
    %(category)s,
    %(benefit_summary)s,
    %(eligibility_text_clean)s,
    %(gender)s,
    %(min_age)s,
    %(max_age)s,
    %(max_annual_income)s,
    %(occupation_tokens)s,
    %(allowed_social_categories)s,
    %(required_disability_status)s,
    %(benefit_value_numeric)s,
    %(confidence_score)s,
    %(application_url)s,
    %(official_source_url)s
)
"""


def _nullify(value: Any) -> Any:
    """Convert pandas NaN/NaT and empty strings to Python None for MySQL NULL."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


def create_database_if_not_exists() -> None:
    """Connect to MySQL server and create the target database."""
    logger.info(
        "Connecting to MySQL at %s:%s as %s",
        MYSQL_HOST,
        MYSQL_PORT,
        MYSQL_USER,
    )
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD or None,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        logger.info("Database '%s' is ready", MYSQL_DATABASE)
    finally:
        connection.close()


def execute_schema(engine: Engine) -> None:
    """Run schema.sql to create tables and indexes."""
    if not SCHEMA_SQL_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_SQL_PATH}")

    schema_sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    logger.info("Executing schema from %s", SCHEMA_SQL_PATH)

    # Split on semicolons; skip empty fragments and comments-only blocks
    statements = [
        stmt.strip()
        for stmt in schema_sql.split(";")
        if stmt.strip() and not stmt.strip().startswith("--")
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
    logger.info("Schema applied successfully")


def load_cleaned_csv(path: Path) -> pd.DataFrame:
    """Load the cleaned CSV produced by clean_data.py."""
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned CSV not found: {path}. Run clean_data.py first."
        )
    logger.info("Loading cleaned CSV from %s", path)
    df = pd.read_csv(path, keep_default_na=True, na_values=["", "NA", "NaN"])
    logger.info("Loaded %s rows for import", len(df))
    return df


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame rows to dicts with proper NULL handling."""
    records: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        record = {key: _nullify(value) for key, value in row.items()}
        records.append(record)
    return records


def truncate_table(engine: Engine) -> None:
    """Remove existing rows so re-imports are idempotent."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE schemes"))
    logger.info("Truncated existing rows in schemes table")


def batch_insert(engine: Engine, records: list[dict[str, Any]]) -> None:
    """Insert records in batches using a raw DBAPI connection for speed."""
    total = len(records)
    if total == 0:
        logger.warning("No records to insert")
        return

    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        inserted = 0
        for start in range(0, total, INSERT_BATCH_SIZE):
            batch = records[start : start + INSERT_BATCH_SIZE]
            cursor.executemany(INSERT_SQL, batch)
            raw_conn.commit()
            inserted += len(batch)
            logger.info("Inserted %s / %s rows (%.1f%%)", inserted, total, 100 * inserted / total)
        cursor.close()
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()


def verify_import(engine: Engine) -> None:
    """Log post-import statistics."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM schemes")).scalar_one()
        avg_conf = conn.execute(
            text("SELECT AVG(confidence_score) FROM schemes")
        ).scalar_one()
        index_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.statistics "
                "WHERE table_schema = :db AND table_name = 'schemes'"
            ),
            {"db": MYSQL_DATABASE},
        ).scalar_one()

    logger.info("Verification:")
    logger.info("  Total rows in schemes : %s", count)
    logger.info("  Average confidence    : %.4f", avg_conf or 0)
    logger.info("  Index entries         : %s", index_count)


def main() -> None:
    try:
        create_database_if_not_exists()

        engine = create_engine(mysql_url(include_database=True), pool_pre_ping=True)
        execute_schema(engine)

        df = load_cleaned_csv(CLEANED_CSV_PATH)
        records = dataframe_to_records(df)

        truncate_table(engine)
        batch_insert(engine, records)
        verify_import(engine)

        logger.info("MySQL import completed successfully.")
        logger.info("  Database : %s", MYSQL_DATABASE)
        logger.info("  Table    : schemes")
    except Exception:
        logger.exception("MySQL import failed")
        sys.exit(1)
    finally:
        if "engine" in locals():
            engine.dispose()


if __name__ == "__main__":
    main()
