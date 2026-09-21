"""Deterministic strategy-family filters over the Polygon market graph.

This module turns a complete market graph into explicit bounded strategy
surfaces. It never quotes, values, signs, submits, or declares profitability.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .market_graph import MarketCycle


class StrategyFamily(str, Enum):
    DIRECT_CROSS_VENUE = "DIRECT_CROSS_VENUE"
    SAME_VENUE_POOL_DISLOCATION = "SAME_VENUE_POOL_DISLOCATION"
    TRIANGULAR = "TRIANGULAR"
    FOUR_LEG = "FOUR_LEG"
    MIXED_CURVE = "MIXED_CURVE"


@dataclass(frozen=True)
class StrategyCandidate:
    family: StrategyFamily
    cycle: MarketCycle


def _distinct(values: Iterable[str]) -> bool:
    return len(set(values)) == len(tuple(values))


def classify_cycle(cycle: MarketCycle) -> tuple[StrategyFamily, ...]:
    venues = tuple(edge.venue for edge in cycle.edges)
    families: list[StrategyFamily] = []

    if len(cycle.edges) == 2 and len(set(venues)) == 2:
        families.append(StrategyFamily.DIRECT_CROSS_VENUE)

    if len(cycle.edges) == 2 and len({(edge.venue, edge.pool_id) for edge in cycle.edges}) == 2:
        # Same venue is useful only when the two legs touch distinct pool
        # instances, preventing a self-referential duplicate pool cycle.
        if venues[0] == venues[1]:
            families.append(StrategyFamily.SAME_VENUE_POOL_DISLOCATION)

    if len(cycle.edges) == 3 and len(set(venues)) == 3:
        families.append(StrategyFamily.TRIANGULAR)

    if len(cycle.edges) == 4:
        families.append(StrategyFamily.FOUR_LEG)

    if len({edge.venue for edge in cycle.edges}) >= 2:
        families.append(StrategyFamily.MIXED_CURVE)

    return tuple(families)


def generate_candidates(
    cycles: Iterable[MarketCycle],
    family: StrategyFamily,
) -> tuple[StrategyCandidate, ...]:
    result = [
        StrategyCandidate(family, cycle)
        for cycle in cycles
        if family in classify_cycle(cycle)
    ]
    unique = {(candidate.family.value, candidate.cycle.route_id): candidate for candidate in result}
    return tuple(sorted(unique.values(), key=lambda item: (item.family.value, item.cycle.route_id)))
