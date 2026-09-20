"""Deterministic cross-venue A→B→A route acquisition.

One market block is acquired exactly once and passed to every venue adapter.
This prevents the route from silently mixing observations from different
blocks. The composer remains read-only and execution-agnostic.
"""
from __future__ import annotations

from typing import Any, Protocol, Sequence

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quickswap_v2 import QuickSwapV2ExactQuoter
from .route_simulator import RouteSimulation, simulate_two_leg
from .uniswap_v3 import UniswapV3ExactQuoter


class CrossVenueRouteError(ValueError):
    """Raised when an exact route leg cannot be acquired at the pinned block."""

    def __init__(self, *, leg: str, venue: str, token_in: str, token_out: str, amount_in: int, fee: int | None, cause: BaseException) -> None:
        self.leg = leg
        self.venue = venue
        self.token_in = token_in
        self.token_out = token_out
        self.amount_in = amount_in
        self.fee = fee
        self.cause_type = type(cause).__name__
        self.cause_message = str(cause)
        super().__init__(
            f"{leg} leg failed venue={venue} token_in={token_in} token_out={token_out} "
            f"amount_in={amount_in} fee={fee} cause={self.cause_type}: {self.cause_message}"
        )


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform a read-only JSON-RPC request."""


def _context_or_acquire(rpc: RpcTransport, block: MarketBlockSnapshot | None) -> MarketBlockSnapshot:
    context = block if block is not None else acquire_market_block(rpc)
    if context.chain_id != 137:
        raise ValueError("route composer requires Polygon mainnet")
    return context


def build_quickswap_to_uniswap_route(
    rpc: RpcTransport,
    quickswap: QuickSwapV2ExactQuoter,
    uniswap: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    uniswap_fee: int,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    """Quote QuickSwap A→B then Uniswap V3 B→A at one shared block."""
    context = _context_or_acquire(rpc, block)

    try:
        first = quickswap.quote_snapshot(
            amount_in, [token_a, token_b], context, gas_estimate=quickswap_gas_estimate
        )
    except Exception as exc:
        raise CrossVenueRouteError(
            leg="first",
            venue="quickswap_v2",
            token_in=token_a,
            token_out=token_b,
            amount_in=amount_in,
            fee=None,
            cause=exc,
        ) from exc
    try:
        second = uniswap.quote_snapshot(
            first.amount_out, token_b, token_a, uniswap_fee, context,
            gas_estimate=uniswap_gas_estimate,
        )
    except Exception as exc:
        raise CrossVenueRouteError(
            leg="second",
            venue="uniswap_v3",
            token_in=token_b,
            token_out=token_a,
            amount_in=first.amount_out,
            fee=uniswap_fee,
            cause=exc,
        ) from exc
    return simulate_two_leg(first, second)


def build_uniswap_to_quickswap_route(
    rpc: RpcTransport,
    quickswap: QuickSwapV2ExactQuoter,
    uniswap: UniswapV3ExactQuoter,
    *,
    amount_in: int,
    token_a: str,
    token_b: str,
    uniswap_fee: int,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block: MarketBlockSnapshot | None = None,
) -> RouteSimulation:
    """Quote Uniswap V3 A→B then QuickSwap B→A at one shared block."""
    context = _context_or_acquire(rpc, block)

    try:
        first = uniswap.quote_snapshot(
            amount_in, token_a, token_b, uniswap_fee, context,
            gas_estimate=uniswap_gas_estimate,
        )
    except Exception as exc:
        raise CrossVenueRouteError(
            leg="first",
            venue="uniswap_v3",
            token_in=token_a,
            token_out=token_b,
            amount_in=amount_in,
            fee=uniswap_fee,
            cause=exc,
        ) from exc
    try:
        second = quickswap.quote_snapshot(
            first.amount_out, [token_b, token_a], context, gas_estimate=quickswap_gas_estimate
        )
    except Exception as exc:
        raise CrossVenueRouteError(
            leg="second",
            venue="quickswap_v2",
            token_in=token_b,
            token_out=token_a,
            amount_in=first.amount_out,
            fee=None,
            cause=exc,
        ) from exc
    return simulate_two_leg(first, second)
