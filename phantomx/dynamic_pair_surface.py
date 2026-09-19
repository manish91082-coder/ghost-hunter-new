"""Live Polygon pair-surface discovery for route scanners.

Combines deterministic seed pairs with recent on-chain pool-creation evidence.
The seed set preserves continuity; discovered pairs expand coverage. Discovery
status is explicit so a scanner never mistakes an infrastructure miss for
universe completeness.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .polygon_pair_universe import PairUniverseRecord, build_pair_universe, base_pairs
from .polygon_universe_inventory import InventoryTask, InventoryTaskResult
from .polygon_venue_inventory import VENUE_SPECS


@dataclass(frozen=True)
class DynamicPairSpec:
    name: str
    token_b: str
    source: str
    venues: tuple[str, ...]


@dataclass(frozen=True)
class DynamicPairDiscovery:
    pairs: tuple[DynamicPairSpec, ...]
    status: str
    from_block: int
    to_block: int
    inventory_results: tuple[InventoryTaskResult, ...]
    error: str | None = None


def discover_live_base_pairs(
    rpc: Any,
    *,
    base_token: str,
    seed_pairs: Sequence[tuple[str, str]],
    required_venues: Iterable[str],
    lookback_blocks: int = 25_000,
    chunk_size: int = 2_000,
) -> DynamicPairDiscovery:
    if lookback_blocks < 1 or chunk_size < 1:
        raise ValueError("lookback_blocks and chunk_size must be positive")
    latest = int(str(rpc.call("eth_blockNumber", [])), 16)
    from_block = max(0, latest - lookback_blocks + 1)
    required = tuple(sorted(set(required_venues)))
    specs = {spec.venue_id: spec for spec in VENUE_SPECS}
    missing = [venue for venue in required if venue not in specs]
    if missing:
        raise ValueError(f"unknown venue ids: {missing}")

    results: list[InventoryTaskResult] = []
    for venue_id in required:
        spec = specs[venue_id]
        results.append(
            __import__("phantomx.polygon_universe_inventory", fromlist=["run_inventory_task"]).run_inventory_task(
                rpc,
                spec,
                InventoryTask(venue_id, from_block, latest, chunk_size),
            )
        )

    universe = build_pair_universe(results)
    discovered = base_pairs(universe, base_token=base_token, required_venues=required)
    seed_by_token = {token.lower(): name for name, token in seed_pairs}
    pair_map: dict[str, DynamicPairSpec] = {}

    for name, token in seed_pairs:
        pair_map[token.lower()] = DynamicPairSpec(name, token, "SEED", tuple())

    for record in discovered:
        token = record.token1 if record.token0 == base_token.lower() else record.token0
        pair_map[token.lower()] = DynamicPairSpec(
            f"{base_token}/{token}",
            token,
            "LIVE_INVENTORY",
            record.venues,
        )

    pairs = tuple(sorted(pair_map.values(), key=lambda item: item.name.lower()))
    status = "COMPLETE_RECENT_WINDOW" if all(r.status in {"QUOTED", "ONCHAIN_UNAVAILABLE"} for r in results) else "PAIR_UNIVERSE_INCOMPLETE"
    return DynamicPairDiscovery(
        pairs=pairs,
        status=status,
        from_block=from_block,
        to_block=latest,
        inventory_results=tuple(results),
    )
