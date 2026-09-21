"""Read-only QuickSwap V3 <-> Ramses V3 route composition.

Both V3 legs are quoted at one immutable Polygon block. QuickSwap V3 uses
Algebra poolByPair and returns a quote-time dynamic fee; Ramses V3 resolves
by tickSpacing and reads the pool's current fee.
"""
from __future__ import annotations

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quickswap_v3 import QuickSwapV3ExactQuoter
from .ramses_v3 import RamsesV3ExactQuoter
from .route_simulator import RouteSimulation, simulate_two_leg

POLYGON_CHAIN_ID = 137
QUICKSWAP_V3_TO_RAMSES_V3_PATH = "quickswap_v3->ramses_v3"
RAMSES_V3_TO_QUICKSWAP_V3_PATH = "ramses_v3->quickswap_v3"


def _context(rpc, block: MarketBlockSnapshot | None) -> MarketBlockSnapshot:
    context = block if block is not None else acquire_market_block(rpc)
    if context.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("route requires Polygon mainnet")
    return context


def build_quickswap_v3_to_ramses_v3_route(
    rpc,
    quickswap_v3: QuickSwapV3ExactQuoter,
    ramses_v3: RamsesV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    ramses_tick_spacing: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = quickswap_v3.quote_snapshot(amount_in, token_a, token_b, context)
    second = ramses_v3.quote_snapshot(first.amount_out, token_b, token_a, ramses_tick_spacing, context)
    return simulate_two_leg(first, second)


def build_ramses_v3_to_quickswap_v3_route(
    rpc,
    quickswap_v3: QuickSwapV3ExactQuoter,
    ramses_v3: RamsesV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    ramses_tick_spacing: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = ramses_v3.quote_snapshot(amount_in, token_a, token_b, ramses_tick_spacing, context)
    second = quickswap_v3.quote_snapshot(first.amount_out, token_b, token_a, context)
    return simulate_two_leg(first, second)


__all__ = [
    "POLYGON_CHAIN_ID",
    "QUICKSWAP_V3_TO_RAMSES_V3_PATH",
    "RAMSES_V3_TO_QUICKSWAP_V3_PATH",
    "build_quickswap_v3_to_ramses_v3_route",
    "build_ramses_v3_to_quickswap_v3_route",
]
