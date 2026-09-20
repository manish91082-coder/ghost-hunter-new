"""Machine-readable Polygon arbitrage-universe coverage manifest.

The manifest is an evidence ledger, not a profitability model. It explicitly
separates observed coverage from incomplete infrastructure/adapter coverage.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

TERMINAL_STATUSES = frozenset({"QUOTED", "ONCHAIN_UNAVAILABLE"})
BLOCKING_STATUSES = frozenset({"RPC_EXHAUSTED", "ADAPTER_UNAVAILABLE", "PENDING", "IN_FLIGHT"})


@dataclass(frozen=True)
class VenueSlice:
    venue: str
    from_block: int
    to_block: int
    status: str
    edge_count: int
    rpc_failure_count: int
    evidence_hash: str

    def __post_init__(self) -> None:
        if self.from_block < 0 or self.to_block < self.from_block:
            raise ValueError("invalid venue block range")
        if not self.venue.strip() or not self.evidence_hash.strip():
            raise ValueError("venue and evidence_hash are required")
        if self.edge_count < 0 or self.rpc_failure_count < 0:
            raise ValueError("counts must be non-negative")


@dataclass
class UniverseManifest:
    chain_id: int
    venue_slices: list[VenueSlice] = field(default_factory=list)
    pairs: set[tuple[str, str]] = field(default_factory=set)
    strategy_task_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_slice(self, item: VenueSlice) -> None:
        self.venue_slices.append(item)

    def add_pair(self, token_a: str, token_b: str) -> None:
        a, b = token_a.lower(), token_b.lower()
        if not a or not b or a == b:
            raise ValueError("pair tokens must be distinct non-empty strings")
        self.pairs.add(tuple(sorted((a, b))))

    def add_strategy_task(self, task_id: str) -> None:
        if not task_id.strip():
            raise ValueError("task_id is required")
        self.strategy_task_ids.add(task_id)

    @property
    def blocking_slices(self) -> tuple[VenueSlice, ...]:
        return tuple(
            sorted((item for item in self.venue_slices if item.status not in TERMINAL_STATUSES),
                   key=lambda item: (item.venue, item.from_block, item.to_block))
        )

    @property
    def exhausted(self) -> bool:
        return bool(self.venue_slices) and not self.blocking_slices

    def summary(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "venue_slice_count": len(self.venue_slices),
            "pair_count": len(self.pairs),
            "strategy_task_count": len(self.strategy_task_ids),
            "blocking_slice_count": len(self.blocking_slices),
            "status": "EXHAUSTED" if self.exhausted else "INCOMPLETE",
        }

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": 1,
            "chain_id": self.chain_id,
            "venue_slices": [
                {
                    "venue": item.venue,
                    "from_block": item.from_block,
                    "to_block": item.to_block,
                    "status": item.status,
                    "edge_count": item.edge_count,
                    "rpc_failure_count": item.rpc_failure_count,
                    "evidence_hash": item.evidence_hash,
                }
                for item in sorted(self.venue_slices, key=lambda item: (item.venue, item.from_block, item.to_block))
            ],
            "pairs": [list(pair) for pair in sorted(self.pairs)],
            "strategy_task_ids": sorted(self.strategy_task_ids),
            "metadata": self.metadata,
        }
        payload["summary"] = self.summary()
        payload["manifest_hash"] = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return payload


def load_inventory_artifact(path: str | Path, *, expected_chain_id: int = 137) -> UniverseManifest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if int(raw.get("chain_id_expected", raw.get("chain_id", expected_chain_id))) != expected_chain_id:
        raise ValueError("inventory artifact chain mismatch")

    manifest = UniverseManifest(chain_id=expected_chain_id)
    venue = str(raw.get("venue", raw.get("strategy", "unknown"))).lower()
    status = str(raw.get("status", "PENDING"))
    from_block = int(raw.get("from_block", raw.get("block_range", {}).get("from_block", 0)))
    to_block = int(raw.get("to_block", raw.get("block_range", {}).get("to_block", from_block)))
    edges = raw.get("edges", [])
    failure_events = raw.get("rpc_pool", {}).get("failover_events", [])
    evidence_hash = str(raw.get("evidence_hash", raw.get("manifest_hash", raw.get("artifact_hash", "unknown"))))
    manifest.add_slice(VenueSlice(venue, from_block, to_block, status, len(edges), len(failure_events), evidence_hash or "unknown"))

    for edge in edges:
        if not isinstance(edge, Mapping):
            continue
        manifest.add_pair(str(edge.get("token_in", "")), str(edge.get("token_out", "")))
    return manifest


def merge_manifests(manifests: Iterable[UniverseManifest]) -> UniverseManifest:
    merged: UniverseManifest | None = None
    for manifest in manifests:
        if merged is None:
            merged = UniverseManifest(chain_id=manifest.chain_id)
        elif merged.chain_id != manifest.chain_id:
            raise ValueError("cannot merge manifests from different chains")
        merged.venue_slices.extend(manifest.venue_slices)
        merged.pairs.update(manifest.pairs)
        merged.strategy_task_ids.update(manifest.strategy_task_ids)
        merged.metadata.update(manifest.metadata)
    return merged or UniverseManifest(chain_id=137)


def validate_expected_venues(manifest: UniverseManifest, expected_venues: Iterable[str]) -> tuple[str, ...]:
    covered = {item.venue for item in manifest.venue_slices}
    missing = sorted(set(expected_venues) - covered)
    return tuple(missing)
