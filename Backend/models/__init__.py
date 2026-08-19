"""
Domain models for the Seva-AI eligibility engine.
"""

from Backend.models.profile import (
    Gender,
    MaritalStatus,
    SocialCategory,
    UserProfile,
)
from Backend.models.results import (
    ConditionResult,
    ConditionStatus,
    EligibilityResult,
    OverallResult,
)
from Backend.models.scheme import Scheme

__all__ = [
    "ConditionResult",
    "ConditionStatus",
    "EligibilityResult",
    "Gender",
    "MaritalStatus",
    "OverallResult",
    "Scheme",
    "SocialCategory",
    "UserProfile",
]