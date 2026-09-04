"""Domain services — pure business rules (no repository I/O here except via args)."""

from __future__ import annotations

import uuid

from domain.models import (
    AuthorizationDecision,
    AuthorizationResult,
    ClaimResult,
    ClaimStatus,
    ClaimType,
    EligibilityResult,
    EligibilityStatus,
    Policy,
)


def resolve_service_code(claim_type: ClaimType, description: str) -> str:
    text = f"{claim_type.value} {description}".upper()
    if "MRI" in text:
        return "MRI"
    return claim_type.value if claim_type != ClaimType.UNSPECIFIED else "medical_expense"


def evaluate_eligibility(policy: Policy | None, policy_id: int, member_id: str) -> EligibilityResult:
    if policy is None:
        return EligibilityResult(
            eligible=False,
            status=EligibilityStatus.UNKNOWN,
            plan_name="",
            message=f"Policy {policy_id} not found",
        )
    if member_id and member_id != policy.member_id:
        return EligibilityResult(
            eligible=False,
            status=EligibilityStatus.INACTIVE,
            plan_name=policy.plan_name,
            message="Member ID does not match policy",
        )
    if not policy.active:
        return EligibilityResult(
            eligible=False,
            status=EligibilityStatus.INACTIVE,
            plan_name=policy.plan_name,
            message="Policy is not active",
        )
    return EligibilityResult(
        eligible=True,
        status=EligibilityStatus.ACTIVE,
        plan_name=policy.plan_name,
        message=f"Policy {policy.policy_id} is active ({policy.plan_name})",
    )


def evaluate_authorization(
    policy: Policy | None,
    *,
    service_code: str,
    provider_id: str,
    in_network: bool,
) -> AuthorizationResult:
    if policy is None or not policy.active:
        return AuthorizationResult(
            decision=AuthorizationDecision.DENIED,
            authorization_id="",
            message="Policy not found or inactive",
        )

    service = (service_code or "MRI").upper()
    if service not in policy.covered_services:
        return AuthorizationResult(
            decision=AuthorizationDecision.DENIED,
            authorization_id="",
            message=f"Service {service} is not covered by the plan",
        )

    if not in_network or provider_id not in policy.in_network_providers:
        return AuthorizationResult(
            decision=AuthorizationDecision.DENIED,
            authorization_id="",
            message="Provider is out of network or unknown",
        )

    if service not in policy.requires_prior_auth:
        return AuthorizationResult(
            decision=AuthorizationDecision.NOT_REQUIRED,
            authorization_id="",
            message=f"Prior authorization not required for {service}",
        )

    auth_id = f"AUTH-{uuid.uuid4().hex[:8].upper()}"
    return AuthorizationResult(
        decision=AuthorizationDecision.APPROVED,
        authorization_id=auth_id,
        message=f"{service} authorized for in-network provider {provider_id}",
    )


def adjudicate_claim(
    policy: Policy | None,
    *,
    claim_type: ClaimType,
    amount: float,
    description: str,
    authorization_id: str,
    provider_id: str,
    in_network: bool,
) -> ClaimResult:
    billed = float(amount) if amount > 0 else 0.0

    if policy is None or not policy.active:
        return ClaimResult(
            claim_id="",
            status=ClaimStatus.DENIED,
            billed_amount=billed,
            negotiated_amount=0.0,
            deductible_applied=0.0,
            coinsurance_patient=0.0,
            patient_responsibility=0.0,
            insurer_pays=0.0,
            message="Policy not found or inactive on date of service",
        )

    service = resolve_service_code(claim_type, description)

    if service not in policy.covered_services:
        return ClaimResult(
            claim_id="",
            status=ClaimStatus.DENIED,
            billed_amount=billed,
            negotiated_amount=0.0,
            deductible_applied=0.0,
            coinsurance_patient=0.0,
            patient_responsibility=0.0,
            insurer_pays=0.0,
            message=f"Procedure {service} is not covered",
        )

    if not in_network or provider_id not in policy.in_network_providers:
        return ClaimResult(
            claim_id="",
            status=ClaimStatus.DENIED,
            billed_amount=billed,
            negotiated_amount=0.0,
            deductible_applied=0.0,
            coinsurance_patient=0.0,
            patient_responsibility=0.0,
            insurer_pays=0.0,
            message="Provider was not valid / out of network",
        )

    if service in policy.requires_prior_auth and not authorization_id:
        return ClaimResult(
            claim_id="",
            status=ClaimStatus.DENIED,
            billed_amount=billed,
            negotiated_amount=0.0,
            deductible_applied=0.0,
            coinsurance_patient=0.0,
            patient_responsibility=0.0,
            insurer_pays=0.0,
            message="Prior authorization required but missing",
        )

    negotiated = float(policy.negotiated_rates.get(service, billed or 1000.0))
    deductible = min(policy.deductible_remaining, negotiated)
    remaining = negotiated - deductible
    coinsurance = remaining * policy.coinsurance_patient_pct
    patient = deductible + coinsurance
    insurer = negotiated - patient
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"

    return ClaimResult(
        claim_id=claim_id,
        status=ClaimStatus.ADJUDICATED,
        billed_amount=billed,
        negotiated_amount=negotiated,
        deductible_applied=deductible,
        coinsurance_patient=coinsurance,
        patient_responsibility=patient,
        insurer_pays=insurer,
        message=f"Adjudicated {service}: patient ${patient:.2f}, insurer ${insurer:.2f}",
    )
