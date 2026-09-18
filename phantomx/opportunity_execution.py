"""Execution hand-off for an economically proven discovered opportunity.

This module is the narrow bridge between opportunity economics and deterministic
execution assembly. It does not quote, value, sign, submit, or broadcast.
"""
from __future__ import annotations

from .cross_venue_discovery import (
    QUICKSWAP_TO_UNISWAP_PATH,
    UNISWAP_TO_QUICKSWAP_PATH,
)
from .cross_venue_qsv3_route import (
    QUICKSWAP_V3_TO_UNISWAP_V3_PATH,
    UNISWAP_V3_TO_QUICKSWAP_V3_PATH,
)
from .execution_assembly import ExecutionAssembly, ExecutionAssemblyError, assemble_execution
from .opportunity_economics import OpportunityEconomicEvaluation


class OpportunityExecutionError(ValueError):
    """Raised when a proven opportunity cannot be safely mapped to execution."""


def assemble_proven_opportunity(
    evaluation: OpportunityEconomicEvaluation,
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
    gas_limit: int,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    quickswap_v2_router: str | None = None,
    quickswap_v3_router: str | None = None,
    quickswap_router: str | None = None,
) -> ExecutionAssembly:
    """Assemble execution only from a strictly profitable discovered evaluation.

    Venue direction is taken from the immutable opportunity label and must agree
    with the route's actual dex ordering. Output minima and transaction controls
    remain explicit caller inputs, so this bridge never invents execution safety
    margins from discovery data.
    """
    if quickswap_v2_router is None:
        quickswap_v2_router = quickswap_router
    if quickswap_v3_router is None:
        quickswap_v3_router = quickswap_router if quickswap_router is not None else quickswap_v2_router
    if quickswap_v2_router is None or quickswap_v3_router is None:
        raise OpportunityExecutionError("QuickSwap V2/V3 router addresses are required")
    if not isinstance(evaluation, OpportunityEconomicEvaluation):
        raise OpportunityExecutionError("evaluation must be an OpportunityEconomicEvaluation")
    if not evaluation.economically_valid:
        raise OpportunityExecutionError("opportunity is not above the strict economic floor")

    path = evaluation.candidate.venue_path
    if path == QUICKSWAP_TO_UNISWAP_PATH:
        first_on_quickswap = True
        quickswap_venue_kind = 1
    elif path == UNISWAP_TO_QUICKSWAP_PATH:
        first_on_quickswap = False
        quickswap_venue_kind = 1
    elif path == QUICKSWAP_V3_TO_UNISWAP_V3_PATH:
        first_on_quickswap = True
        quickswap_venue_kind = 2
    elif path == UNISWAP_V3_TO_QUICKSWAP_V3_PATH:
        first_on_quickswap = False
        quickswap_venue_kind = 2
    else:
        raise OpportunityExecutionError("unsupported discovered venue path")

    simulation = evaluation.candidate.simulation
    if simulation.initial_amount != evaluation.candidate.loan_amount:
        raise OpportunityExecutionError("candidate loan amount does not match simulation")

    try:
        return assemble_execution(
            simulation=simulation,
            economic_proof=evaluation.proof,
            executor=executor,
            sender=sender,
            nonce=nonce,
            deadline=deadline,
            first_on_quickswap=first_on_quickswap,
            quickswap_venue_kind=quickswap_venue_kind,
            amount_out_min_first=amount_out_min_first,
            amount_out_min_second=amount_out_min_second,
            minimum_surplus=minimum_surplus,
            aave_pool=aave_pool,
            quickswap_v2_router=quickswap_v2_router,
            quickswap_v3_router=quickswap_v3_router,
            uniswap_v3_router=uniswap_v3_router,
            gas_limit=gas_limit,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
        )
    except ExecutionAssemblyError as exc:
        raise OpportunityExecutionError("execution assembly rejected proven opportunity") from exc
