from __future__ import annotations

from dataclasses import dataclass

from domain.models import AuthorizationResult
from domain.ports import PolicyRepository
from domain.services import evaluate_authorization


@dataclass(frozen=True)
class RequestAuthorizationCommand:
    policy_id: int
    member_id: str
    service_code: str
    provider_id: str
    in_network: bool


class RequestAuthorizationService:
    """Application service for the RequestAuthorization use case."""

    def __init__(self, policies: PolicyRepository) -> None:
        self._policies = policies

    def execute(self, command: RequestAuthorizationCommand) -> AuthorizationResult:
        policy = self._policies.get_by_id(command.policy_id)
        return evaluate_authorization(
            policy,
            service_code=command.service_code,
            provider_id=command.provider_id,
            in_network=command.in_network,
        )
