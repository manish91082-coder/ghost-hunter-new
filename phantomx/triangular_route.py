"""Discovery-only deterministic multi-leg route simulation.

Unlike the canonical Phase-19 two-leg executor route, triangular routes are
research/discovery objects until a dedicated 3+ leg executor is independently
certified. This module validates exact quote continuity and one pinned block.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .hashing import keccak256_hex
from .quote_snapshot import QuoteSnapshot


class TriangularRouteSimulationError(ValueError):
    """Raised when a multi-leg discovery route cannot be proven consistent."""


@dataclass(frozen=True)
class TriangularRouteSimulation:
    schema_version: int
    chain_id: int
    block_number: int
    initial_amount: int
    final_amount: int
    legs: tuple[QuoteSnapshot, ...]
    route_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise TriangularRouteSimulationError("unsupported triangular route schema")
        if len(self.legs) < 3:
            raise TriangularRouteSimulationError("triangular route requires at least three legs")
        if self.chain_id <= 0 or self.block_number < 0:
            raise TriangularRouteSimulationError("invalid route chain/block")
        if self.initial_amount <= 0 or self.final_amount <= 0:
            raise TriangularRouteSimulationError("route amounts must be positive")
        for leg in self.legs:
            if leg.chain_id != self.chain_id:
                raise TriangularRouteSimulationError("leg chain identity mismatch")
            if leg.block_number != self.block_number:
                raise TriangularRouteSimulationError("all legs must share one pinned block")
        if self.legs[0].amount_in != self.initial_amount:
            raise TriangularRouteSimulationError("initial amount does not match first leg")
        for previous, current in zip(self.legs, self.legs[1:]):
            if previous.token_out.lower() != current.token_in.lower():
                raise TriangularRouteSimulationError("route token continuity is broken")
            if previous.amount_out != current.amount_in:
                raise TriangularRouteSimulationError("leg amount continuity is broken")
        if self.legs[-1].token_out.lower() != self.legs[0].token_in.lower():
            raise TriangularRouteSimulationError("route does not return to the initial asset")
        if self.final_amount != self.legs[-1].amount_out:
            raise TriangularRouteSimulationError("final amount does not match last leg")
        if not self.route_hash.startswith("0x") or len(self.route_hash) != 66:
            raise TriangularRouteSimulationError("route_hash must be a 32-byte digest")
        if self.route_hash != compute_multi_leg_route_hash(self.legs):
            raise TriangularRouteSimulationError("route_hash does not match route evidence")


def compute_multi_leg_route_hash(legs: Sequence[QuoteSnapshot]) -> str:
    if len(legs) < 3:
        raise TriangularRouteSimulationError("at least three quote legs are required")
    try:
        payload = b"".join(bytes.fromhex(leg.quote_hash[2:]) for leg in legs)
    except (ValueError, AttributeError) as exc:
        raise TriangularRouteSimulationError("invalid quote hash in route") from exc
    return keccak256_hex(payload)


def simulate_multi_leg(legs: Sequence[QuoteSnapshot]) -> TriangularRouteSimulation:
    normalized = tuple(legs)
    if len(normalized) < 3:
        raise TriangularRouteSimulationError("at least three quote legs are required")
    for previous, current in zip(normalized, normalized[1:]):
        if previous.chain_id != current.chain_id:
            raise TriangularRouteSimulationError("route legs must use the same chain")
        if previous.block_number != current.block_number:
            raise TriangularRouteSimulationError("route legs must use the same pinned block")
        if previous.token_out.lower() != current.token_in.lower():
            raise TriangularRouteSimulationError("route token continuity is broken")
        if previous.amount_out != current.amount_in:
            raise TriangularRouteSimulationError("leg amount_in must equal prior leg amount_out")
    if normalized[-1].token_out.lower() != normalized[0].token_in.lower():
        raise TriangularRouteSimulationError("route must return to the initial asset")
    route_hash = compute_multi_leg_route_hash(normalized)
    return TriangularRouteSimulation(
        schema_version=1,
        chain_id=normalized[0].chain_id,
        block_number=normalized[0].block_number,
        initial_amount=normalized[0].amount_in,
        final_amount=normalized[-1].amount_out,
        legs=normalized,
        route_hash=route_hash,
    )


__all__ = [
    "TriangularRouteSimulation",
    "TriangularRouteSimulationError",
    "compute_multi_leg_route_hash",
    "simulate_multi_leg",
]
