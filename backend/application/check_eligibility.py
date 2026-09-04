from __future__ import annotations

from dataclasses import dataclass

from domain.models import EligibilityResult
from domain.ports import PolicyRepository
from domain.services import evaluate_eligibility


@dataclass(frozen=True)
class CheckEligibilityCommand:
    policy_id: int
    member_id: str = ""


class CheckEligibilityService:
    """Application service for the CheckEligibility use case."""

    def __init__(self, policies: PolicyRepository) -> None:
        self._policies = policies

    def execute(self, command: CheckEligibilityCommand) -> EligibilityResult:
        policy = self._policies.get_by_id(command.policy_id)
        return evaluate_eligibility(policy, command.policy_id, command.member_id)
