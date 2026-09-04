"""gRPC inbound adapter — maps protobuf ↔ application use cases."""

from __future__ import annotations

from application.check_eligibility import CheckEligibilityCommand, CheckEligibilityService
from application.request_authorization import (
    RequestAuthorizationCommand,
    RequestAuthorizationService,
)
from application.submit_claim import SubmitClaimCommand, SubmitClaimService
from domain.models import (
    AuthorizationDecision,
    ClaimStatus,
    ClaimType,
    EligibilityStatus,
)
from infrastructure.grpc.generated import (
    authorization_pb2,
    claim_pb2,
    eligibility_pb2,
    enums_pb2,
    insurance_service_pb2_grpc,
)

_CLAIM_TYPE_FROM_PROTO = {
    enums_pb2.CLAIM_TYPE_UNSPECIFIED: ClaimType.UNSPECIFIED,
    enums_pb2.CLAIM_TYPE_MEDICAL_EXPENSE: ClaimType.MEDICAL_EXPENSE,
    enums_pb2.CLAIM_TYPE_PHARMACY: ClaimType.PHARMACY,
    enums_pb2.CLAIM_TYPE_DENTAL: ClaimType.DENTAL,
}

_ELIGIBILITY_TO_PROTO = {
    EligibilityStatus.ACTIVE: enums_pb2.ELIGIBILITY_STATUS_ACTIVE,
    EligibilityStatus.INACTIVE: enums_pb2.ELIGIBILITY_STATUS_INACTIVE,
    EligibilityStatus.UNKNOWN: enums_pb2.ELIGIBILITY_STATUS_UNKNOWN,
}

_AUTH_TO_PROTO = {
    AuthorizationDecision.APPROVED: enums_pb2.AUTHORIZATION_DECISION_APPROVED,
    AuthorizationDecision.DENIED: enums_pb2.AUTHORIZATION_DECISION_DENIED,
    AuthorizationDecision.NOT_REQUIRED: enums_pb2.AUTHORIZATION_DECISION_NOT_REQUIRED,
}

_CLAIM_STATUS_TO_PROTO = {
    ClaimStatus.ADJUDICATED: enums_pb2.CLAIM_STATUS_ADJUDICATED,
    ClaimStatus.DENIED: enums_pb2.CLAIM_STATUS_DENIED,
}


class InsuranceGrpcServicer(insurance_service_pb2_grpc.InsuranceServiceServicer):
    def __init__(
        self,
        check_eligibility: CheckEligibilityService,
        request_authorization: RequestAuthorizationService,
        submit_claim: SubmitClaimService,
    ) -> None:
        self._check_eligibility = check_eligibility
        self._request_authorization = request_authorization
        self._submit_claim = submit_claim

    def CheckEligibility(self, request, context):
        result = self._check_eligibility.execute(
            CheckEligibilityCommand(
                policy_id=request.policy_id,
                member_id=request.member_id,
            )
        )
        return eligibility_pb2.EligibilityResponse(
            eligible=result.eligible,
            status=_ELIGIBILITY_TO_PROTO[result.status],
            plan_name=result.plan_name,
            message=result.message,
        )

    def RequestAuthorization(self, request, context):
        result = self._request_authorization.execute(
            RequestAuthorizationCommand(
                policy_id=request.policy_id,
                member_id=request.member_id,
                service_code=request.service_code,
                provider_id=request.provider_id,
                in_network=request.in_network,
            )
        )
        return authorization_pb2.AuthorizationResponse(
            decision=_AUTH_TO_PROTO[result.decision],
            authorization_id=result.authorization_id,
            message=result.message,
        )

    def SubmitClaim(self, request, context):
        claim_type = _CLAIM_TYPE_FROM_PROTO.get(
            request.type, ClaimType.MEDICAL_EXPENSE
        )
        result = self._submit_claim.execute(
            SubmitClaimCommand(
                policy_id=request.policy_id,
                member_id=request.member_id,
                claim_type=claim_type,
                amount=request.amount,
                description=request.description,
                authorization_id=request.authorization_id,
                provider_id=request.provider_id,
                in_network=request.in_network,
            )
        )
        return claim_pb2.ClaimResponse(
            claim_id=result.claim_id,
            status=_CLAIM_STATUS_TO_PROTO[result.status],
            billed_amount=result.billed_amount,
            negotiated_amount=result.negotiated_amount,
            deductible_applied=result.deductible_applied,
            coinsurance_patient=result.coinsurance_patient,
            patient_responsibility=result.patient_responsibility,
            insurer_pays=result.insurer_pays,
            message=result.message,
        )
