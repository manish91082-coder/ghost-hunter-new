"""Coordinator for provenance-backed Polygon venue inventory tasks.

Each task is one venue + one explicit block range. It uses the shared RPC
failover pool and chunked eth_getLogs reader, then decodes only the venue's
declared event schema into deterministic PoolEdge records.

The coordinator never equates infrastructure exhaustion with market absence.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .market_graph import PoolEdge
from .polygon_log_inventory import InventoryLog, PolygonLogInventory, PolygonLogInventoryError
from .polygon_venue_inventory import VenueInventoryError, VenueInventorySpec, decode_inventory_log


@dataclass(frozen=True)
class InventoryTask:
    venue_id: str
    from_block: int
    to_block: int
    chunk_size: int = 2000

    def __post_init__(self) -> None:
        if not self.venue_id.strip():
            raise ValueError("venue_id is required")
        if self.from_block < 0 or self.to_block < self.from_block:
            raise ValueError("invalid inventory block range")
        if self.chunk_size < 1:
            raise ValueError("chunk_size must be positive")


@dataclass(frozen=True)
class InventoryTaskResult:
    task: InventoryTask
    logs: tuple[InventoryLog, ...]
    edges: tuple[PoolEdge, ...]
    status: str
    error: str | None
    evidence_hash: str


def _hash_evidence(task: InventoryTask, logs: tuple[InventoryLog, ...], edges: tuple[PoolEdge, ...], status: str) -> str:
    payload = "
".join(
        [
            task.venue_id,
            str(task.from_block),
            str(task.to_block),
            str(task.chunk_size),
            status,
            *(f"log:{log.block_number}:{log.transaction_hash}:{log.log_index}:{log.address}:{','.join(log.topics)}:{log.data}" for log in logs),
            *(f"edge:{edge.edge_id}:{edge.venue}:{edge.pool_id}:{edge.token_in.lower()}:{edge.token_out.lower()}:{edge.parameters}" for edge in edges),
        ]
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def run_inventory_task(rpc: Any, spec: VenueInventorySpec, task: InventoryTask) -> InventoryTaskResult:
    if task.venue_id != spec.venue_id:
        raise ValueError("task/spec venue mismatch")
    reader = PolygonLogInventory(rpc, initial_chunk_size=task.chunk_size)
    try:
        logs = reader.scan(
            from_block=task.from_block,
            to_block=task.to_block,
            address=spec.factory_or_manager,
            topics=(spec.topic0,),
        )
        edges = tuple(
            sorted(
                (decode_inventory_log(log, spec) for log in logs),
                key=lambda edge: edge.identity,
            )
        )
        status = "QUOTED" if edges else "ONCHAIN_UNAVAILABLE"
        return InventoryTaskResult(
            task=task,
            logs=logs,
            edges=edges,
            status=status,
            error=None,
            evidence_hash=_hash_evidence(task, logs, edges, status),
        )
    except (PolygonLogInventoryError, VenueInventoryError) as exc:
        status = "RPC_EXHAUSTED" if "exhausted" in str(exc).lower() else "ADAPTER_UNAVAILABLE"
        return InventoryTaskResult(
            task=task,
            logs=tuple(),
            edges=tuple(),
            status=status,
            error=f"{type(exc).__name__}: {exc}",
            evidence_hash=_hash_evidence(task, tuple(), tuple(), status),
        )