"""In-memory PolicyRepository — demo persistence adapter."""

from __future__ import annotations

from domain.models import Policy
from domain.ports import PolicyRepository

_SEED: dict[int, Policy] = {
    1001: Policy(
        policy_id=1001,
        member_id="M-1001",
        plan_name="Gold PPO",
        active=True,
        deductible_remaining=200.0,
        coinsurance_patient_pct=0.20,
        in_network_providers=frozenset({"PROV-MRI-01", "PROV-HOSP-01"}),
        covered_services=frozenset({"MRI", "medical_expense", "pharmacy", "dental"}),
        requires_prior_auth=frozenset({"MRI"}),
        negotiated_rates={"MRI": 1000.0, "medical_expense": 1000.0},
    ),
    1002: Policy(
        policy_id=1002,
        member_id="M-1002",
        plan_name="Silver HMO",
        active=True,
        deductible_remaining=500.0,
        coinsurance_patient_pct=0.30,
        in_network_providers=frozenset({"PROV-MRI-01"}),
        covered_services=frozenset({"MRI", "medical_expense", "pharmacy"}),
        requires_prior_auth=frozenset({"MRI"}),
        negotiated_rates={"MRI": 1000.0, "medical_expense": 1000.0},
    ),
    1999: Policy(
        policy_id=1999,
        member_id="M-1999",
        plan_name="Expired Basic",
        active=False,
        deductible_remaining=0.0,
        coinsurance_patient_pct=0.50,
        in_network_providers=frozenset(),
        covered_services=frozenset(),
        requires_prior_auth=frozenset(),
        negotiated_rates={},
    ),
}


class InMemoryPolicyRepository(PolicyRepository):
    def __init__(self, policies: dict[int, Policy] | None = None) -> None:
        self._policies = dict(policies if policies is not None else _SEED)

    def get_by_id(self, policy_id: int) -> Policy | None:
        return self._policies.get(policy_id)
