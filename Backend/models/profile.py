"""
User profile domain model for the Seva-AI eligibility engine.

Represents a citizen's self-declared attributes used to evaluate
eligibility against government scheme rules.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Gender(str, Enum):
    """Supported gender values for eligibility matching."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SocialCategory(str, Enum):
    """Supported social categories for eligibility matching."""

    SC = "sc"
    ST = "st"
    OBC = "obc"
    EWS = "ews"
    GENERAL = "general"


class MaritalStatus(str, Enum):
    """Supported marital statuses for eligibility matching."""

    SINGLE = "single"
    MARRIED = "married"
    WIDOWED = "widowed"
    DIVORCED = "divorced"
    SEPARATED = "separated"


class UserProfile(BaseModel):
    """
    Citizen profile used as input to the eligibility engine.

    All fields are optional so that a partially completed profile can
    still be evaluated. Missing fields produce ``UNKNOWN`` condition
    results rather than hard failures.
    """

    age: int | None = Field(
        default=None,
        ge=0,
        le=120,
        description="Age in years (0–120).",
    )
    gender: Gender | None = Field(
        default=None,
        description="Gender restriction value.",
    )
    state: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="State of residence (e.g., 'Odisha', 'Bihar').",
    )
    annual_income: int | None = Field(
        default=None,
        ge=0,
        description="Annual income in INR.",
    )
    social_category: SocialCategory | None = Field(
        default=None,
        description="Social category (SC/ST/OBC/EWS/General).",
    )
    occupation: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Primary occupation (e.g., 'farmer', 'student').",
    )
    disability_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Disability type (e.g., 'physical', 'visual').",
    )
    marital_status: MaritalStatus | None = Field(
        default=None,
        description="Marital status.",
    )
    is_bpl: bool | None = Field(
        default=None,
        description="Whether the citizen holds a BPL (Below Poverty Line) card.",
    )
    has_land: bool | None = Field(
        default=None,
        description="Whether the citizen owns agricultural land.",
    )
    documents_held: list[str] = Field(
        default_factory=list,
        description="List of documents the citizen already holds.",
    )

    @field_validator("state")
    @classmethod
    def _strip_state(cls, value: str | None) -> str | None:
        """Strip surrounding whitespace from state names."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("occupation")
    @classmethod
    def _strip_occupation(cls, value: str | None) -> str | None:
        """Strip surrounding whitespace and lowercase occupations."""
        if value is None:
            return None
        stripped = value.strip().lower()
        return stripped or None

    @field_validator("disability_type")
    @classmethod
    def _strip_disability(cls, value: str | None) -> str | None:
        """Strip surrounding whitespace and lowercase disability types."""
        if value is None:
            return None
        stripped = value.strip().lower()
        return stripped or None

    @field_validator("documents_held")
    @classmethod
    def _normalize_documents(cls, values: list[str]) -> list[str]:
        """Strip, lowercase, and deduplicate held document names."""
        seen: set[str] = set()
        normalized: list[str] = []
        for doc in values:
            cleaned = doc.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
        return normalized

    @property
    def profile_completeness(self) -> float:
        """
        Fraction of relevant profile fields that are populated (0.0–1.0).

        Counts the 10 core eligibility fields (excludes ``documents_held``).
        """
        core_fields = (
            "age",
            "gender",
            "state",
            "annual_income",
            "social_category",
            "occupation",
            "disability_type",
            "marital_status",
            "is_bpl",
            "has_land",
        )
        populated = sum(1 for field in core_fields if getattr(self, field) is not None)
        return round(populated / len(core_fields), 4)