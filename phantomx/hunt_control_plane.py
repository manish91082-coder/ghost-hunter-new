"""Adaptive discovery control plane for the Polygon hunt MVP.

Combines:
Inventory snapshot -> strategy-family generation -> coverage ledger -> HOT/WARM/COLD scheduler.
This is planning-only. It never signs, submits, or overrides deterministic economics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .coverage_ledger import CoverageLedger, CoverageStatus, CoverageTask
from .hunt_scheduler import HuntTask, ScheduledTask, schedule, stable_task_id
from .polygon_market_snapshot import MarketSnapshot
from .strategy_search_space import StrategyCandidate, StrategyFamily, generate_candidates


@dataclass(frozen=True)
class HuntPlan:
    strategy_family: StrategyFamily
    candidates: tuple[StrategyCandidate, ...]
    scheduled: tuple[ScheduledTask, ...]


def build_plan(
    snapshot: MarketSnapshot,
    *,
    base_token: str,
    current_block: int,
    family: StrategyFamily,
    coverage: CoverageLedger,
    max_tasks: int | None = None,
) -> HuntPlan:
    if current_block < 0:
        raise ValueError("current_block must be non-negative")

    if family is StrategyFamily.DIRECT_CROSS_VENUE:
        cycles = snapshot.cycles_2_leg
    elif family is StrategyFamily.TRIANGULAR:
        cycles = snapshot.cycles_3_leg
    elif family is StrategyFamily.FOUR_LEG:
        cycles = snapshot.cycles_4_leg
    else:
        # Same-venue and mixed-curve families can draw from all bounded cycles.
        cycles = (*snapshot.cycles_2_leg, *snapshot.cycles_3_leg, *snapshot.cycles_4_leg)

    candidates = generate_candidates(cycles, family)
    tasks: list[HuntTask] = []
    for candidate in candidates:
        state_hash = snapshot_state_hash(snapshot)
        task_id = stable_task_id(candidate.cycle.route_id, state_hash)
        record = coverage.get(task_id)
        if record is not None and record.status in {
            CoverageStatus.QUOTED,
            CoverageStatus.ONCHAIN_UNAVAILABLE,
            CoverageStatus.RISK_REJECTED,
            CoverageStatus.ECONOMIC_REJECTED,
            CoverageStatus.ADAPTER_UNAVAILABLE,
        }:
            continue
        tasks.append(
            HuntTask(
                task_id=task_id,
                route_id=candidate.cycle.route_id,
                last_scanned_block=record.task.universe_block if record else 0,
                recently_positive=bool(record and record.status is CoverageStatus.QUOTED),
                recently_rejected_positive=bool(record and record.status is CoverageStatus.ECONOMIC_REJECTED),
                newly_discovered=record is None,
                failures=record.attempts if record and record.status is CoverageStatus.RPC_EXHAUSTED else 0,
            )
        )

    scheduled = schedule(tasks, current_block, max_tasks=max_tasks)
    return HuntPlan(family, candidates, scheduled)


def snapshot_state_hash(snapshot: MarketSnapshot) -> str:
    import hashlib
    payload = "|".join(edge.edge_id for edge in snapshot.edges).encode()
    return hashlib.sha256(payload).hexdigest()


def plan_all_families(
    snapshot: MarketSnapshot,
    *,
    base_token: str,
    current_block: int,
    coverage: CoverageLedger,
    max_tasks_per_family: int | None = None,
) -> tuple[HuntPlan, ...]:
    families = (
        StrategyFamily.DIRECT_CROSS_VENUE,
        StrategyFamily.SAME_VENUE_POOL_DISLOCATION,
        StrategyFamily.TRIANGULAR,
        StrategyFamily.FOUR_LEG,
        StrategyFamily.MIXED_CURVE,
    )
    return tuple(
        build_plan(
            snapshot,
            base_token=base_token,
            current_block=current_block,
            family=family,
            coverage=coverage,
            max_tasks=max_tasks_per_family,
        )
        for family in families
    )
