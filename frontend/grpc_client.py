"""Thin gRPC client used by Flask."""

from __future__ import annotations

import os

import authorization_pb2
import claim_pb2
import eligibility_pb2
import enums_pb2
import grpc
import insurance_service_pb2_grpc

CLAIM_TYPE_FROM_STR = {
    "medical_expense": enums_pb2.CLAIM_TYPE_MEDICAL_EXPENSE,
    "pharmacy": enums_pb2.CLAIM_TYPE_PHARMACY,
    "dental": enums_pb2.CLAIM_TYPE_DENTAL,
}

CLAIM_STATUS_NAME = {
    enums_pb2.CLAIM_STATUS_UNSPECIFIED: "UNSPECIFIED",
    enums_pb2.CLAIM_STATUS_ADJUDICATED: "ADJUDICATED",
    enums_pb2.CLAIM_STATUS_DENIED: "DENIED",
}

ELIGIBILITY_STATUS_NAME = {
    enums_pb2.ELIGIBILITY_STATUS_UNSPECIFIED: "UNSPECIFIED",
    enums_pb2.ELIGIBILITY_STATUS_ACTIVE: "ACTIVE",
    enums_pb2.ELIGIBILITY_STATUS_INACTIVE: "INACTIVE",
    enums_pb2.ELIGIBILITY_STATUS_UNKNOWN: "UNKNOWN",
}

AUTHORIZATION_DECISION_NAME = {
    enums_pb2.AUTHORIZATION_DECISION_UNSPECIFIED: "UNSPECIFIED",
    enums_pb2.AUTHORIZATION_DECISION_APPROVED: "APPROVED",
    enums_pb2.AUTHORIZATION_DECISION_DENIED: "DENIED",
    enums_pb2.AUTHORIZATION_DECISION_NOT_REQUIRED: "NOT_REQUIRED",
}


def _channel():
    host = os.environ.get("GRPC_HOST", "127.0.0.1")
    port = os.environ.get("GRPC_PORT", "50051")
    return grpc.insecure_channel(f"{host}:{port}")


def _stub():
    return insurance_service_pb2_grpc.InsuranceServiceStub(_channel())


def parse_claim_type(value: str) -> int:
    key = (value or "medical_expense").strip().lower()
    return CLAIM_TYPE_FROM_STR.get(key, enums_pb2.CLAIM_TYPE_MEDICAL_EXPENSE)


def check_eligibility(policy_id: int, member_id: str = "") -> dict:
    resp = _stub().CheckEligibility(
        eligibility_pb2.EligibilityRequest(policy_id=policy_id, member_id=member_id)
    )
    return {
        "eligible": resp.eligible,
        "status": ELIGIBILITY_STATUS_NAME.get(resp.status, str(resp.status)),
        "plan_name": resp.plan_name,
        "message": resp.message,
    }


def request_authorization(
    *,
    policy_id: int,
    member_id: str,
    service_code: str,
    provider_id: str,
    in_network: bool,
) -> dict:
    resp = _stub().RequestAuthorization(
        authorization_pb2.AuthorizationRequest(
            policy_id=policy_id,
            member_id=member_id,
            service_code=service_code,
            provider_id=provider_id,
            in_network=in_network,
        )
    )
    return {
        "decision": AUTHORIZATION_DECISION_NAME.get(resp.decision, str(resp.decision)),
        "authorization_id": resp.authorization_id,
        "message": resp.message,
    }


def submit_claim(
    *,
    policy_id: int,
    member_id: str,
    claim_type: str,
    amount: float,
    description: str,
    authorization_id: str,
    provider_id: str,
    in_network: bool,
) -> dict:
    resp = _stub().SubmitClaim(
        claim_pb2.ClaimRequest(
            policy_id=policy_id,
            member_id=member_id,
            type=parse_claim_type(claim_type),
            amount=amount,
            description=description,
            authorization_id=authorization_id,
            provider_id=provider_id,
            in_network=in_network,
        )
    )
    return {
        "claim_id": resp.claim_id,
        "status": CLAIM_STATUS_NAME.get(resp.status, str(resp.status)),
        "billed_amount": resp.billed_amount,
        "negotiated_amount": resp.negotiated_amount,
        "deductible_applied": resp.deductible_applied,
        "coinsurance_patient": resp.coinsurance_patient,
        "patient_responsibility": resp.patient_responsibility,
        "insurer_pays": resp.insurer_pays,
        "message": resp.message,
    }


def run_full_mri_flow(
    *,
    policy_id: int,
    member_id: str,
    amount: float,
    description: str,
    claim_type: str = "medical_expense",
    provider_id: str = "PROV-MRI-01",
    in_network: bool = True,
) -> dict:
    """Demo pipeline: Eligibility → Prior Auth → Claim adjudication."""
    eligibility = check_eligibility(policy_id, member_id)
    if not eligibility["eligible"]:
        return {
            "ok": False,
            "step": "eligibility",
            "eligibility": eligibility,
            "authorization": None,
            "claim": None,
        }

    authorization = request_authorization(
        policy_id=policy_id,
        member_id=member_id,
        service_code="MRI",
        provider_id=provider_id,
        in_network=in_network,
    )
    if authorization["decision"] == "DENIED":
        return {
            "ok": False,
            "step": "authorization",
            "eligibility": eligibility,
            "authorization": authorization,
            "claim": None,
        }

    claim = submit_claim(
        policy_id=policy_id,
        member_id=member_id,
        claim_type=claim_type,
        amount=amount,
        description=description,
        authorization_id=authorization.get("authorization_id", ""),
        provider_id=provider_id,
        in_network=in_network,
    )
    return {
        "ok": claim["status"] == "ADJUDICATED",
        "step": "claim",
        "eligibility": eligibility,
        "authorization": authorization,
        "claim": claim,
    }
