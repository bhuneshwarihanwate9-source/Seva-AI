"""
Eligibility result domain models for the Seva-AI eligibility engine.

Defines the output contract of the eligibility engine: per-condition
results (``ConditionResult``) and the overall per-scheme verdict
(``EligibilityResult``).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ConditionStatus(str, Enum):
    """Outcome of a single eligibility condition evaluation."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class OverallResult(str, Enum):
    """Overall eligibility verdict for a scheme."""

    ELIGIBLE = "ELIGIBLE"
    PARTIAL = "PARTIAL"
    INELIGIBLE = "INELIGIBLE"


class ConditionResult(BaseModel):
    """
    Result of evaluating a single eligibility condition for a scheme.

    Attributes:
        condition_name: Identifier of the condition (e.g., ``state``,
            ``gender``, ``min_age``, ``max_income``).
        status: One of ``PASS``, ``FAIL``, ``UNKNOWN``, ``NOT_APPLICABLE``.
        user_value: The value supplied by the user profile (or ``None``).
        required_value: The value required by the scheme (or ``None``).
        explanation: Human-readable explanation of the outcome.
    """

    condition_name: str = Field(
        description="Identifier of the condition (e.g., 'state', 'gender', 'min_age')."
    )
    status: ConditionStatus = Field(
        description="Outcome: PASS, FAIL, UNKNOWN, or NOT_APPLICABLE."
    )
    user_value: str | None = Field(
        default=None,
        description="The value supplied by the user profile.",
    )
    required_value: str | None = Field(
        default=None,
        description="The value required by the scheme.",
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation of the outcome.",
    )


class EligibilityResult(BaseModel):
    """
    Overall eligibility verdict for a single scheme.

    Attributes:
        scheme_id: Unique identifier of the scheme.
        scheme_name: Display name of the scheme.
        overall_result: One of ``ELIGIBLE``, ``PARTIAL``, ``INELIGIBLE``.
        confidence_score: Confidence in the verdict, in [0, 1].
        confidence_explanation: Human-readable explanation of the
            confidence score.
        condition_results: List of per-condition evaluation results.
        explanation: Human-readable summary of the overall verdict.
    """

    scheme_id: str = Field(
        description="Unique identifier of the scheme."
    )
    scheme_name: str = Field(
        description="Display name of the scheme."
    )
    overall_result: OverallResult = Field(
        description="Overall verdict: ELIGIBLE, PARTIAL, or INELIGIBLE."
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the verdict, in [0, 1].",
    )
    confidence_explanation: str = Field(
        default="",
        description="Human-readable explanation of the confidence score.",
    )
    condition_results: list[ConditionResult] = Field(
        default_factory=list,
        description="Per-condition evaluation results.",
    )
    explanation: str = Field(
        default="",
        description="Human-readable summary of the overall verdict.",
    )