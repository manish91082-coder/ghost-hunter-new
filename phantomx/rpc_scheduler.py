"""Bounded Polygon RPC provider fleet scheduler.

The registry may contain hundreds of provider records, but each task is sent
only to a bounded active subset. This module is scheduling policy only: it
performs no network calls and holds no credentials.

Safety invariants:
- no endpoint fan-out beyond max_active
- unhealthy/circuit-open providers are excluded
- provider identity is preserved in every assignment
- per-provider task concurrency is bounded
- failures advance circuit state rather than triggering unbounded retries
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Iterable


class RPCSchedulerError(ValueError):
    """Raised when provider scheduling input is unsafe."""


@dataclass
class RPCProviderState:
    provider_id: str
    endpoint_url: str
    chain_id: int = 137
    enabled: bool = True
    health_score: float = 1.0
    consecutive_failures: int = 0
    in_flight: int = 0
    max_concurrency: int = 2
    circuit_open_until: float = 0.0
    last_success_monotonic: float = 0.0

    def eligible(self, now: float) -> bool:
        return (
            self.enabled
            and self.chain_id == 137
            and self.circuit_open_until <= now
            and self.in_flight < self.max_concurrency
            and self.max_concurrency > 0
            and self.health_score > 0
        )


@dataclass(frozen=True)
class ProviderAssignment:
    provider_id: str
    endpoint_url: str
    task_id: str


@dataclass
class RPCProviderScheduler:
    providers: dict[str, RPCProviderState]
    max_active: int = 4
    failure_threshold: int = 3
    circuit_cooldown_seconds: float = 30.0
    _cursor: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not 1 <= self.max_active <= 32:
            raise RPCSchedulerError("max_active must be between 1 and 32")
        if not 1 <= self.failure_threshold <= 20:
            raise RPCSchedulerError("failure_threshold must be between 1 and 20")
        if self.circuit_cooldown_seconds <= 0:
            raise RPCSchedulerError("circuit cooldown must be positive")
        for provider_id, state in self.providers.items():
            if provider_id != state.provider_id:
                raise RPCSchedulerError("provider dictionary key must match provider_id")
            if not state.endpoint_url.startswith(("https://", "http://")):
                raise RPCSchedulerError("provider endpoint must use HTTP(S)")
            if state.chain_id != 137:
                raise RPCSchedulerError("scheduler is Polygon-mainnet only")
            if not 1 <= state.max_concurrency <= 8:
                raise RPCSchedulerError("provider max_concurrency must be 1..8")

    @classmethod
    def from_records(
        cls,
        records: Iterable[dict],
        *,
        max_active: int = 4,
        failure_threshold: int = 3,
        circuit_cooldown_seconds: float = 30.0,
    ) -> "RPCProviderScheduler":
        states: dict[str, RPCProviderState] = {}
        for record in records:
            if not isinstance(record, dict):
                raise RPCSchedulerError("provider record must be an object")
            pid = record.get("provider_id")
            endpoint = record.get("endpoint_url")
            if not isinstance(pid, str) or not pid.strip():
                raise RPCSchedulerError("provider_id is required")
            if pid in states:
                raise RPCSchedulerError("duplicate provider_id")
            states[pid] = RPCProviderState(
                provider_id=pid,
                endpoint_url=endpoint,
                chain_id=int(record.get("chain_id", 137)),
                enabled=bool(record.get("enabled", True)),
                health_score=float(record.get("health_score", 1.0)),
                max_concurrency=int(record.get("max_concurrency", 2)),
            )
        return cls(
            states,
            max_active=max_active,
            failure_threshold=failure_threshold,
            circuit_cooldown_seconds=circuit_cooldown_seconds,
        )

    def select(self, *, task_ids: Iterable[str], now: float | None = None) -> tuple[ProviderAssignment, ...]:
        """Assign tasks to a bounded active provider set without duplicate fan-out."""
        tasks = tuple(task_ids)
        if any(not isinstance(t, str) or not t.strip() for t in tasks):
            raise RPCSchedulerError("task ids must be non-empty strings")
        if not tasks:
            return tuple()
        current = monotonic() if now is None else float(now)
        candidates = [p for p in self.providers.values() if p.eligible(current)]
        candidates.sort(
            key=lambda p: (-p.health_score, p.in_flight, p.provider_id)
        )
        active = candidates[: self.max_active]
        if not active:
            raise RPCSchedulerError("no eligible Polygon RPC providers")
        assignments: list[ProviderAssignment] = []
        for index, task_id in enumerate(tasks):
            provider = active[index % len(active)]
            if provider.in_flight >= provider.max_concurrency:
                # Find the least-loaded eligible active provider with capacity.
                available = [p for p in active if p.in_flight < p.max_concurrency]
                if not available:
                    break
                provider = min(available, key=lambda p: (p.in_flight, -p.health_score, p.provider_id))
            provider.in_flight += 1
            assignments.append(ProviderAssignment(provider.provider_id, provider.endpoint_url, task_id))
        return tuple(assignments)

    def record_success(self, provider_id: str, *, now: float | None = None) -> None:
        state = self._state(provider_id)
        state.in_flight = max(0, state.in_flight - 1)
        state.consecutive_failures = 0
        state.health_score = min(1.0, state.health_score * 0.8 + 0.2)
        state.last_success_monotonic = monotonic() if now is None else float(now)

    def record_failure(self, provider_id: str, *, now: float | None = None) -> None:
        state = self._state(provider_id)
        state.in_flight = max(0, state.in_flight - 1)
        state.consecutive_failures += 1
        state.health_score = max(0.0, state.health_score * 0.7)
        if state.consecutive_failures >= self.failure_threshold:
            current = monotonic() if now is None else float(now)
            state.circuit_open_until = current + self.circuit_cooldown_seconds

    def _state(self, provider_id: str) -> RPCProviderState:
        try:
            return self.providers[provider_id]
        except KeyError as exc:
            raise RPCSchedulerError("unknown provider") from exc

