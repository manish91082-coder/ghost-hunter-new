"""Canonical governor seam for the pre-signer execution boundary.

This adapter reuses the already-tested live discovery/preflight path and feeds
its exact immutable artifacts into the repository's canonical ``governor.py``.
It never signs, submits, broadcasts, or moves live capital.
"""
from __future__ import annotations

from typing import Callable

from .execution import ExecutionState
from .execution_assembly import ExecutionAssembly
from .executor_authority import ExecutorAuthorityEvidence
from .governor import GovernorDecision, GovernorPolicy, govern_execution
from .live_opportunity_pipeline import (
    LiveOpportunityPipelineError,
    discover_prepare_and_preflight_best_opportunity,
)


class CanonicalGovernorPipelineError(ValueError):
    """Raised when the canonical pre-signer governor rejects the artifact chain."""


def govern_live_preflight_artifact(
    *,
    assembly: ExecutionAssembly,
    preflight,
    executor_authority: ExecutorAuthorityEvidence,
    policy_factory: Callable[[ExecutionAssembly], GovernorPolicy],
    lifecycle_state: ExecutionState,
    nonce_reserved: bool,
    replay_consumed: bool,
    current_block_number: int,
    now: int,
    ai_rank=None,
) -> GovernorDecision:
    """Apply the canonical governor to one exact preflight/assembly pair."""
    try:
        if not isinstance(assembly, ExecutionAssembly):
            raise CanonicalGovernorPipelineError("execution assembly is required")
        policy = policy_factory(assembly)
        if not isinstance(policy, GovernorPolicy):
            raise CanonicalGovernorPipelineError("policy factory must return GovernorPolicy")
        return govern_execution(
            policy=policy,
            preflight=preflight,
            intent=assembly.intent,
            envelope=assembly.envelope,
            economic_proof=assembly.economic_proof,
            executor_authority=executor_authority,
            lifecycle_state=lifecycle_state,
            nonce_reserved=nonce_reserved,
            replay_consumed=replay_consumed,
            current_block_number=current_block_number,
            now=now,
            ai_rank=ai_rank,
        )
    except CanonicalGovernorPipelineError:
        raise
    except Exception as exc:
        raise CanonicalGovernorPipelineError("canonical governor evaluation failed") from exc


def discover_prepare_preflight_and_canonical_govern_best_opportunity(
    rpc,
    quickswap,
    uniswap,
    *,
    token_pairs,
    loan_amounts,
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
    policy_factory: Callable[[ExecutionAssembly], GovernorPolicy],
    executor_authority: ExecutorAuthorityEvidence,
    lifecycle_state: ExecutionState,
    nonce_reserved: bool,
    replay_consumed: bool,
    current_block_number: int,
    expected_route_commitment: str | None = None,
    expected_chain_id: int = 137,
    quickswap_gas_estimate: int | None = None,
    uniswap_gas_estimate: int | None = None,
    block=None,
    ai_rank=None,
):
    """Run concrete discovery, economics, assembly, preflight, and canonical governance."""
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
        decision = govern_live_preflight_artifact(
            assembly=assembly,
            preflight=preflight,
            executor_authority=executor_authority,
            policy_factory=policy_factory,
            lifecycle_state=lifecycle_state,
            nonce_reserved=nonce_reserved,
            replay_consumed=replay_consumed,
            current_block_number=current_block_number,
            now=now,
            ai_rank=ai_rank,
        )
        return discovery, economics, assembly, preflight, decision
    except (CanonicalGovernorPipelineError, LiveOpportunityPipelineError):
        raise
    except Exception as exc:
        raise CanonicalGovernorPipelineError("canonical live governor pipeline failed") from exc


__all__ = [
    "CanonicalGovernorPipelineError",
    "govern_live_preflight_artifact",
    "discover_prepare_preflight_and_canonical_govern_best_opportunity",
]
