"""Read-only Curve <-> Uniswap V3 route composition."""
from __future__ import annotations

from .curve import CurvePoolRef, CurveRegistryExactQuoter
from .market_block import MarketBlockSnapshot, acquire_market_block
from .route_simulator import RouteSimulation, simulate_two_leg
from .uniswap_v3 import UniswapV3ExactQuoter

POLYGON_CHAIN_ID = 137
CURVE_TO_UNISWAP_V3_PATH = "curve->uniswap_v3"
UNISWAP_V3_TO_CURVE_PATH = "uniswap_v3->curve"


def _context(rpc, block: MarketBlockSnapshot | None) -> MarketBlockSnapshot:
    context = block if block is not None else acquire_market_block(rpc)
    if context.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("route requires Polygon mainnet")
    return context


def build_curve_to_uniswap_v3_route(
    rpc,
    curve: CurveRegistryExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    curve_pool: CurvePoolRef,
    uniswap_fee: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = curve.quote_snapshot(amount_in, curve_pool, context)
    second = uniswap_v3.quote_snapshot(first.amount_out, token_b, token_a, uniswap_fee, context)
    return simulate_two_leg(first, second)


def build_uniswap_v3_to_curve_route(
    rpc,
    curve: CurveRegistryExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    curve_pool: CurvePoolRef,
    uniswap_fee: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = uniswap_v3.quote_snapshot(amount_in, token_a, token_b, uniswap_fee, context)
    second = curve.quote_snapshot(first.amount_out, curve_pool, context)
    return simulate_two_leg(first, second)


__all__ = [
    "POLYGON_CHAIN_ID",
    "CURVE_TO_UNISWAP_V3_PATH",
    "UNISWAP_V3_TO_CURVE_PATH",
    "build_curve_to_uniswap_v3_route",
    "build_uniswap_v3_to_curve_route",
]
