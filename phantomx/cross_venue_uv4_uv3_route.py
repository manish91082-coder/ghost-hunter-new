"""Read-only Uniswap V4 <-> Uniswap V3 route composition."""
from __future__ import annotations

from .market_block import MarketBlockSnapshot, acquire_market_block
from .route_simulator import RouteSimulation, simulate_two_leg
from .uniswap_v3 import UniswapV3ExactQuoter
from .uniswap_v4 import UniswapV4ExactQuoter, V4PoolKey

POLYGON_CHAIN_ID = 137
UNISWAP_V4_TO_V3_PATH = "uniswap_v4->uniswap_v3"
UNISWAP_V3_TO_V4_PATH = "uniswap_v3->uniswap_v4"


def _context(rpc, block: MarketBlockSnapshot | None) -> MarketBlockSnapshot:
    context = block if block is not None else acquire_market_block(rpc)
    if context.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("route requires Polygon mainnet")
    return context


def build_uniswap_v4_to_v3_route(
    rpc,
    uniswap_v4: UniswapV4ExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    v4_pool_key: V4PoolKey,
    v3_fee: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = uniswap_v4.quote_snapshot(amount_in, token_a, token_b, v4_pool_key, context)
    second = uniswap_v3.quote_snapshot(first.amount_out, token_b, token_a, v3_fee, context)
    return simulate_two_leg(first, second)


def build_uniswap_v3_to_v4_route(
    rpc,
    uniswap_v4: UniswapV4ExactQuoter,
    uniswap_v3: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    v4_pool_key: V4PoolKey,
    v3_fee: int,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    context = _context(rpc, block)
    first = uniswap_v3.quote_snapshot(amount_in, token_a, token_b, v3_fee, context)
    second = uniswap_v4.quote_snapshot(first.amount_out, token_b, token_a, v4_pool_key, context)
    return simulate_two_leg(first, second)


__all__ = [
    "POLYGON_CHAIN_ID",
    "UNISWAP_V4_TO_V3_PATH",
    "UNISWAP_V3_TO_V4_PATH",
    "build_uniswap_v4_to_v3_route",
    "build_uniswap_v3_to_v4_route",
]
