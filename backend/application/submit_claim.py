from __future__ import annotations

from dataclasses import dataclass

from domain.models import ClaimResult, ClaimType
from domain.ports import PolicyRepository
from domain.services import adjudicate_claim


@dataclass(frozen=True)
class SubmitClaimCommand:
    policy_id: int
    member_id: str
    claim_type: ClaimType
    amount: float
    description: str
    authorization_id: str
    provider_id: str
    in_network: bool


class SubmitClaimService:
    """Application service for the SubmitClaim use case."""

    def __init__(self, policies: PolicyRepository) -> None:
        self._policies = policies

    def execute(self, command: SubmitClaimCommand) -> ClaimResult:
        policy = self._policies.get_by_id(command.policy_id)
        return adjudicate_claim(
            policy,
            claim_type=command.claim_type,
            amount=command.amount,
            description=command.description,
            authorization_id=command.authorization_id,
            provider_id=command.provider_id,
            in_network=command.in_network,
        )
