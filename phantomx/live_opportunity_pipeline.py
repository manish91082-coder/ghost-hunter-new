"""Compose concrete live discovery through the execution governor.

This module provides deterministic orchestration before the signer boundary. It
performs no signing, submission, broadcast, or live-capital operation.
"""
from __future__ import annotations

from typing import Callable, Iterable

from .cross_venue_discovery import (
    QUICKSWAP_TO_UNISWAP_PATH,
    UNISWAP_TO_QUICKSWAP_PATH,
    discover_cross_venue_opportunities,
)
from .evm_preflight import EVMPreflightResult, preflight_execution
from .execution_assembly import ExecutionAssembly
from .execution_governor import GovernorDecision, GovernorPolicy, govern_execution
from .executor_authority import ExecutorAuthorityEvidence
from .opportunity_discovery import OpportunityDiscoveryResult
from .opportunity_economics import OpportunityEconomicsResult
from .opportunity_pipeline import prepare_best_opportunity_execution
from .quickswap_v2 import QuickSwapV2ExactQuoter
from .uniswap_v3 import UniswapV3ExactQuoter


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
    """Discover the exact frontier, prove economics, and assemble its winner."""
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


def discover_prepare_and_preflight_best_opportunity(
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
    now: int,
    executor_authority: ExecutorAuthorityEvidence | None = None,
    expected_route_commitment: str | None = None,
    expected_chain_id: int = 137,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block=None,
) -> tuple[OpportunityDiscoveryResult, OpportunityEconomicsResult, ExecutionAssembly, EVMPreflightResult]:
    """Run live discovery, economic assembly, and EVM preflight."""
    try:
        discovery, economics, assembly = discover_and_prepare_best_opportunity_execution(
            rpc,
            quickswap,
            uniswap,
            token_pairs=token_pairs,
            loan_amounts=loan_amounts,
            uniswap_fee=uniswap_fee,
            build_proof_for=build_proof_for,
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
            quickswap_gas_estimate=quickswap_gas_estimate,
            uniswap_gas_estimate=uniswap_gas_estimate,
            block=block,
        )
        preflight = preflight_execution(
            intent=assembly.intent,
            authorization=assembly.authorization,
            envelope=assembly.envelope,
            simulation=assembly.simulation,
            economic_proof=assembly.economic_proof,
            now=now,
            expected_chain_id=expected_chain_id,
            expected_route_commitment=expected_route_commitment,
            executor_authority=executor_authority,
        )
    except Exception as exc:
        if isinstance(exc, LiveOpportunityPipelineError):
            raise
        raise LiveOpportunityPipelineError("live opportunity preflight failed") from exc
    return discovery, economics, assembly, preflight


def discover_prepare_preflight_and_govern_best_opportunity(
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
    now: int,
    governor_policy: GovernorPolicy,
    executor_authority: ExecutorAuthorityEvidence | None = None,
    expected_route_commitment: str | None = None,
    expected_chain_id: int = 137,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block=None,
) -> tuple[OpportunityDiscoveryResult, OpportunityEconomicsResult, ExecutionAssembly, EVMPreflightResult, GovernorDecision]:
    """Run the complete deterministic pipeline through the pre-signer governor."""
    try:
        discovery, economics, assembly, preflight = discover_prepare_and_preflight_best_opportunity(
            rpc,
            quickswap,
            uniswap,
            token_pairs=token_pairs,
            loan_amounts=loan_amounts,
            uniswap_fee=uniswap_fee,
            build_proof_for=build_proof_for,
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
            now=now,
            executor_authority=executor_authority,
            expected_route_commitment=expected_route_commitment,
            expected_chain_id=expected_chain_id,
            quickswap_gas_estimate=quickswap_gas_estimate,
            uniswap_gas_estimate=uniswap_gas_estimate,
            block=block,
        )
        decision = govern_execution(
            preflight=preflight,
            assembly=assembly,
            policy=governor_policy,
            now=now,
        )
    except Exception as exc:
        if isinstance(exc, LiveOpportunityPipelineError):
            raise
        raise LiveOpportunityPipelineError("live opportunity governor rejected execution") from exc
    return discovery, economics, assembly, preflight, decision


__all__ = [
    "LiveOpportunityPipelineError",
    "discover_and_prepare_best_opportunity_execution",
    "discover_prepare_and_preflight_best_opportunity",
    "discover_prepare_preflight_and_govern_best_opportunity",
    "QUICKSWAP_TO_UNISWAP_PATH",
    "UNISWAP_TO_QUICKSWAP_PATH",
]
