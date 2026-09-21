"""Deterministic directed Polygon market graph and bounded cycle generator.

This module is network-free. It models every executable pool/configuration as
an independent directed edge, so multiple pools or fee configurations for the
same token pair are preserved instead of collapsed into one pair.

The graph generator is discovery infrastructure only. Economic and execution
gates remain outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Iterable


class MarketGraphError(ValueError):
    """Raised when graph input violates deterministic invariants."""


@dataclass(frozen=True)
class PoolEdge:
    edge_id: str
    venue: str
    pool_id: str
    token_in: str
    token_out: str
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("edge_id", self.edge_id),
            ("venue", self.venue),
            ("pool_id", self.pool_id),
            ("token_in", self.token_in),
            ("token_out", self.token_out),
        ):
            if not isinstance(value, str) or not value.strip():
                raise MarketGraphError(f"{name} is required")
        if self.token_in.lower() == self.token_out.lower():
            raise MarketGraphError("self-loop edges are not allowed")

    @property
    def identity(self) -> tuple[str, ...]:
        return (
            self.edge_id,
            self.venue,
            self.pool_id,
            self.token_in.lower(),
            self.token_out.lower(),
            *self.parameters,
        )


@dataclass(frozen=True)
class MarketCycle:
    base_token: str
    edges: tuple[PoolEdge, ...]
    token_path: tuple[str, ...]
    route_id: str

    def __post_init__(self) -> None:
        if len(self.edges) < 2:
            raise MarketGraphError("cycle requires at least two edges")
        if len(self.token_path) != len(self.edges) + 1:
            raise MarketGraphError("token_path length must equal edge count + 1")
        if self.token_path[0].lower() != self.base_token.lower():
            raise MarketGraphError("cycle must start from base token")
        if self.token_path[-1].lower() != self.base_token.lower():
            raise MarketGraphError("cycle must return to base token")


@dataclass
class PolygonMarketGraph:
    _outgoing: dict[str, list[PoolEdge]] = field(default_factory=dict)
    _edge_ids: set[str] = field(default_factory=set)

    def add_edge(self, edge: PoolEdge) -> None:
        key = edge.edge_id.lower()
        if key in self._edge_ids:
            raise MarketGraphError("duplicate edge_id")
        self._edge_ids.add(key)
        self._outgoing.setdefault(edge.token_in.lower(), []).append(edge)

    def add_bidirectional_pool(self, edge: PoolEdge) -> None:
        """Add both executable directions for a two-token AMM pool."""
        forward = PoolEdge(
            edge_id=f"{edge.edge_id}:forward",
            venue=edge.venue,
            pool_id=edge.pool_id,
            token_in=edge.token_in.lower(),
            token_out=edge.token_out.lower(),
            parameters=edge.parameters,
        )
        reverse = PoolEdge(
            edge_id=f"{edge.edge_id}:reverse",
            venue=edge.venue,
            pool_id=edge.pool_id,
            token_in=edge.token_out.lower(),
            token_out=edge.token_in.lower(),
            parameters=edge.parameters,
        )
        self.add_edge(forward)
        self.add_edge(reverse)
    def add_edges(self, edges: Iterable[PoolEdge]) -> None:
        for edge in edges:
            self.add_edge(edge)

    def outgoing(self, token: str) -> tuple[PoolEdge, ...]:
        return tuple(
            sorted(
                self._outgoing.get(token.lower(), ()),
                key=lambda edge: edge.identity,
            )
        )

    def token_universe(self) -> tuple[str, ...]:
        tokens: set[str] = set()
        for edges in self._outgoing.values():
            for edge in edges:
                tokens.add(edge.token_in.lower())
                tokens.add(edge.token_out.lower())
        return tuple(sorted(tokens))

    def edge_count(self) -> int:
        return len(self._edge_ids)

    def cycles_from(self, base_token: str, *, max_legs: int = 4, min_legs: int = 2) -> tuple[MarketCycle, ...]:
        if not isinstance(max_legs, int) or isinstance(max_legs, bool) or max_legs < 2:
            raise MarketGraphError("max_legs must be an integer >= 2")
        if not isinstance(min_legs, int) or isinstance(min_legs, bool) or min_legs < 2 or min_legs > max_legs:
            raise MarketGraphError("min_legs must be an integer >= 2 and <= max_legs")
        base = base_token.lower()
        if not base:
            raise MarketGraphError("base_token is required")

        cycles: list[MarketCycle] = []

        def dfs(
            current: str,
            path_edges: tuple[PoolEdge, ...],
            visited_tokens: frozenset[str],
        ) -> None:
            legs = len(path_edges)
            if legs >= max_legs:
                return
            for edge in self.outgoing(current):
                nxt = edge.token_out.lower()
                next_legs = path_edges + (edge,)
                if nxt == base:
                    if len(next_legs) >= min_legs:
                        token_path = (base, *[e.token_out.lower() for e in next_legs])
                        route_id = self._route_id(base, next_legs)
                        cycles.append(
                            MarketCycle(
                                base_token=base,
                                edges=next_legs,
                                token_path=token_path,
                                route_id=route_id,
                            )
                        )
                    continue
                if nxt in visited_tokens:
                    continue
                dfs(nxt, next_legs, visited_tokens | {nxt})

        dfs(base, tuple(), frozenset({base}))
        unique = {cycle.route_id: cycle for cycle in cycles}
        return tuple(sorted(unique.values(), key=lambda cycle: cycle.route_id))

    @staticmethod
    def _route_id(base: str, edges: tuple[PoolEdge, ...]) -> str:
        payload = "|".join(
            (
                base.lower(),
                *(f"{edge.edge_id.lower()}:{edge.venue}:{edge.pool_id}:{edge.token_in.lower()}>{edge.token_out.lower()}:{edge.parameters}" for edge in edges),
            )
        ).encode("utf-8")
        return "route:" + sha256(payload).hexdigest()