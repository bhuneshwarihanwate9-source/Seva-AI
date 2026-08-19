"""
Eligibility engine for the Seva-AI backend.

Evaluates a citizen's ``UserProfile`` against a ``Scheme``'s structured
eligibility rules and produces an ``EligibilityResult`` with a score
and per-condition reasons.
"""

from __future__ import annotations

from Backend.models.profile import UserProfile
from Backend.models.results import (
    ConditionResult,
    ConditionStatus,
    EligibilityResult,
    OverallResult,
)
from Backend.models.scheme import Scheme

# Conditions evaluated by the engine, in display order.
CONDITION_ORDER = [
    "gender",
    "age",
    "income",
    "social_category",
    "occupation",
    "disability",
]


def evaluate_scheme(profile: UserProfile, scheme: Scheme) -> EligibilityResult:
    """
    Evaluate a single scheme against a user profile.

    Returns an ``EligibilityResult`` containing:
      - ``overall_result``: ELIGIBLE, PARTIAL, or INELIGIBLE
      - ``confidence_score``: 0.0–1.0 match confidence
      - ``condition_results``: per-condition PASS/FAIL/UNKNOWN/NOT_APPLICABLE
      - ``explanation``: human-readable summary

    Matching logic:
      - Any hard FAIL  -> INELIGIBLE
      - All applicable PASS -> ELIGIBLE
      - No FAIL but >=1 UNKNOWN -> PARTIAL
    """
    conditions: list[ConditionResult] = [
        _match_gender(profile, scheme),
        _match_age(profile, scheme),
        _match_income(profile, scheme),
        _match_social_category(profile, scheme),
        _match_occupation(profile, scheme),
        _match_disability(profile, scheme),
    ]

    fails = [c for c in conditions if c.status == ConditionStatus.FAIL]
    unknowns = [c for c in conditions if c.status == ConditionStatus.UNKNOWN]
    passes = [c for c in conditions if c.status == ConditionStatus.PASS]

    if fails:
        overall = OverallResult.INELIGIBLE
    elif passes and not unknowns:
        overall = OverallResult.ELIGIBLE
    elif not fails and unknowns:
        overall = OverallResult.PARTIAL
    else:
        overall = OverallResult.UNKNOWN  # type: ignore[assignment]

    confidence = _compute_confidence(scheme, conditions)
    explanation = _build_explanation(overall, fails, unknowns)

    return EligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.scheme_name,
        overall_result=overall,
        confidence_score=confidence,
        confidence_explanation=_confidence_explanation(confidence),
        condition_results=conditions,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Individual condition matchers
# ---------------------------------------------------------------------------


def _match_gender(profile: UserProfile, scheme: Scheme) -> ConditionResult:
    """Gender restriction: scheme.gender in {any, male, female}."""
    required = scheme.gender.strip().lower()
    user_value = profile.gender.value if profile.gender else None

    if required in ("", "any"):
        return ConditionResult(
            condition_name="gender",
            status=ConditionStatus.NOT_APPLICABLE,
            user_value=user_value,
            required_value="any",
            explanation="Scheme is open to all genders.",
        )
    if user_value is None:
        return ConditionResult(
            condition_name="gender",
            status=ConditionStatus.UNKNOWN,
            user_value=None,
            required_value=required,
            explanation=f"Scheme is restricted to '{required}'; user gender not provided.",
        )
    if user_value == required:
        return ConditionResult(
            condition_name="gender",
            status=ConditionStatus.PASS,
            user_value=user_value,
            required_value=required,
            explanation=f"User gender '{user_value}' matches required '{required}'.",
        )
    return ConditionResult(
        condition_name="gender",
        status=ConditionStatus.FAIL,
        user_value=user_value,
        required_value=required,
        explanation=f"Scheme is restricted to '{required}', but user is '{user_value}'.",
    )


