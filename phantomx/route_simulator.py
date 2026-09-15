"""Independent exact two-leg route simulation primitives.

This module is execution-agnostic. It consumes canonical quote evidence only,
requires the second leg's input to equal the first leg's exact output, and
never substitutes forecasts, spot prices, or percentage spreads for settlement
truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .quote_snapshot import QuoteSnapshot, QuoteSnapshotError


class RouteSimulationError(ValueError):
    """Raised when a route cannot be proven internally consistent."""


@dataclass(frozen=True)
class RouteSimulation:
    schema_version: int
    chain_id: int
    block_number: int
    initial_amount: int
    final_amount: int
    legs: tuple[QuoteSnapshot, ...]
    route_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise RouteSimulationError("unsupported route simulation schema")
        if self.chain_id <= 0 or self.block_number < 0:
            raise RouteSimulationError("invalid route chain/block")
        if len(self.legs) != 2:
            raise RouteSimulationError("production route must contain exactly two legs")
        if self.initial_amount <= 0 or self.final_amount <= 0:
            raise RouteSimulationError("route amounts must be positive")
        if self.legs[0].chain_id != self.chain_id or self.legs[1].chain_id != self.chain_id:
            raise RouteSimulationError("leg chain identity mismatch")
        if self.legs[0].block_number != self.block_number or self.legs[1].block_number != self.block_number:
            raise RouteSimulationError("all legs must share one pinned block")
        if self.legs[0].amount_in != self.initial_amount:
            raise RouteSimulationError("initial amount does not match first leg")
        if self.legs[1].amount_in != self.legs[0].amount_out:
            raise RouteSimulationError("second-leg input is not first-leg exact output")
        if self.final_amount != self.legs[1].amount_out:
            raise RouteSimulationError("final amount does not match second leg")
        if self.legs[0].token_out.lower() != self.legs[1].token_in.lower():
            raise RouteSimulationError("route token continuity is broken")
        if self.legs[0].token_in.lower() != self.legs[1].token_out.lower():
            raise RouteSimulationError("route is not A→B→A")
        if not self.route_hash.startswith("0x") or len(self.route_hash) != 66:
            raise RouteSimulationError("route_hash must be a 32-byte digest")
        if self.route_hash != compute_route_hash(self.legs):
            raise RouteSimulationError("route_hash does not match route evidence")


def compute_route_hash(legs: Sequence[QuoteSnapshot]) -> str:
    """Hash ordered quote hashes, preserving route direction and leg order."""
    if len(legs) != 2:
        raise RouteSimulationError("production route must contain exactly two legs")
    try:
        from .hashing import keccak256_hex
        payload = b"".join(bytes.fromhex(leg.quote_hash[2:]) for leg in legs)
    except (ValueError, AttributeError) as exc:
        raise RouteSimulationError("invalid quote hash in route") from exc
    return keccak256_hex(payload)


def simulate_two_leg(leg_one: QuoteSnapshot, leg_two: QuoteSnapshot) -> RouteSimulation:
    """Build a deterministic A→B→A simulation from two canonical quote snapshots."""
    if leg_one.chain_id != leg_two.chain_id:
        raise RouteSimulationError("route legs must use the same chain")
    if leg_one.block_number != leg_two.block_number:
        raise RouteSimulationError("route legs must use the same pinned block")
    if leg_one.token_out.lower() != leg_two.token_in.lower():
        raise RouteSimulationError("route token continuity is broken")
    if leg_one.token_in.lower() != leg_two.token_out.lower():
        raise RouteSimulationError("route must return to the initial asset")
    if leg_two.amount_in != leg_one.amount_out:
        raise RouteSimulationError("second-leg amount_in must equal first-leg amount_out")
    route_hash = compute_route_hash((leg_one, leg_two))
    return RouteSimulation(
        schema_version=1,
        chain_id=leg_one.chain_id,
        block_number=leg_one.block_number,
        initial_amount=leg_one.amount_in,
        final_amount=leg_two.amount_out,
        legs=(leg_one, leg_two),
        route_hash=route_hash,
    )
