#!/usr/bin/env python3
"""Read-only Polygon venue inventory slice runner.

One invocation processes a bounded block window for the registered venue specs.
The output is a deterministic checkpoint artifact that can be consumed by the
next slice. No signing, submission, broadcast, or production capital path exists.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.polygon_universe_inventory import InventoryTask, run_inventory_task
from phantomx.polygon_venue_inventory import VENUE_SPECS
from phantomx.rpc_failover import build_free_polygon_rpc_pool

DEFAULT_SLICE_BLOCKS = 25_000
MIN_START_BLOCK = 0


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def _spec_order() -> tuple[str, ...]:
    requested = os.getenv("PHANTOMX_INVENTORY_VENUES", "").strip()
    known = {spec.venue_id for spec in VENUE_SPECS}
    if not requested:
        return tuple(spec.venue_id for spec in VENUE_SPECS)
    names = tuple(item.strip() for item in requested.split(",") if item.strip())
    unknown = sorted(set(names) - known)
    if unknown:
        raise ValueError(f"unknown inventory venue(s): {unknown}")
    return names


def _hash_payload(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    started = time.time()
    from_block = _int_env("PHANTOMX_INVENTORY_FROM_BLOCK", MIN_START_BLOCK)
    slice_blocks = _int_env("PHANTOMX_INVENTORY_SLICE_BLOCKS", DEFAULT_SLICE_BLOCKS)
    if slice_blocks < 1:
        raise ValueError("PHANTOMX_INVENTORY_SLICE_BLOCKS must be >= 1")
    to_block = _int_env("PHANTOMX_INVENTORY_TO_BLOCK", -1)
    pool = build_free_polygon_rpc_pool()

    if to_block < 0:
        raw_head = pool.call("eth_blockNumber", [])
        to_block = int(str(raw_head), 16)
    if to_block < from_block:
        raise ValueError("inventory end block is before start block")

    slice_to = min(to_block, from_block + slice_blocks - 1)
    selected = _spec_order()
    spec_by_id = {spec.venue_id: spec for spec in VENUE_SPECS}

    tasks = []
    failures = []
    for venue_id in selected:
        task = InventoryTask(venue_id, from_block, slice_to, chunk_size=2000)
        result = run_inventory_task(pool, spec_by_id[venue_id], task)
        item = {
            "task": asdict(result.task),
            "status": result.status,
            "error": result.error,
            "edge_count": len(result.edges),
            "log_count": len(result.logs),
            "evidence_hash": result.evidence_hash,
            "edges": [asdict(edge) for edge in result.edges],
        }
        tasks.append(item)
        if result.status == "RPC_EXHAUSTED":
            failures.append(item)

    next_start = slice_to + 1 if slice_to < to_block else None
    checkpoint = {
        "schema_version": 1,
        "mission": "PHANTOMX POLYGON VENUE INVENTORY SLICE",
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "chain_id": 137,
        "from_block": from_block,
        "to_block": slice_to,
        "head_observed": to_block,
        "next_start_block": next_start,
        "slice_blocks": slice_blocks,
        "venues": selected,
        "tasks": tasks,
        "rpc_pool": {
            "provider_count": len(pool.records),
            "failure_count": len(pool.failure_history()),
            "provider_stats": list(pool.provider_stats()),
        },
        "provenance": {
            "git_commit_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.environ.get("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "duration_seconds": round(time.time() - started, 3),
    }
    checkpoint["checkpoint_hash"] = _hash_payload(checkpoint)

    Path("artifacts").mkdir(exist_ok=True)
    out = Path("artifacts/polygon_inventory_slice.json")
    out.write_text(json.dumps(checkpoint, indent=2, sort_keys=True), encoding="utf-8")

    print(
        f"Inventory slice {from_block}-{slice_to}/{to_block}: "
        f"venues={len(selected)} rpc_failures={len(pool.failure_history())} "
        f"next={next_start}",
        flush=True,
    )
    print(f"Wrote {out}", flush=True)

    # Infrastructure exhaustion is evidence requiring requeue, not a clean
    # market-negative result. Fail CI so the scheduler can retry the slice.
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
