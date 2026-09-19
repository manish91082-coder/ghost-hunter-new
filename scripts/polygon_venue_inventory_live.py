#!/usr/bin/env python3
"""Live read-only Polygon venue inventory runner."""
from __future__ import annotations
import json, os, sys, time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.polygon_universe_inventory import InventoryTask, run_inventory_task
from phantomx.polygon_venue_inventory import VENUE_SPECS
from phantomx.rpc_failover import build_free_polygon_rpc_pool

def _int_env(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value

def _spec():
    venue = os.getenv("PHANTOMX_INVENTORY_VENUE", "").strip()
    matches = [spec for spec in VENUE_SPECS if spec.venue_id == venue]
    if len(matches) != 1:
        raise ValueError(f"unknown PHANTOMX_INVENTORY_VENUE: {venue!r}")
    return matches[0]

def _resolve_range(rpc_pool) -> tuple[int, int, str]:
    latest = int(str(rpc_pool.call("eth_blockNumber", [])), 16)
    explicit_from = _int_env("PHANTOMX_INVENTORY_FROM_BLOCK")
    explicit_to = _int_env("PHANTOMX_INVENTORY_TO_BLOCK", latest)
    event_name = os.getenv("GITHUB_EVENT_NAME", "").strip()

    if explicit_from is not None:
        mode = "explicit-backfill"
    elif event_name == "schedule":
        slice_blocks = _int_env("PHANTOMX_INVENTORY_SCHEDULE_SLICE_BLOCKS", 100_000) or 100_000
        if slice_blocks < 1:
            raise ValueError("PHANTOMX_INVENTORY_SCHEDULE_SLICE_BLOCKS must be positive")
        run_number = _int_env("GITHUB_RUN_NUMBER", 1) or 1
        slot = max(0, run_number - 1)
        scheduled_from = slot * slice_blocks
        if scheduled_from <= latest:
            explicit_from = scheduled_from
            explicit_to = min(latest, scheduled_from + slice_blocks - 1)
            mode = "scheduled-historical-backfill"
        else:
            explicit_from = max(0, latest - slice_blocks + 1)
            explicit_to = latest
            mode = "scheduled-head-refresh"
    else:
        window = _int_env("PHANTOMX_INVENTORY_WINDOW_BLOCKS", 5000)
        if window is None or window < 1:
            raise ValueError("PHANTOMX_INVENTORY_WINDOW_BLOCKS must be positive")
        explicit_from = max(0, explicit_to - window + 1)
        mode = "rolling-window"

    if explicit_to < explicit_from or explicit_to > latest:
        raise ValueError("invalid inventory block range")
    return explicit_from, explicit_to, mode

def main() -> int:
    started = time.time()
    Path("artifacts").mkdir(exist_ok=True)
    spec = _spec()
    rpc_pool = build_free_polygon_rpc_pool()
    from_block, to_block, mode = _resolve_range(rpc_pool)
    chunk_size = _int_env("PHANTOMX_INVENTORY_CHUNK_SIZE", 2000) or 2000
    task = InventoryTask(spec.venue_id, from_block, to_block, chunk_size)
    print(f"INVENTORY venue={spec.venue_id} mode={mode} range={from_block}-{to_block} providers={len(rpc_pool.records)}", flush=True)
    result = run_inventory_task(rpc_pool, spec, task)
    edges = [asdict(edge) for edge in result.edges]
    tokens = sorted({t.lower() for edge in result.edges for t in (edge.token_in, edge.token_out)})
    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX POLYGON VENUE INVENTORY READ-ONLY",
        "venue": spec.venue_id,
        "factory_or_manager": spec.factory_or_manager,
        "event_signature": spec.event_signature,
        "event_topic0": spec.topic0,
        "coverage_mode": mode,
        "from_block": from_block,
        "to_block": to_block,
        "chunk_size": chunk_size,
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time() - started, 3),
        "log_count": len(result.logs),
        "edge_count": len(result.edges),
        "token_count": len(tokens),
        "tokens": tokens,
        "edges": edges,
        "status": result.status,
        "error": result.error,
        "evidence_hash": result.evidence_hash,
        "rpc_pool": {
            "mode": "task_preserving_failover",
            "provider_count": len(rpc_pool.records),
            "failover_events": [asdict(x) for x in rpc_pool.failure_history()],
            "provider_stats": list(rpc_pool.provider_stats()),
        },
        "provenance": {
            "git_commit_sha": os.getenv("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.getenv("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "notes": [
            "ONCHAIN_UNAVAILABLE is limited to the requested block range.",
            "RPC_EXHAUSTED is infrastructure exhaustion and must be requeued.",
            "Rolling-window coverage is incremental, not historical-universe completion.",
        ],
    }
    out = Path("artifacts") / f"polygon_inventory_{spec.venue_id}_{from_block}_{to_block}.json"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out} status={result.status} edges={len(result.edges)}", flush=True)
    return 0 if result.status in {"QUOTED", "ONCHAIN_UNAVAILABLE"} else 1

if __name__ == "__main__":
    raise SystemExit(main())