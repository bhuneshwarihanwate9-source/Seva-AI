"""
API route definitions for the Seva-AI backend.

Exposes the existing eligibility engine and related services through
FastAPI endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from Backend.models.profile import UserProfile
from Backend.models.results import EligibilityResult
from Backend.services.eligibility_engine import evaluate_scheme
from Backend.services.document_checker import check_documents
from Backend.services.readiness_scorer import score_readiness
from Backend.services.future_opportunities import find_future_opportunities

router = APIRouter(prefix="/api", tags=["eligibility"])


@router.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/eligibility/check", response_model=list[EligibilityResult])
def eligibility_check(profile: UserProfile) -> list[EligibilityResult]:
    """
    Evaluate a user profile against all available schemes.

    Returns a list of ``EligibilityResult`` objects, one per scheme,
    sorted by confidence score (highest first).
    """
    from Backend.services.data_loader import load_all_schemes

    schemes = load_all_schemes()
    results = [evaluate_scheme(profile, scheme) for scheme in schemes]
    results.sort(key=lambda r: r.confidence_score, reverse=True)
    return results


@router.post("/documents/check")
def documents_check(profile: UserProfile) -> dict:
    """
    Compare required documents against documents held by the user.

    Returns a summary of required, held, and missing documents.
    """
    return check_documents(profile)


@router.post("/readiness/check")
def readiness_check(profile: UserProfile) -> dict:
    """
    Compute a 0–100 readiness score for the user profile.

    Returns the overall readiness score and per-scheme breakdown.
    """
    return score_readiness(profile)


@router.post("/future-opportunities/check")
def future_opportunities_check(profile: UserProfile) -> dict:
    """
    Identify schemes the user is currently ineligible for but could
    become eligible for with a deterministic change (e.g., age).

    Returns a list of near-miss opportunities.
    """
    return find_future_opportunities(profile)