def _match_age(profile: UserProfile, scheme: Scheme) -> ConditionResult:
    """Age range: user.age must be within [min_age, max_age]."""
    user_age = profile.age
    min_age = scheme.min_age
    max_age = scheme.max_age

    if min_age is None and max_age is None:
        return ConditionResult(
            condition_name="age",
            status=ConditionStatus.NOT_APPLICABLE,
            user_value=str(user_age) if user_age is not None else None,
            required_value="no age restriction",
            explanation="Scheme has no age restriction.",
        )
    if user_age is None:
        return ConditionResult(
            condition_name="age",
            status=ConditionStatus.UNKNOWN,
            user_value=None,
            required_value=_format_age_range(min_age, max_age),
            explanation="User age not provided; cannot verify age eligibility.",
        )

    if min_age is not None and user_age < min_age:
        return ConditionResult(
            condition_name="age",
            status=ConditionStatus.FAIL,
            user_value=str(user_age),
            required_value=f">= {min_age:g}",
            explanation=f"User age {user_age:g} is below minimum {min_age:g}.",
        )
    if max_age is not None and user_age > max_age:
        return ConditionResult(
            condition_name="age",
            status=ConditionStatus.FAIL,
            user_value=str(user_age),
            required_value=f"<= {max_age:g}",
            explanation=f"User age {user_age:g} exceeds maximum {max_age:g}.",
        )

    return ConditionResult(
        condition_name="age",
        status=ConditionStatus.PASS,
        user_value=str(user_age),
        required_value=_format_age_range(min_age, max_age),
        explanation=f"User age {user_age:g} is within the required range.",
    )


def _match_income(profile: UserProfile, scheme: Scheme) -> ConditionResult:
    """Income limit: user.annual_income must be <= scheme.max_annual_income."""
    user_income = profile.annual_income
    max_income = scheme.max_annual_income

    if max_income is None:
        return ConditionResult(
            condition_name="income",
            status=ConditionStatus.NOT_APPLICABLE,
            user_value=str(user_income) if user_income is not None else None,
            required_value="no income limit",
            explanation="Scheme has no income restriction.",
        )
    if user_income is None:
        return ConditionResult(
            condition_name="income",
            status=ConditionStatus.UNKNOWN,
            user_value=None,
            required_value=f"<= {max_income:,.0f}",
            explanation="User income not provided; cannot verify income eligibility.",
        )
    if user_income <= max_income:
        return ConditionResult(
            condition_name="income",
            status=ConditionStatus.PASS,
            user_value=f"{user_income:,.0f}",
            required_value=f"<= {max_income:,.0f}",
            explanation=f"User income ₹{user_income:,.0f} is within the ₹{max_income:,.0f} limit.",
        )
    return ConditionResult(
        condition_name="income",
        status=ConditionStatus.FAIL,
        user_value=f"{user_income:,.0f}",
        required_value=f"<= {max_income:,.0f}",
        explanation=f"User income ₹{user_income:,.0f} exceeds the ₹{max_income:,.0f} limit.",
    )


def _match_social_category(profile: UserProfile, scheme: Scheme) -> ConditionResult:
    """Social category: user.social_category must be in scheme's allowed list."""
    allowed = scheme.social_category_list()
    user_category = profile.social_category.value if profile.social_category else None

    if not allowed:
        return ConditionResult(
            condition_name="social_category",
            status=ConditionStatus.NOT_APPLICABLE,
            user_value=user_category,
            required_value="no category restriction",
            explanation="Scheme has no social category restriction.",
        )
    if user_category is None:
        return ConditionResult(
            condition_name="social_category",
            status=ConditionStatus.UNKNOWN,
            user_value=None,
            required_value="; ".join(allowed),
            explanation="User social category not provided; cannot verify category eligibility.",
        )
    if user_category in allowed:
        return ConditionResult(
            condition_name="social_category",
            status=ConditionStatus.PASS,
            user_value=user_category,
            required_value="; ".join(allowed),
            explanation=f"User category '{user_category}' is in the allowed list.",
        )
    return ConditionResult(
        condition_name="social_category",
        status=ConditionStatus.FAIL,
        user_value=user_category,
        required_value="; ".join(allowed),
        explanation=f"User category '{user_category}' is not in the allowed list.",
    )


