"""
Clean and normalize the raw government schemes CSV for MySQL ingestion.

Usage (from project root):
    python backend/data_pipeline/clean_data.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow running as a script without installing the package
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.data_pipeline.config import CLEANED_CSV_PATH, RAW_CSV_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Canonical enums used during normalization
VALID_GENDERS = {"any", "male", "female"}

VALID_STATES = {
    "All India",
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
}

# Common state alias map for minor input variants
STATE_ALIASES = {
    "all india": "All India",
    "andaman & nicobar islands": "Andaman and Nicobar Islands",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "jammu & kashmir": "Jammu and Kashmir",
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "uttaranchal": "Uttarakhand",
}

VALID_CATEGORIES = {
    "agriculture",
    "disability",
    "education",
    "employment",
    "financial_inclusion",
    "health",
    "housing",
    "other",
    "pension",
    "women_and_child",
}

CATEGORY_ALIASES = {
    "women_child": "women_and_child",
    "women and child": "women_and_child",
    "women & child": "women_and_child",
}

OUTPUT_COLUMNS = [
    "scheme_id",
    "scheme_name",
    "state",
    "category",
    "benefit_summary",
    "eligibility_text_clean",
    "gender",
    "min_age",
    "max_age",
    "max_annual_income",
    "occupation_tokens",
    "allowed_social_categories",
    "required_disability_status",
    "benefit_value_numeric",
    "confidence_score",
    "application_url",
    "official_source_url",
]

STRUCTURED_ELIGIBILITY_FIELDS = [
    "min_age",
    "max_age",
    "max_annual_income",
    "occupation_tokens",
    "allowed_social_categories",
    "required_disability_status",
]


def _empty_to_null(df: pd.DataFrame) -> pd.DataFrame:
    """Replace empty strings and whitespace-only values with NaN."""
    return df.replace(r"^\s*$", np.nan, regex=True)


def _normalize_gender(value: object) -> str:
    if pd.isna(value):
        return "any"
    normalized = str(value).strip().lower()
    if normalized in VALID_GENDERS:
        return normalized
    logger.warning("Unknown gender value %r; defaulting to 'any'", value)
    return "any"


def _normalize_state(value: object) -> str | float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    if text in VALID_STATES:
        return text
    alias = STATE_ALIASES.get(text.lower())
    if alias:
        return alias
    # Title-case fallback for close matches
    for valid in VALID_STATES:
        if valid.lower() == text.lower():
            return valid
    logger.warning("Unrecognized state %r; keeping original value", value)
    return text


def _normalize_category(value: object) -> str | float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower().replace(" ", "_")
    if text in VALID_CATEGORIES:
        return text
    if text in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[text]
    logger.warning("Unknown category %r; defaulting to 'other'", value)
    return "other"


def _null_placeholder(value: object, placeholder: float = 1.0) -> float | object:
    """Convert known placeholder numeric values to NULL."""
    if pd.isna(value):
        return np.nan
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return np.nan
    return np.nan if numeric == placeholder else numeric


def _structured_eligibility_ratio(row: pd.Series) -> float:
    """Fraction of structured eligibility fields populated for a scheme."""
    populated = 0
    total = len(STRUCTURED_ELIGIBILITY_FIELDS) + 1  # +1 for gender restriction

    for field in STRUCTURED_ELIGIBILITY_FIELDS:
        if pd.notna(row.get(field)) and str(row.get(field)).strip():
            populated += 1

    gender = row.get("gender")
    if pd.notna(gender) and str(gender).strip().lower() not in ("", "any"):
        populated += 1

    return populated / total if total else 0.0


def _compute_confidence_score(row: pd.Series, eligibility_verified: bool) -> float:
    """
    Composite confidence score in [0, 1] based on:
      - eligibility_verified (40%)
      - structured eligibility field coverage (35%)
      - benefit data availability (25%)
    """
    verified_score = 1.0 if eligibility_verified else 0.0
    structured_score = _structured_eligibility_ratio(row)

    has_benefit_numeric = pd.notna(row.get("benefit_value_numeric"))
    has_benefit_text = pd.notna(row.get("benefit_summary")) and bool(
        str(row.get("benefit_summary")).strip()
    )
    benefit_score = 1.0 if has_benefit_numeric else (0.5 if has_benefit_text else 0.0)

    confidence = (
        0.40 * verified_score + 0.35 * structured_score + 0.25 * benefit_score
    )
    return round(min(max(confidence, 0.0), 1.0), 4)


def load_raw_csv(path: Path) -> pd.DataFrame:
    """Load the source CSV and validate that it exists."""
    if not path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {path}")
    logger.info("Loading raw data from %s", path)
    df = pd.read_csv(path, low_memory=False)
    logger.info("Loaded %s rows and %s columns", len(df), len(df.columns))
    return df


def clean_schemes(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning and normalization rules."""
    df = _empty_to_null(df.copy())

    before_dupes = len(df)
    df = df.drop_duplicates(subset=["scheme_id"], keep="first")
    removed_dupes = before_dupes - len(df)
    if removed_dupes:
        logger.info("Removed %s duplicate scheme_id record(s)", removed_dupes)

    # Normalize income_inferred placeholders before any coalesce logic (audit only)
    if "income_inferred" in df.columns:
        df["income_inferred"] = df["income_inferred"].apply(
            lambda v: _null_placeholder(v, placeholder=1.0)
        )

    cleaned = pd.DataFrame()
    cleaned["scheme_id"] = df["scheme_id"].astype(str).str.strip()
    cleaned["scheme_name"] = df["scheme_name"].astype(str).str.strip()
    cleaned["state"] = df["state_restricted_to_normalized"].apply(_normalize_state)
    cleaned["category"] = df["scheme_category_clean"].apply(_normalize_category)
    cleaned["benefit_summary"] = df["benefit_summary"]
    cleaned["eligibility_text_clean"] = df["eligibility_text_clean"]
    cleaned["gender"] = df["gender_restricted_to"].apply(_normalize_gender)

    for numeric_col, source_col in [
        ("min_age", "min_age"),
        ("max_age", "max_age"),
        ("max_annual_income", "max_annual_income"),
    ]:
        cleaned[numeric_col] = pd.to_numeric(df[source_col], errors="coerce")

    cleaned["occupation_tokens"] = df["allowed_occupations"]
    cleaned["allowed_social_categories"] = df["allowed_social_categories"]
    cleaned["required_disability_status"] = df["required_disability_status"]

    cleaned["benefit_value_numeric"] = pd.to_numeric(
        df["benefit_value_numeric"], errors="coerce"
    ).apply(lambda v: _null_placeholder(v, placeholder=1.0))

    verified_flags = (
        df["eligibility_verified"].astype(str).str.lower().isin(["true", "1", "yes"])
        if "eligibility_verified" in df.columns
        else pd.Series([False] * len(df), index=df.index)
    )

    cleaned["confidence_score"] = [
        _compute_confidence_score(cleaned.iloc[i], bool(verified_flags.iloc[i]))
        for i in range(len(cleaned))
    ]

    cleaned["application_url"] = df["application_url"].astype(str).str.strip()
    cleaned["official_source_url"] = df["official_source_url"].astype(str).str.strip()

    # Final pass: enforce column order and NULL semantics for export
    cleaned = cleaned[OUTPUT_COLUMNS]
    cleaned = _empty_to_null(cleaned)

    # Drop rows missing mandatory identifiers
    mandatory = ["scheme_id", "scheme_name", "state", "category"]
    before_drop = len(cleaned)
    cleaned = cleaned.dropna(subset=mandatory)
    dropped = before_drop - len(cleaned)
    if dropped:
        logger.warning("Dropped %s rows missing mandatory fields", dropped)

    return cleaned


def save_cleaned_csv(df: pd.DataFrame, path: Path) -> None:
    """Write cleaned data to CSV with empty cells representing SQL NULL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, na_rep="")
    logger.info("Saved cleaned data to %s (%s rows)", path, len(df))


def main() -> None:
    try:
        raw_df = load_raw_csv(RAW_CSV_PATH)
        cleaned_df = clean_schemes(raw_df)
        save_cleaned_csv(cleaned_df, CLEANED_CSV_PATH)

        logger.info("Cleaning complete.")
        logger.info("  Rows written : %s", len(cleaned_df))
        logger.info(
            "  Avg confidence: %.4f",
            cleaned_df["confidence_score"].mean(),
        )
        logger.info(
            "  Output file   : %s",
            CLEANED_CSV_PATH,
        )
    except Exception:
        logger.exception("Data cleaning failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
