"""Exact Ramses V3 <-> Uniswap V3 route composition.

Discovery-only. Both legs share one immutable Polygon block. Ramses V3 pool
selection is by tickSpacing; the actual pool fee is read from the resolved
pool and stored in quote evidence.
"""
from __future__ import annotations

from .market_block import MarketBlockSnapshot, acquire_market_block
from .ramses_v3 import DEFAULT_TICK_SPACINGS, RamsesV3ExactQuoter
from .route_simulator import RouteSimulation, simulate_two_leg
from .uniswap_v3 import UniswapV3ExactQuoter

POLYGON_CHAIN_ID = 137
RAMSES_V3_TO_UNISWAP_V3_PATH = "ramses_v3->uniswap_v3"
UNISWAP_V3_TO_RAMSES_V3_PATH = "uniswap_v3->ramses_v3"


def _context(rpc, block: MarketBlockSnapshot | None) -> MarketBlockSnapshot:
    context = block if block is not None else acquire_market_block(rpc)
    if context.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("route requires Polygon mainnet")
    return context


def build_ramses_v3_to_uniswap_v3_route(
    rpc,
    ramses_v3: RamsesV3ExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    ramses_tick_spacing: int,
    uniswap_fee: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = ramses_v3.quote_snapshot(
        amount_in, token_a, token_b, ramses_tick_spacing, context
    )
    second = uniswap_v3.quote_snapshot(
        first.amount_out, token_b, token_a, uniswap_fee, context
    )
    return simulate_two_leg(first, second)


def build_uniswap_v3_to_ramses_v3_route(
    rpc,
    ramses_v3: RamsesV3ExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    ramses_tick_spacing: int,
    uniswap_fee: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = uniswap_v3.quote_snapshot(
        amount_in, token_a, token_b, uniswap_fee, context
    )
    second = ramses_v3.quote_snapshot(
        first.amount_out, token_b, token_a, ramses_tick_spacing, context
    )
    return simulate_two_leg(first, second)


__all__ = [
    "DEFAULT_TICK_SPACINGS",
    "POLYGON_CHAIN_ID",
    "RAMSES_V3_TO_UNISWAP_V3_PATH",
    "UNISWAP_V3_TO_Ramses_V3_PATH",
    "build_ramses_v3_to_uniswap_v3_route",
    "build_uniswap_v3_to_ramses_v3_route",
]
