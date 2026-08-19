"""
Document checker for the Seva-AI backend.

Compares documents required by eligible schemes against documents
held by the user.
"""

from __future__ import annotations

from Backend.models.profile import UserProfile


def check_documents(profile: UserProfile) -> dict:
    """
    Compare required documents against documents held by the user.

    Returns a summary of required, held, and missing documents.
    """
    held = set(profile.documents_held)

    # Minimal implementation: report the user's held documents.
    # Full document-requirement matching requires the ``required_documents``
    # column, which is not yet present in the MySQL schema.
    return {
        "held_documents": sorted(held),
        "missing_documents": [],
        "note": "Document requirements per scheme are not yet available in the database.",
    }