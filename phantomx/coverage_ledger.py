"""Evidence coverage ledger for exhaustive Polygon hunt tasks.

A task is considered searched only when it reaches a terminal evidence state.
RPC_EXHAUSTED is explicitly retryable and never equivalent to NO_OPPORTUNITY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Iterable


class CoverageStatus(str, Enum):
    PENDING = "PENDING"
    IN_FLIGHT = "IN_FLIGHT"
    QUOTED = "QUOTED"
    ONCHAIN_UNAVAILABLE = "ONCHAIN_UNAVAILABLE"
    RISK_REJECTED = "RISK_REJECTED"
    ECONOMIC_REJECTED = "ECONOMIC_REJECTED"
    RPC_EXHAUSTED = "RPC_EXHAUSTED"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"


TERMINAL = frozenset({
    CoverageStatus.QUOTED,
    CoverageStatus.ONCHAIN_UNAVAILABLE,
    CoverageStatus.RISK_REJECTED,
    CoverageStatus.ECONOMIC_REJECTED,
    CoverageStatus.ADAPTER_UNAVAILABLE,
})
RETRYABLE = frozenset({CoverageStatus.RPC_EXHAUSTED})


@dataclass(frozen=True)
class CoverageTask:
    task_id: str
    strategy_family: str
    route_id: str
    universe_block: int

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.strategy_family.strip() or not self.route_id.strip():
            raise ValueError("task_id, strategy_family and route_id are required")
        if self.universe_block < 0:
            raise ValueError("universe_block must be non-negative")


@dataclass(frozen=True)
class CoverageRecord:
    task: CoverageTask
    status: CoverageStatus
    evidence_hash: str
    attempts: int = 1

    def __post_init__(self) -> None:
        if not self.evidence_hash.strip():
            raise ValueError("evidence_hash is required")
        if self.attempts < 1:
            raise ValueError("attempts must be >= 1")


@dataclass
class CoverageLedger:
    _records: dict[str, CoverageRecord] = field(default_factory=dict)

    def upsert(self, record: CoverageRecord) -> None:
        previous = self._records.get(record.task.task_id)
        if previous is not None and record.attempts < previous.attempts:
            raise ValueError("attempt count cannot decrease")
        self._records[record.task.task_id] = record

    def get(self, task_id: str) -> CoverageRecord | None:
        return self._records.get(task_id)

    def retryable(self) -> tuple[CoverageRecord, ...]:
        return tuple(
            sorted(
                (record for record in self._records.values() if record.status in RETRYABLE),
                key=lambda record: record.task.task_id,
            )
        )

    def incomplete(self) -> tuple[CoverageRecord, ...]:
        return tuple(
            sorted(
                (record for record in self._records.values() if record.status not in TERMINAL),
                key=lambda record: record.task.task_id,
            )
        )

    def is_exhausted(self, expected_task_ids: Iterable[str] | None = None) -> bool:
        if expected_task_ids is None:
            records = tuple(self._records.values())
        else:
            expected = tuple(expected_task_ids)
            records = tuple(self._records.get(task_id) for task_id in expected)
            if any(record is None for record in records):
                return False
        return bool(records) and all(record.status in TERMINAL for record in records)

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in CoverageStatus}
        for record in self._records.values():
            counts[record.status.value] += 1
        counts["TOTAL"] = len(self._records)
        counts["TERMINAL"] = sum(
            counts[status.value] for status in TERMINAL
        )
        counts["RETRYABLE"] = sum(
            counts[status.value] for status in RETRYABLE
        )
        return counts

    def snapshot_hash(self) -> str:
        payload = "|".join(
            f"{r.task.task_id}:{r.task.strategy_family}:{r.task.route_id}:{r.task.universe_block}:{r.status.value}:{r.evidence_hash}:{r.attempts}"
            for r in sorted(self._records.values(), key=lambda x: x.task.task_id)
        ).encode()
        return sha256(payload).hexdigest()
