"""Deterministic event-driven HOT-route detector.

Consumes already decoded inventory logs and converts state-change events into
route scheduler hints. No pricing or execution decisions are made here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping

from .hunt_scheduler import HuntTask


HOT_EVENT_TOPICS = frozenset({
    "POOL_CREATED",
    "POOL_INITIALIZED",
    "SWAP",
    "MINT",
    "BURN",
    "LIQUIDITY_CHANGED",
    "FLASH_LIQUIDITY_CHANGED",
})


@dataclass(frozen=True)
class HotTrigger:
    event_id: str
    route_id: str
    block_number: int
    reason: str
    state_hash: str


def state_hash(payload: Mapping[str, object]) -> str:
    import json
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def triggers_from_events(
    events: Iterable[Mapping[str, object]],
    route_ids_by_pool: Mapping[str, Iterable[str]],
) -> tuple[HotTrigger, ...]:
    result: list[HotTrigger] = []
    for event in events:
        topic = str(event.get("topic", "")).upper()
        pool = str(event.get("pool", "")).lower()
        if topic not in HOT_EVENT_TOPICS or not pool:
            continue
        block = int(event.get("block_number", 0))
        payload_hash = state_hash(event)
        for route_id in sorted(set(route_ids_by_pool.get(pool, ()))):
            event_id = str(event.get("transaction_hash", "")) + ":" + str(event.get("log_index", ""))
            result.append(HotTrigger(event_id, route_id, block, topic, payload_hash))
    unique = {(x.event_id, x.route_id): x for x in result}
    return tuple(sorted(unique.values(), key=lambda x: (x.block_number, x.route_id, x.event_id)))


def apply_hot_triggers(
    tasks: Iterable[HuntTask],
    triggers: Iterable[HotTrigger],
) -> tuple[HuntTask, ...]:
    by_route = {trigger.route_id for trigger in triggers}
    out = []
    for task in tasks:
        if task.route_id in by_route:
            out.append(
                HuntTask(
                    task_id=task.task_id,
                    route_id=task.route_id,
                    last_scanned_block=task.last_scanned_block,
                    eligible=task.eligible,
                    recently_positive=task.recently_positive,
                    recently_rejected_positive=task.recently_rejected_positive,
                    state_changed=True,
                    newly_discovered=task.newly_discovered,
                    liquidity_score_bps=task.liquidity_score_bps,
                    age_blocks=task.age_blocks,
                    failures=task.failures,
                )
            )
        else:
            out.append(task)
    return tuple(out)
