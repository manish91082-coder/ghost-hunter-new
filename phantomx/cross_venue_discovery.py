"""Concrete exact opportunity discovery across both supported venue directions.

The frontier acquires one canonical Polygon block and reuses that immutable
context for every exact quote. Discovery is valuation-independent: gross
positive observations are recorded, but no executable profitability claim is
made here.
"""
from __future__ import annotations

from typing import Iterable

from .cross_venue_route import (
    build_quickswap_to_uniswap_route,
    build_uniswap_to_quickswap_route,
)
from .market_block import MarketBlockSnapshot, acquire_market_block
from .opportunity_discovery import (
    OpportunityCandidate,
    OpportunityDiscoveryResult,
    discover_exact_opportunities,
)
from .quickswap_v2 import QuickSwapV2ExactQuoter
from .uniswap_v3 import UniswapV3ExactQuoter


QUICKSWAP_TO_UNISWAP_PATH = "quickswap_v2->uniswap_v3"
UNISWAP_TO_QUICKSWAP_PATH = "uniswap_v3->quickswap_v2"


def discover_cross_venue_opportunities(
    rpc,
    quickswap: QuickSwapV2ExactQuoter,
    uniswap: UniswapV3ExactQuoter,
    *,
    token_pairs: Iterable[tuple[str, str]],
    loan_amounts: Iterable[int],
    uniswap_fee: int,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block: MarketBlockSnapshot | None = None,
    continue_on_error: bool = False,
) -> OpportunityDiscoveryResult:
    """Evaluate the complete two-direction frontier at one pinned block.

    A caller may provide a previously verified ``MarketBlockSnapshot``. When
    omitted, this function acquires the block exactly once before evaluating
    either venue direction. All exact route calls receive that same context.
    """
    if not isinstance(uniswap_fee, int) or isinstance(uniswap_fee, bool) or not 0 <= uniswap_fee < (1 << 24):
        raise ValueError("uniswap_fee must be a uint24 integer")

    pairs = tuple(token_pairs)
    amounts = tuple(loan_amounts)
    context = block if block is not None else acquire_market_block(rpc)

    forward = discover_exact_opportunities(
        token_pairs=pairs,
        loan_amounts=amounts,
        venue_path=QUICKSWAP_TO_UNISWAP_PATH,
        continue_on_error=continue_on_error,
        evaluate_route=lambda token_a, token_b, amount: build_quickswap_to_uniswap_route(
            rpc,
            quickswap,
            uniswap,
            amount_in=amount,
            token_a=token_a,
            token_b=token_b,
            uniswap_fee=uniswap_fee,
            quickswap_gas_estimate=quickswap_gas_estimate,
            uniswap_gas_estimate=uniswap_gas_estimate,
            block=context,
        ),
    )

    reverse = discover_exact_opportunities(
        token_pairs=pairs,
        loan_amounts=amounts,
        venue_path=UNISWAP_TO_QUICKSWAP_PATH,
        continue_on_error=continue_on_error,
        evaluate_route=lambda token_a, token_b, amount: build_uniswap_to_quickswap_route(
            rpc,
            quickswap,
            uniswap,
            amount_in=amount,
            token_a=token_a,
            token_b=token_b,
            uniswap_fee=uniswap_fee,
            quickswap_gas_estimate=quickswap_gas_estimate,
            uniswap_gas_estimate=uniswap_gas_estimate,
            block=context,
        ),
    )

    combined: tuple[OpportunityCandidate, ...] = forward.evaluated + reverse.evaluated
    return OpportunityDiscoveryResult(evaluated=combined)
