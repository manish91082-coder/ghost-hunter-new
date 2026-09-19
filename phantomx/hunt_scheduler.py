"""Deterministic adaptive hunt scheduler for Polygon route tasks.

The scheduler changes scan frequency, not truth. It cannot certify economics,
promote execution, or suppress an eligible route permanently.

HOT routes are revisited rapidly, WARM routes periodically, and COLD routes are
still guaranteed service through bounded starvation protection.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable


class HuntBand(str, Enum):
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"


@dataclass(frozen=True)
class HuntTask:
    task_id: str
    route_id: str
    last_scanned_block: int
    eligible: bool = True
    recently_positive: bool = False
    recently_rejected_positive: bool = False
    state_changed: bool = False
    newly_discovered: bool = False
    liquidity_score_bps: int = 0
    age_blocks: int = 0
    failures: int = 0

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.route_id.strip():
            raise ValueError("task_id and route_id are required")
        if self.last_scanned_block < 0 or self.age_blocks < 0 or self.failures < 0:
            raise ValueError("block/failure counters must be non-negative")
        if not 0 <= self.liquidity_score_bps <= 10_000:
            raise ValueError("liquidity_score_bps must be in [0, 10000]")


@dataclass(frozen=True)
class ScheduledTask:
    task: HuntTask
    band: HuntBand
    next_due_block: int
    priority: int


HOT_INTERVAL = 1
WARM_INTERVAL = 5
COLD_INTERVAL = 100


def classify(task: HuntTask) -> HuntBand:
    if not task.eligible:
        return HuntBand.COLD
    if task.recently_positive or task.newly_discovered or task.state_changed or task.recently_rejected_positive:
        return HuntBand.HOT
    if task.liquidity_score_bps >= 2500 or task.age_blocks <= WARM_INTERVAL:
        return HuntBand.WARM
    return HuntBand.COLD


def _interval(band: HuntBand) -> int:
    return {HuntBand.HOT: HOT_INTERVAL, HuntBand.WARM: WARM_INTERVAL, HuntBand.COLD: COLD_INTERVAL}[band]


def priority(task: HuntTask, current_block: int) -> int:
    if not task.eligible:
        return 0
    band = classify(task)
    overdue = max(0, current_block - (task.last_scanned_block + _interval(band)))
    base = {HuntBand.HOT: 1000, HuntBand.WARM: 500, HuntBand.COLD: 100}[band]
    score = base
    score += min(400, overdue * 5)
    score += min(200, task.liquidity_score_bps // 50)
    score += min(150, task.failures * 10)
    if task.recently_positive:
        score += 250
    elif task.recently_rejected_positive:
        score += 180
    if task.newly_discovered:
        score += 200
    if task.state_changed:
        score += 175
    return score


def schedule(tasks: Iterable[HuntTask], current_block: int, *, max_tasks: int | None = None) -> tuple[ScheduledTask, ...]:
    if current_block < 0:
        raise ValueError("current_block must be non-negative")
    candidates: list[ScheduledTask] = []
    for task in tasks:
        if not task.eligible:
            continue
        band = classify(task)
        interval = _interval(band)
        next_due = task.last_scanned_block + interval
        candidates.append(ScheduledTask(task, band, next_due, priority(task, current_block)))

    candidates.sort(key=lambda item: (-item.priority, item.next_due_block, item.task.task_id))

    if max_tasks is not None:
        if not isinstance(max_tasks, int) or isinstance(max_tasks, bool) or max_tasks < 1:
            raise ValueError("max_tasks must be a positive integer")
        if len(candidates) <= max_tasks:
            return tuple(candidates)

        selected = candidates[:max_tasks]
        # Starvation guard: ensure a due cold task gets a slot whenever one exists.
        cold_due = [
            item for item in candidates[max_tasks:]
            if item.band is HuntBand.COLD and item.next_due_block <= current_block
        ]
        if cold_due and not any(item.band is HuntBand.COLD and item.next_due_block <= current_block for item in selected):
            selected[-1] = cold_due[0]
            selected.sort(key=lambda item: (-item.priority, item.next_due_block, item.task.task_id))
        return tuple(selected)

    return tuple(candidates)


def stable_task_id(route_id: str, venue_state_hash: str) -> str:
    if not route_id.strip() or not venue_state_hash.strip():
        raise ValueError("route_id and venue_state_hash are required")
    payload = f"{route_id}|{venue_state_hash}".encode()
    return "hunt:" + sha256(payload).hexdigest()
