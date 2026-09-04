"""Composition root — wire ports/adapters and start the gRPC server."""

from __future__ import annotations

import logging

from application.check_eligibility import CheckEligibilityService
from application.request_authorization import RequestAuthorizationService
from application.submit_claim import SubmitClaimService
from infrastructure.grpc.server import serve
from infrastructure.grpc.servicer import InsuranceGrpcServicer
from infrastructure.persistence.in_memory_policy_repository import (
    InMemoryPolicyRepository,
)

logging.basicConfig(level=logging.INFO)


def main() -> None:
    policies = InMemoryPolicyRepository()

    check_eligibility = CheckEligibilityService(policies)
    request_authorization = RequestAuthorizationService(policies)
    submit_claim = SubmitClaimService(policies)

    servicer = InsuranceGrpcServicer(
        check_eligibility=check_eligibility,
        request_authorization=request_authorization,
        submit_claim=submit_claim,
    )
    serve(servicer)


if __name__ == "__main__":
    main()
