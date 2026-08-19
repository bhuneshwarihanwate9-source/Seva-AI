"""
Scheme domain model for the Seva-AI eligibility engine.

Represents a government scheme as stored in the MySQL ``schemes`` table.
Provides helper methods to parse semicolon-separated token lists used
by the eligibility engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Scheme(BaseModel):
    """
    A government scheme with its structured eligibility rules.

    Mirrors the 17 columns of the MySQL ``schemes`` table.
    """

    scheme_id: str = Field(description="Unique identifier of the scheme.")
    scheme_name: str = Field(description="Display name of the scheme.")
    state: str = Field(description="State restriction (e.g., 'All India', 'Odisha').")
    category: str = Field(description="Scheme category (e.g., 'agriculture', 'health').")
    benefit_summary: str = Field(description="Human-readable benefit description.")
    eligibility_text_clean: str = Field(description="Full eligibility rules (free text).")
    gender: str = Field(
        default="any",
        description="Gender restriction: 'any', 'male', or 'female'.",
    )
    min_age: float | None = Field(
        default=None,
        description="Minimum age requirement.",
    )
    max_age: float | None = Field(
        default=None,
        description="Maximum age requirement.",
    )
    max_annual_income: float | None = Field(
        default=None,
        description="Maximum annual income limit in INR.",
    )
    occupation_tokens: str | None = Field(
        default=None,
        description="Semicolon-separated allowed occupations.",
    )
    allowed_social_categories: str | None = Field(
        default=None,
        description="Semicolon-separated allowed social categories.",
    )
    required_disability_status: str | None = Field(
        default=None,
        description="Semicolon-separated required disability types.",
    )
    benefit_value_numeric: float | None = Field(
        default=None,
        description="Numeric benefit amount in INR.",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Data quality confidence score in [0, 1].",
    )
    application_url: str = Field(
        default="",
        description="Application link.",
    )
    official_source_url: str = Field(
        default="",
        description="Official source link.",
    )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def is_national(self) -> bool:
        """Return True if the scheme applies to all of India."""
        return self.state.strip().lower() == "all india"

    def occupation_list(self) -> list[str]:
        """Parse semicolon-separated occupation tokens into a list."""
        return self._parse_tokens(self.occupation_tokens)

    def social_category_list(self) -> list[str]:
        """Parse semicolon-separated social category tokens into a list."""
        return self._parse_tokens(self.allowed_social_categories)

    def disability_list(self) -> list[str]:
        """Parse semicolon-separated disability tokens into a list."""
        return self._parse_tokens(self.required_disability_status)

    @staticmethod
    def _parse_tokens(value: str | None) -> list[str]:
        """Split a semicolon-separated string into a cleaned token list."""
        if not value:
            return []
        return [
            token.strip().lower()
            for token in value.split(";")
            if token.strip()
        ]

    @classmethod
    def from_row(cls, row: dict) -> "Scheme":
        """
        Build a ``Scheme`` instance from a database row dict.

        Accepts both SQLAlchemy ``Row``-style dicts and plain dicts with
        keys matching the MySQL ``schemes`` table columns.
        """
        return cls(
            scheme_id=str(row["scheme_id"]),
            scheme_name=str(row["scheme_name"]),
            state=str(row["state"]),
            category=str(row["category"]),
            benefit_summary=str(row["benefit_summary"]),
            eligibility_text_clean=str(row["eligibility_text_clean"]),
            gender=str(row.get("gender") or "any"),
            min_age=row.get("min_age"),
            max_age=row.get("max_age"),
            max_annual_income=row.get("max_annual_income"),
            occupation_tokens=row.get("occupation_tokens"),
            allowed_social_categories=row.get("allowed_social_categories"),
            required_disability_status=row.get("required_disability_status"),
            benefit_value_numeric=row.get("benefit_value_numeric"),
            confidence_score=float(row.get("confidence_score") or 0.0),
            application_url=str(row.get("application_url") or ""),
            official_source_url=str(row.get("official_source_url") or ""),
        )