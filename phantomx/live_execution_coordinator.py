"""Bridge concrete live opportunity discovery into durable signed execution.

This module composes the real discovery/economic frontier with the existing
execution coordinator. The coordinator owns nonce reservation, exact assembly,
EVM preflight, canonical Governor policy, signing, and durable persistence.
This bridge never submits, broadcasts, or moves live capital.
"""
from __future__ import annotations

from typing import Callable, Iterable

from .cross_venue_discovery import (
    QUICKSWAP_TO_UNISWAP_PATH,
    UNISWAP_TO_QUICKSWAP_PATH,
    discover_cross_venue_opportunities,
)
from .execution_coordinator import ExecutionCoordinatorError, PreparedExecution, prepare_signed_execution
from .governor import GovernorPolicy
from .opportunity_economics import EconomicProof, OpportunityEconomicsResult, evaluate_discovered_opportunities
from .opportunity_discovery import OpportunityDiscoveryResult
from .production_authority_evidence import AuthorityEvidenceReusePolicy
from .quickswap_v2 import QuickSwapV2ExactQuoter
from .signer import TransactionSigner
from .sqlite_execution_store import SQLiteExecutionStore
from .executor_authority import ExecutorAuthorityEvidence
from .uniswap_v3 import UniswapV3ExactQuoter


class LiveExecutionCoordinatorError(RuntimeError):
    """Raised when live opportunity preparation cannot reach a durable signed artifact safely."""


def discover_and_prepare_signed_execution(
    rpc,
    quickswap: QuickSwapV2ExactQuoter,
    uniswap: UniswapV3ExactQuoter,
    *,
    token_pairs: Iterable[tuple[str, str]],
    loan_amounts: Iterable[int],
    uniswap_fee: int,
    build_proof_for: Callable,
    store: SQLiteExecutionStore,
    executor: str,
    sender: str,
    executor_authority: ExecutorAuthorityEvidence,
    authority_evidence_reuse_policy: AuthorityEvidenceReusePolicy,
    chain_pending_nonce: int,
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
    policy: GovernorPolicy,
    signer: TransactionSigner,
    now: int,
    current_block_number: int,
    ai_rank=None,
    reservation_id: str | None = None,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block=None,
) -> tuple[OpportunityDiscoveryResult, OpportunityEconomicsResult, PreparedExecution]:
    """Discover the complete frontier and carry only its proven winner into durable signing.

    The selected opportunity's exact simulation and economic proof become the
    authoritative inputs to ``prepare_signed_execution``. That coordinator then
    reserves the chain-pending nonce, reconstructs the execution envelope with
    that nonce, reruns preflight and Governor checks, signs once, and persists the
    signed artifact. No public/private relay submission occurs here.
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
        economics = evaluate_discovered_opportunities(discovery.evaluated, build_proof_for)
        evaluation = economics.best

        if evaluation.candidate.venue_path == QUICKSWAP_TO_UNISWAP_PATH:
            first_on_quickswap = True
        elif evaluation.candidate.venue_path == UNISWAP_TO_QUICKSWAP_PATH:
            first_on_quickswap = False
        else:
            raise LiveExecutionCoordinatorError("unsupported discovered venue path")

        prepared = prepare_signed_execution(
            store=store,
            simulation=evaluation.candidate.simulation,
            economic_proof=evaluation.proof,
            executor=executor,
            sender=sender,
            executor_authority=executor_authority,
            authority_evidence_reuse_policy=authority_evidence_reuse_policy,
            chain_pending_nonce=chain_pending_nonce,
            deadline=deadline,
            first_on_quickswap=first_on_quickswap,
            amount_out_min_first=amount_out_min_first,
            amount_out_min_second=amount_out_min_second,
            minimum_surplus=minimum_surplus,
            aave_pool=aave_pool,
            quickswap_router=quickswap_router,
            uniswap_v3_router=uniswap_v3_router,
            gas_limit=gas_limit,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            policy=policy,
            signer=signer,
            now=now,
            current_block_number=current_block_number,
            ai_rank=ai_rank,
            reservation_id=reservation_id,
        )
        return discovery, economics, prepared
    except (LiveExecutionCoordinatorError, ExecutionCoordinatorError):
        raise
    except Exception as exc:
        raise LiveExecutionCoordinatorError("live execution coordination failed") from exc


__all__ = ["LiveExecutionCoordinatorError", "discover_and_prepare_signed_execution"]
