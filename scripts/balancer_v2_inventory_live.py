#!/usr/bin/env python3
"""Read-only Balancer V2 Polygon inventory runner."""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.balancer_v2 import BALANCER_V2_VAULT, POOL_REGISTERED_TOPIC, BalancerInventoryError, BalancerV2Inventory
from phantomx.market_block import acquire_market_block, acquire_market_block_at
from phantomx.polygon_log_inventory import PolygonLogInventory, PolygonLogInventoryError
from phantomx.rpc_failover import build_free_polygon_rpc_pool

SLICE_BLOCKS = 100_000

def _int_env(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value

def _resolve_range(context_block: int) -> tuple[int, int, str]:
    start = _int_env("PHANTOMX_INVENTORY_FROM_BLOCK")
    end = _int_env("PHANTOMX_INVENTORY_TO_BLOCK", context_block)
    event = os.getenv("GITHUB_EVENT_NAME", "")
    if start is not None:
        mode = "explicit-backfill"
    elif event == "schedule":
        run_number = _int_env("GITHUB_RUN_NUMBER", 1) or 1
        slot = max(0, run_number - 1)
        start = slot * SLICE_BLOCKS
        if start <= context_block:
            end = min(context_block, start + SLICE_BLOCKS - 1)
            mode = "scheduled-historical-backfill"
        else:
            start = max(0, context_block - SLICE_BLOCKS + 1)
            end = context_block
            mode = "scheduled-head-refresh"
    else:
        window = _int_env("PHANTOMX_INVENTORY_WINDOW_BLOCKS", 5_000) or 5_000
        start = max(0, end - window + 1)
        mode = "rolling-window"
    if end < start or end > context_block:
        raise ValueError("invalid Balancer inventory range")
    return start, end, mode

def main() -> int:
    started = time.time()
    Path("artifacts").mkdir(exist_ok=True)
    pool = build_free_polygon_rpc_pool()
    context = acquire_market_block(pool)
    from_block, to_block, mode = _resolve_range(context.block_number)
    pinned_block = _int_env("PHANTOMX_INVENTORY_PINNED_BLOCK")
    if pinned_block is not None:
        if pinned_block > to_block:
            raise ValueError("pinned inventory block cannot exceed inventory end block")
        context = acquire_market_block_at(pool, pinned_block)
    chunk_size = _int_env("PHANTOMX_INVENTORY_CHUNK_SIZE", 2_000) or 2_000
    reader = PolygonLogInventory(pool, initial_chunk_size=chunk_size)
    inventory = BalancerV2Inventory(pool)
    pools = []
    edges = {}
    pool_errors = []
    status = "ONCHAIN_UNAVAILABLE"
    try:
        logs = reader.scan(from_block=from_block, to_block=to_block, address=BALANCER_V2_VAULT, topics=(POOL_REGISTERED_TOPIC,))
    except PolygonLogInventoryError as exc:
        logs = ()
        status = "RPC_EXHAUSTED"
        pool_errors.append({"stage": "logs", "error": f"{type(exc).__name__}: {exc}"})
    for log in logs:
        try:
            pool_id, pool_address, specialization = inventory.decode_pool_registered({"address": log.address, "topics": log.topics, "data": log.data})
            loaded = inventory.load_pool(pool_id, pool_address, specialization, context)
            pools.append(asdict(loaded))
            for edge in inventory.graph_edges(loaded):
                edges[edge.edge_id.lower()] = asdict(edge)
        except (BalancerInventoryError, ValueError) as exc:
            pool_errors.append({"log_identity": log.identity, "error": f"{type(exc).__name__}: {exc}"})
    if edges:
        status = "QUOTED" if not pool_errors else "QUOTED_PARTIAL"
    elif status != "RPC_EXHAUSTED":
        status = "ADAPTER_UNAVAILABLE" if pool_errors else "ONCHAIN_UNAVAILABLE"
    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX BALANCER V2 POLYGON INVENTORY READ-ONLY",
        "venue": "balancer_v2",
        "vault": BALANCER_V2_VAULT,
        "event_signature": "PoolRegistered(bytes32,address,uint8)",
        "event_topic0": POOL_REGISTERED_TOPIC,
        "coverage_mode": mode,
        "from_block": from_block,
        "to_block": to_block,
        "pinned_block": context.block_number,
        "pinned_timestamp": context.timestamp,
        "chunk_size": chunk_size,
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time() - started, 3),
        "log_count": len(logs),
        "pool_count": len(pools),
        "edge_count": len(edges),
        "pools": pools,
        "edges": list(edges.values()),
        "pool_errors": pool_errors,
        "status": status,
        "provenance": {
            "git_commit_sha": os.getenv("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.getenv("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "rpc_pool": {
            "mode": "task_preserving_failover",
            "provider_count": len(pool.records),
            "failover_events": [asdict(x) for x in pool.failure_history()],
            "provider_stats": list(pool.provider_stats()),
        },
        "notes": [
            "RPC_EXHAUSTED means infrastructure coverage is incomplete and the task must be retried.",
            "QUOTED_PARTIAL means at least one pool was inventoried but one or more pool reads failed.",
            "No swap quote, execution authorization, signing, submission, or broadcast is performed.",
        ],
    }
    out = Path("artifacts") / f"balancer_v2_inventory_{from_block}_{to_block}.json"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    print(f"BALANCER_INVENTORY mode={mode} range={from_block}-{to_block} status={status} pools={len(pools)} edges={len(edges)} rpc_failures={len(pool.failure_history())}", flush=True)
    print(f"Wrote {out}", flush=True)
    return 0 if status in {"QUOTED", "QUOTED_PARTIAL", "ONCHAIN_UNAVAILABLE"} else 1

if __name__ == "__main__":
    raise SystemExit(main())