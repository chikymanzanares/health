from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EligibilityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"


class AuthorizationDecision(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    NOT_REQUIRED = "NOT_REQUIRED"


class ClaimType(str, Enum):
    UNSPECIFIED = "unspecified"
    MEDICAL_EXPENSE = "medical_expense"
    PHARMACY = "pharmacy"
    DENTAL = "dental"


class ClaimStatus(str, Enum):
    ADJUDICATED = "ADJUDICATED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class Policy:
    policy_id: int
    member_id: str
    plan_name: str
    active: bool
    deductible_remaining: float
    coinsurance_patient_pct: float
    in_network_providers: frozenset[str]
    covered_services: frozenset[str]
    requires_prior_auth: frozenset[str]
    negotiated_rates: dict[str, float]


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    status: EligibilityStatus
    plan_name: str
    message: str


@dataclass(frozen=True)
class AuthorizationResult:
    decision: AuthorizationDecision
    authorization_id: str
    message: str


@dataclass(frozen=True)
class ClaimResult:
    claim_id: str
    status: ClaimStatus
    billed_amount: float
    negotiated_amount: float
    deductible_applied: float
    coinsurance_patient: float
    patient_responsibility: float
    insurer_pays: float
    message: str