def _match_occupation(profile: UserProfile, scheme: Scheme) -> ConditionResult:
    """Occupation: user.occupation must be in scheme's allowed occupation list."""
    allowed = scheme.occupation_list()
    user_occupation = profile.occupation

    if not allowed:
        return ConditionResult(
            condition_name="occupation",
            status=ConditionStatus.NOT_APPLICABLE,
            user_value=user_occupation,
            required_value="no occupation restriction",
            explanation="Scheme has no occupation restriction.",
        )
    if user_occupation is None:
        return ConditionResult(
            condition_name="occupation",
            status=ConditionStatus.UNKNOWN,
            user_value=None,
            required_value="; ".join(allowed),
            explanation="User occupation not provided; cannot verify occupation eligibility.",
        )
    if user_occupation in allowed:
        return ConditionResult(
            condition_name="occupation",
            status=ConditionStatus.PASS,
            user_value=user_occupation,
            required_value="; ".join(allowed),
            explanation=f"User occupation '{user_occupation}' is in the allowed list.",
        )
    return ConditionResult(
        condition_name="occupation",
        status=ConditionStatus.FAIL,
        user_value=user_occupation,
        required_value="; ".join(allowed),
        explanation=f"User occupation '{user_occupation}' is not in the allowed list.",
    )


def _match_disability(profile: UserProfile, scheme: Scheme) -> ConditionResult:
    """Disability: user.disability_type must be in scheme's required list."""
    required = scheme.disability_list()
    user_disability = profile.disability_type

    if not required:
        return ConditionResult(
            condition_name="disability",
            status=ConditionStatus.NOT_APPLICABLE,
            user_value=user_disability,
            required_value="no disability restriction",
            explanation="Scheme has no disability restriction.",
        )
    if user_disability is None:
        return ConditionResult(
            condition_name="disability",
            status=ConditionStatus.UNKNOWN,
            user_value=None,
            required_value="; ".join(required),
            explanation="User disability status not provided; cannot verify disability eligibility.",
        )
    if user_disability in required:
        return ConditionResult(
            condition_name="disability",
            status=ConditionStatus.PASS,
            user_value=user_disability,
            required_value="; ".join(required),
            explanation=f"User disability '{user_disability}' matches a required type.",
        )
    return ConditionResult(
        condition_name="disability",
        status=ConditionStatus.FAIL,
        user_value=user_disability,
        required_value="; ".join(required),
        explanation=f"User disability '{user_disability}' is not in the required list.",
    )


# ---------------------------------------------------------------------------
# Scoring and explanation helpers
# ---------------------------------------------------------------------------


def _compute_confidence(scheme: Scheme, conditions: list[ConditionResult]) -> float:
    """
    Compute a 0.0–1.0 confidence score for the match.

    Formula:
      confidence = 0.5 * scheme_data_quality + 0.5 * match_certainty

    where:
      - scheme_data_quality = scheme.confidence_score (0–1 from data pipeline)
      - match_certainty     = fraction of evaluated conditions that are
        PASS or FAIL (i.e., not UNKNOWN / NOT_APPLICABLE)
    """
    evaluated = [c for c in conditions if c.status in (ConditionStatus.PASS, ConditionStatus.FAIL)]
    total = len(conditions)
    certainty = len(evaluated) / total if total else 0.0

    confidence = 0.5 * scheme.confidence_score + 0.5 * certainty
    return round(min(max(confidence, 0.0), 1.0), 4)


def _confidence_explanation(confidence: float) -> str:
    """Human-readable label for a confidence score."""
    if confidence >= 0.8:
        return "High confidence — most criteria verified."
    if confidence >= 0.5:
        return "Medium confidence — some criteria unverified."
    return "Low confidence — many criteria unverified."


def _build_explanation(
    overall: OverallResult,
    fails: list[ConditionResult],
    unknowns: list[ConditionResult],
) -> str:
    """Build a human-readable summary of the overall verdict."""
    if overall == OverallResult.INELIGIBLE:
        failed_names = ", ".join(c.condition_name for c in fails)
        return f"Ineligible: failed {failed_names}."
    if overall == OverallResult.ELIGIBLE:
        return "Eligible: all applicable criteria are satisfied."
    if overall == OverallResult.PARTIAL:
        unknown_names = ", ".join(c.condition_name for c in unknowns)
        return f"Partially eligible: {unknown_names} could not be verified."
    return "Eligibility could not be determined."


def _format_age_range(min_age: float | None, max_age: float | None) -> str:
    """Format an age range for display."""
    if min_age is not None and max_age is not None:
        return f"{min_age:g}–{max_age:g}"
    if min_age is not None:
        return f">= {min_age:g}"
    if max_age is not None:
        return f"<= {max_age:g}"
    return "no age restriction"