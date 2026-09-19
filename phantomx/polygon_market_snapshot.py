"""Convert Polygon inventory results into a deterministic market snapshot.

This layer is intentionally network-free. It consumes already decoded PoolEdge
records, adds executable directions for AMM pools, generates bounded cycles,
and returns stable identifiers for adaptive scheduling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .hunt_scheduler import HuntTask, stable_task_id
from .market_graph import MarketCycle, PolygonMarketGraph, PoolEdge
from .polygon_universe_inventory import InventoryTaskResult


@dataclass(frozen=True)
class MarketSnapshot:
    edges: tuple[PoolEdge, ...]
    tokens: tuple[str, ...]
    cycles_2_leg: tuple[MarketCycle, ...]
    cycles_3_leg: tuple[MarketCycle, ...]
    cycles_4_leg: tuple[MarketCycle, ...]

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def token_count(self) -> int:
        return len(self.tokens)


def build_snapshot(results: Iterable[InventoryTaskResult], *, base_token: str) -> MarketSnapshot:
    graph = PolygonMarketGraph()
    all_edges: dict[str, PoolEdge] = {}
    for result in results:
        if result.status not in {"QUOTED", "ONCHAIN_UNAVAILABLE"}:
            continue
        for edge in result.edges:
            graph.add_bidirectional_pool(edge)
            forward_id = f"{edge.edge_id}:forward".lower()
            reverse_id = f"{edge.edge_id}:reverse".lower()
            all_edges[forward_id] = PoolEdge(
                f"{edge.edge_id}:forward",
                edge.venue,
                edge.pool_id,
                edge.token_in.lower(),
                edge.token_out.lower(),
                edge.parameters,
            )
            all_edges[reverse_id] = PoolEdge(
                f"{edge.edge_id}:reverse",
                edge.venue,
                edge.pool_id,
                edge.token_out.lower(),
                edge.token_in.lower(),
                edge.parameters,
            )
    return MarketSnapshot(
        edges=tuple(sorted(all_edges.values(), key=lambda edge: edge.identity)),
        tokens=graph.token_universe(),
        cycles_2_leg=graph.cycles_from(base_token, max_legs=2),
        cycles_3_leg=graph.cycles_from(base_token, max_legs=3),
        cycles_4_leg=graph.cycles_from(base_token, max_legs=4),
    )


def cycle_tasks(snapshot: MarketSnapshot, *, base_token: str, last_scanned_block: int) -> tuple[HuntTask, ...]:
    tasks: list[HuntTask] = []
    state_hash = "|".join(edge.edge_id for edge in snapshot.edges)
    for cycle in (*snapshot.cycles_2_leg, *snapshot.cycles_3_leg, *snapshot.cycles_4_leg):
        task_id = stable_task_id(cycle.route_id, state_hash or "empty")
        tasks.append(
            HuntTask(
                task_id=task_id,
                route_id=cycle.route_id,
                last_scanned_block=last_scanned_block,
                newly_discovered=True,
                age_blocks=0,
            )
        )
    unique = {task.task_id: task for task in tasks}
    return tuple(sorted(unique.values(), key=lambda task: task.task_id))
