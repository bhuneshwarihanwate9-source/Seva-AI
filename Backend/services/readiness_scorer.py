"""
Readiness scorer for the Seva-AI backend.

Computes a 0–100 readiness score that reflects how ready a user is to
apply for government schemes.
"""

from __future__ import annotations

from Backend.models.profile import UserProfile


def score_readiness(profile: UserProfile) -> dict:
    """
    Compute a 0–100 readiness score for the user profile.

    Returns the overall readiness score and a per-factor breakdown.
    """
    completeness = profile.profile_completeness  # 0.0 – 1.0

    # Minimal implementation: readiness is based on profile completeness.
    score = round(completeness * 100, 1)

    return {
        "overall_score": score,
        "profile_completeness": completeness,
        "factors": {
            "profile_completeness_weight": 1.0,
        },
        "label": _score_label(score),
    }


def _score_label(score: float) -> str:
    """Return a human-readable label for a readiness score."""
    if score >= 80:
        return "Ready"
    if score >= 60:
        return "Almost Ready"
    if score >= 40:
        return "Needs Work"
    return "Not Ready"
