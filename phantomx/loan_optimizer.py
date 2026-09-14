"""Exact-quote loan-size optimizer for the Phase-19 execution spine.

This module deliberately does not model slippage from pool reserves, infer a
percentage spread, or use floating-point PnL. It selects the best loan amount
from an explicit set of amounts after each amount has been evaluated by the
real quote/economic-proof pipeline.

The result is therefore exact over the supplied candidate domain, not a claim
of a continuous mathematical optimum. A future caller may generate the
candidate domain from on-chain liquidity bounds, but the optimizer itself never
turns a liquidity proxy into execution truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable

from .economic_proof import EconomicProof, EconomicProofError


class LoanOptimizationError(ValueError):
    """Raised when a loan-size search cannot be proven safe and deterministic."""


@dataclass(frozen=True)
class LoanEvaluation:
    """One exact candidate evaluation at one pinned market block."""

    loan_amount: int
    chain_id: int
    block_number: int
    proof: EconomicProof

    def __post_init__(self) -> None:
        if not isinstance(self.loan_amount, int) or isinstance(self.loan_amount, bool):
            raise LoanOptimizationError("loan_amount must be an integer")
        if self.loan_amount <= 0:
            raise LoanOptimizationError("loan_amount must be positive")
        if self.chain_id <= 0 or self.block_number < 0:
            raise LoanOptimizationError("invalid candidate chain/block")
        if not isinstance(self.proof, EconomicProof):
            raise LoanOptimizationError("candidate must contain an EconomicProof")


@dataclass(frozen=True)
class LoanOptimizationResult:
    """Best economically valid candidate and the complete evaluated domain."""

    best: LoanEvaluation
    evaluated: tuple[LoanEvaluation, ...]

    @property
    def best_net_profit_usd(self) -> Decimal:
        return self.best.proof.worst_case_net_profit_usd


def candidate_amount_grid(min_amount: int, max_amount: int, step: int) -> tuple[int, ...]:
    """Generate a deterministic inclusive integer candidate grid."""
    for name, value in (("min_amount", min_amount), ("max_amount", max_amount), ("step", step)):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise LoanOptimizationError(f"{name} must be a positive integer")
    if max_amount < min_amount:
        raise LoanOptimizationError("max_amount must be >= min_amount")

    values = tuple(range(min_amount, max_amount + 1, step))
    if not values:
        raise LoanOptimizationError("candidate grid is empty")
    return values


def optimize_exact_candidates(
    candidate_amounts: Iterable[int],
    evaluate: Callable[[int], LoanEvaluation],
) -> LoanOptimizationResult:
    """Evaluate every candidate and select the highest strict-proof PnL.

    Every candidate is evaluated. Exceptions from the evaluator are fatal rather
    than silently skipped, because an incomplete search cannot justify an
    optimization decision. Candidates at or below the strict economic floor are
    retained as evidence but are never eligible for selection.

    Ties are resolved toward the smaller loan amount, giving deterministic and
    conservative sizing when two candidates have identical worst-case PnL.
    All candidates must refer to the same chain and pinned market block so the
    comparison does not mix incompatible market states.
    """
    amounts = tuple(candidate_amounts)
    if not amounts:
        raise LoanOptimizationError("candidate domain cannot be empty")

    normalized: list[int] = []
    seen: set[int] = set()
    for amount in amounts:
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise LoanOptimizationError("all candidate loan amounts must be positive integers")
        if amount in seen:
            raise LoanOptimizationError("duplicate loan amount in candidate domain")
        seen.add(amount)
        normalized.append(amount)

    evaluations: list[LoanEvaluation] = []
    for amount in normalized:
        try:
            evaluation = evaluate(amount)
        except EconomicProofError as exc:
            raise LoanOptimizationError(f"economic proof construction failed for {amount}") from exc
        except Exception as exc:
            raise LoanOptimizationError(f"candidate evaluation failed for {amount}") from exc
        if not isinstance(evaluation, LoanEvaluation):
            raise LoanOptimizationError("evaluator returned an invalid candidate")
        if evaluation.loan_amount != amount:
            raise LoanOptimizationError("evaluator returned a different loan amount")
        evaluations.append(evaluation)

    chain_block = {(item.chain_id, item.block_number) for item in evaluations}
    if len(chain_block) != 1:
        raise LoanOptimizationError("candidate evaluations must share one chain and pinned block")

    valid = [item for item in evaluations if item.proof.economically_valid]
    if not valid:
        raise LoanOptimizationError("no candidate exceeds the strict minimum net profit")

    best = max(
        valid,
        key=lambda item: (item.proof.worst_case_net_profit_usd, -item.loan_amount),
    )
    return LoanOptimizationResult(best=best, evaluated=tuple(evaluations))
