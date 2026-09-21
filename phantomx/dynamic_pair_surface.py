"""Live Polygon pair-surface discovery for route scanners.

Combines deterministic seed pairs with recent on-chain pool-creation evidence.
The seed set preserves continuity; discovered pairs expand coverage. Discovery
status is explicit so a scanner never mistakes an infrastructure miss for
universe completeness.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .curve import CurveRegistryExactQuoter
from .market_block import acquire_market_block, acquire_market_block_at
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
    chunk_size: int = 50,
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

    inventory_venues = tuple(venue for venue in required if venue != "curve")
    results: list[InventoryTaskResult] = []
    for venue_id in inventory_venues:
        spec = specs[venue_id]
        results.append(
            __import__("phantomx.polygon_universe_inventory", fromlist=["run_inventory_task"]).run_inventory_task(
                rpc,
                spec,
                InventoryTask(venue_id, from_block, latest, chunk_size),
            )
        )

    universe = build_pair_universe(results)
    discovered = base_pairs(
        universe,
        base_token=base_token,
        required_venues=inventory_venues,
    )
    pair_map: dict[str, DynamicPairSpec] = {}

    if "curve" not in required:
        for name, token in seed_pairs:
            pair_map[token.lower()] = DynamicPairSpec(name, token, "SEED", tuple())

    curve_lookup_complete = True
    if "curve" in required:
        curve = CurveRegistryExactQuoter(rpc)
        market_block = acquire_market_block_at(rpc, latest)
        candidate_tokens = {record.token1 if record.token0 == base_token.lower() else record.token0 for record in discovered}
        candidate_tokens.update(token for _name, token in seed_pairs)
        for token in sorted(candidate_tokens):
            try:
                refs = curve.find_pools_for_pair(
                    base_token,
                    token,
                    market_block,
                    max_pools_per_registry=4,
                )
            except Exception as exc:
                curve_lookup_complete = False
                raise RuntimeError(
                    f"Curve pair-surface lookup failed for {base_token}/{token}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            if refs:
                name = next(
                    (seed_name for seed_name, seed_token in seed_pairs if seed_token.lower() == token.lower()),
                    f"{base_token}/{token}",
                )
                pair_map[token.lower()] = DynamicPairSpec(
                    name,
                    token,
                    "LIVE_CURVE_REGISTRY",
                    tuple(sorted({"curve", *next((record.venues for record in discovered if (record.token0 == base_token.lower() and record.token1 == token.lower()) or (record.token1 == base_token.lower() and record.token0 == token.lower())), tuple())})),
                )

    for record in discovered:
        token = record.token1 if record.token0 == base_token.lower() else record.token0
        if "curve" not in required:
            pair_map[token.lower()] = DynamicPairSpec(
                f"{base_token}/{token}",
                token,
                "LIVE_INVENTORY",
                record.venues,
            )
        elif token.lower() in {item.lower() for item in candidate_tokens}:
            if token.lower() not in pair_map:
                continue

    status = (
        "COMPLETE_RECENT_WINDOW"
        if all(r.status in {"QUOTED", "ONCHAIN_UNAVAILABLE"} for r in results)
        and curve_lookup_complete
        else "PAIR_UNIVERSE_INCOMPLETE"
    )
    return DynamicPairDiscovery(
        pairs=tuple(sorted(pair_map.values(), key=lambda item: item.name.lower())),
        status=status,
        from_block=from_block,
        to_block=latest,
        inventory_results=tuple(results),
    )