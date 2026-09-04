"""Ports (interfaces) — implemented by infrastructure adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models import Policy


class PolicyRepository(ABC):
    """Outbound port: load insurance policies regardless of storage."""

    @abstractmethod
    def get_by_id(self, policy_id: int) -> Policy | None:
        raise NotImplementedError
