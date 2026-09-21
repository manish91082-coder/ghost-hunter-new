"""Exact QuickSwap V3 (Algebra) <-> Uniswap V3 route composition.

This is discovery-only. Both legs share one immutable Polygon block.
QuickSwap V3 fee is returned by its Algebra quoter; Uniswap V3 fee is an
explicit pool-tier input resolved against its factory.
"""
from __future__ import annotations

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quickswap_v3 import QuickSwapV3ExactQuoter
from .route_simulator import RouteSimulation, simulate_two_leg
from .uniswap_v3 import UniswapV3ExactQuoter

POLYGON_CHAIN_ID = 137

QUICKSWAP_V3_TO_UNISWAP_V3_PATH = "quickswap_v3->uniswap_v3"
UNISWAP_V3_TO_QUICKSWAP_V3_PATH = "uniswap_v3->quickswap_v3"


def _context(rpc, block: MarketBlockSnapshot | None) -> MarketBlockSnapshot:
    context = block if block is not None else acquire_market_block(rpc)
    if context.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("route requires Polygon mainnet")
    return context


def build_quickswap_v3_to_uniswap_v3_route(
    rpc,
    quickswap_v3: QuickSwapV3ExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    uniswap_fee: int,
    quickswap_limit_sqrt_price: int = 0,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = quickswap_v3.quote_snapshot(
        amount_in, token_a, token_b, context,
        limit_sqrt_price=quickswap_limit_sqrt_price,
    )
    second = uniswap_v3.quote_snapshot(
        first.amount_out, token_b, token_a, uniswap_fee, context,
    )
    return simulate_two_leg(first, second)


def build_uniswap_v3_to_quickswap_v3_route(
    rpc,
    quickswap_v3: QuickSwapV3ExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    uniswap_fee: int,
    quickswap_limit_sqrt_price: int = 0,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = uniswap_v3.quote_snapshot(
        amount_in, token_a, token_b, uniswap_fee, context,
    )
    second = quickswap_v3.quote_snapshot(
        first.amount_out, token_b, token_a, context,
        limit_sqrt_price=quickswap_limit_sqrt_price,
    )
    return simulate_two_leg(first, second)


__all__ = [
    "POLYGON_CHAIN_ID",
    "QUICKSWAP_V3_TO_UNISWAP_V3_PATH",
    "UNISWAP_V3_TO_QUICKSWAP_V3_PATH",
    "build_quickswap_v3_to_uniswap_v3_route",
    "build_uniswap_v3_to_quickswap_v3_route",
]
