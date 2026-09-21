"""Deterministic pair-universe index derived from Polygon pool inventory."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .market_graph import PoolEdge
from .polygon_universe_inventory import InventoryTaskResult


@dataclass(frozen=True)
class PairUniverseRecord:
    token0: str
    token1: str
    venues: tuple[str, ...]
    pool_count: int

    @property
    def key(self) -> tuple[str, str]:
        return self.token0, self.token1


def _pair_key(token_a: str, token_b: str) -> tuple[str, str]:
    a, b = token_a.lower(), token_b.lower()
    if a == b:
        raise ValueError("pair tokens must differ")
    return (a, b) if a < b else (b, a)


def build_pair_universe(results: Iterable[InventoryTaskResult]) -> tuple[PairUniverseRecord, ...]:
    pairs: dict[tuple[str, str], dict[str, object]] = {}
    for result in results:
        if result.status != "QUOTED":
            continue
        for edge in result.edges:
            key = _pair_key(edge.token_in, edge.token_out)
            bucket = pairs.setdefault(key, {"venues": set(), "pools": set()})
            bucket["venues"].add(edge.venue)
            bucket["pools"].add((edge.venue, edge.pool_id, edge.parameters))
    return tuple(
        PairUniverseRecord(
            token0=key[0],
            token1=key[1],
            venues=tuple(sorted(bucket["venues"])),
            pool_count=len(bucket["pools"]),
        )
        for key, bucket in sorted(pairs.items())
    )


def base_pairs(
    universe: Iterable[PairUniverseRecord],
    *,
    base_token: str,
    required_venues: Iterable[str] = (),
) -> tuple[PairUniverseRecord, ...]:
    base = base_token.lower()
    required = frozenset(required_venues)
    result = [
        record
        for record in universe
        if base in record.key and required.issubset(record.venues)
    ]
    return tuple(sorted(result, key=lambda record: record.key))
