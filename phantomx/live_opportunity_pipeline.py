"""Compose concrete live discovery with proven economic execution preparation.

This module adds the missing orchestration seam between the concrete cross-venue
market scanner and the existing economic/execution boundaries. It performs no
signing, submission, broadcast, or live-capital operation.
"""
from __future__ import annotations

from typing import Callable, Iterable

from .cross_venue_discovery import (
    QUICKSWAP_TO_UNISWAP_PATH,
    UNISWAP_TO_QUICKSWAP_PATH,
    discover_cross_venue_opportunities,
)
from .cross_venue_route import QuickSwapV2ExactQuoter, UniswapV3ExactQuoter
from .execution_assembly import ExecutionAssembly
from .opportunity_discovery import OpportunityDiscoveryResult
from .opportunity_economics import OpportunityEconomicsResult
from .opportunity_pipeline import prepare_best_opportunity_execution


class LiveOpportunityPipelineError(ValueError):
    """Raised when live opportunity preparation cannot be proven safely."""


def discover_and_prepare_best_opportunity_execution(
    rpc,
    quickswap: QuickSwapV2ExactQuoter,
    uniswap: UniswapV3ExactQuoter,
    *,
    token_pairs: Iterable[tuple[str, str]],
    loan_amounts: Iterable[int],
    uniswap_fee: int,
    build_proof_for: Callable,
    executor: str,
    sender: str,
    nonce: int,
    deadline: int,
    amount_out_min_first: int,
    amount_out_min_second: int,
    minimum_surplus: int,
    aave_pool: str,
    quickswap_router: str,
    uniswap_v3_router: str,
    gas_limit: int,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block=None,
) -> tuple[OpportunityDiscoveryResult, OpportunityEconomicsResult, ExecutionAssembly]:
    """Discover the complete exact frontier, prove economics, and assemble its winner.

    Discovery and execution preparation share the same pinned block. No partial
    frontier is returned, and execution assembly is attempted only after the
    downstream strict economic gate selects a winner.
    """
    try:
        discovery = discover_cross_venue_opportunities(
            rpc,
            quickswap,
            uniswap,
            token_pairs=token_pairs,
            loan_amounts=loan_amounts,
            uniswap_fee=uniswap_fee,
            quickswap_gas_estimate=quickswap_gas_estimate,
            uniswap_gas_estimate=uniswap_gas_estimate,
            block=block,
        )
        economics, assembly = prepare_best_opportunity_execution(
            discovery.evaluated,
            build_proof_for,
            executor=executor,
            sender=sender,
            nonce=nonce,
            deadline=deadline,
            amount_out_min_first=amount_out_min_first,
            amount_out_min_second=amount_out_min_second,
            minimum_surplus=minimum_surplus,
            aave_pool=aave_pool,
            quickswap_router=quickswap_router,
            uniswap_v3_router=uniswap_v3_router,
            gas_limit=gas_limit,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
        )
    except Exception as exc:
        if isinstance(exc, LiveOpportunityPipelineError):
            raise
        raise LiveOpportunityPipelineError("live opportunity preparation failed") from exc
    return discovery, economics, assembly


__all__ = [
    "LiveOpportunityPipelineError",
    "discover_and_prepare_best_opportunity_execution",
    "QUICKSWAP_TO_UNISWAP_PATH",
    "UNISWAP_TO_QUICKSWAP_PATH",
]
