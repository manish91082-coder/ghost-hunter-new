"""Deterministic discovered-opportunity to execution-preparation pipeline.

The pipeline composes the existing discovery, economic-proof, and execution
boundaries. It introduces no market assumptions and performs no signing,
submission, or broadcast. Callers supply discovery candidates and genuine
valuation/cost evidence explicitly.
"""
from __future__ import annotations

from typing import Callable, Iterable

from .execution_assembly import ExecutionAssembly
from .opportunity_discovery import OpportunityCandidate
from .opportunity_economics import (
    OpportunityEconomicEvaluation,
    OpportunityEconomicsResult,
    evaluate_discovered_opportunities,
)
from .opportunity_execution import assemble_proven_opportunity


class OpportunityPipelineError(ValueError):
    """Raised when complete opportunity preparation cannot be proven safely."""


def prepare_best_opportunity_execution(
    candidates: Iterable[OpportunityCandidate],
    build_proof_for: Callable,
    *,
    executor: str,
    sender: str,
    nonce: int,
    deadline: int,
    amount_out_min_first: int,
    amount_out_min_second: int,
    minimum_surplus: int,
    aave_pool: str,
    uniswap_v3_router: str,
    quickswap_v2_router: str | None = None,
    quickswap_v3_router: str | None = None,
    quickswap_router: str | None = None,
    gas_limit: int,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
) -> tuple[OpportunityEconomicsResult, ExecutionAssembly]:
    """Evaluate the complete discovered frontier, then assemble only its winner.

    The economic evaluator remains the sole selection authority. Execution is
    attempted only for the returned strictly profitable winner, preserving the
    separation between evidence evaluation and deterministic assembly. QuickSwap
    V2 and V3 router identities are passed explicitly when available; the legacy
    single-router argument remains only as a compatibility fallback.
    """
    try:
        economic_result = evaluate_discovered_opportunities(candidates, build_proof_for)
        evaluation = economic_result.best
        assembly = assemble_proven_opportunity(
            evaluation,
            executor=executor,
            sender=sender,
            nonce=nonce,
            deadline=deadline,
            amount_out_min_first=amount_out_min_first,
            amount_out_min_second=amount_out_min_second,
            minimum_surplus=minimum_surplus,
            aave_pool=aave_pool,
            quickswap_v2_router=quickswap_v2_router,
            quickswap_v3_router=quickswap_v3_router,
            quickswap_router=quickswap_router,
            uniswap_v3_router=uniswap_v3_router,
            gas_limit=gas_limit,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
        )
    except Exception as exc:
        if isinstance(exc, (OpportunityPipelineError,)):
            raise
        raise OpportunityPipelineError("opportunity preparation failed") from exc
    return economic_result, assembly
