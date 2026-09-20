"""Deterministic opportunity discovery over exact route evaluations.

The discovery layer is intentionally valuation- and execution-independent. It
asks an injected route evaluator for exact, block-pinned simulations, records
both profitable and unprofitable candidates, and never converts a forecast or
spot spread into an execution claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .route_simulator import RouteSimulation


class OpportunityDiscoveryError(ValueError):
    """Raised when the discovery domain cannot be evaluated safely."""


@dataclass(frozen=True)
class OpportunityCandidate:
    """One exact route/loan observation from the discovery frontier."""

    token_a: str
    token_b: str
    venue_path: str
    loan_amount: int
    simulation: RouteSimulation

    @property
    def gross_delta(self) -> int:
        return self.simulation.final_amount - self.simulation.initial_amount

    @property
    def gross_positive(self) -> bool:
        return self.gross_delta > 0


@dataclass(frozen=True)
class OpportunityDiscoveryResult:
    """Complete evaluated frontier plus exact gross-positive candidates."""

    evaluated: tuple[OpportunityCandidate, ...]

    @property
    def gross_positive(self) -> tuple[OpportunityCandidate, ...]:
        return tuple(item for item in self.evaluated if item.gross_positive)


def discover_exact_opportunities(
    *,
    token_pairs: Iterable[tuple[str, str]],
    loan_amounts: Iterable[int],
    evaluate_route: Callable[[str, str, int], RouteSimulation],
    venue_path: str,
) -> OpportunityDiscoveryResult:
    """Evaluate the complete explicit search domain without skipping errors.

    The evaluator must source exact quotes from the current market state. This
    function only organizes that evidence. Every candidate is evaluated, and
    any evaluator failure aborts the discovery pass rather than creating a
    partial ranking.
    """
    pairs = tuple(token_pairs)
    amounts = tuple(loan_amounts)
    if not pairs:
        raise OpportunityDiscoveryError("token pair domain cannot be empty")
    if not amounts:
        raise OpportunityDiscoveryError("loan amount domain cannot be empty")
    if not isinstance(venue_path, str) or not venue_path.strip():
        raise OpportunityDiscoveryError("venue_path must be non-empty")

    normalized_amounts: list[int] = []
    seen_amounts: set[int] = set()
    for amount in amounts:
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise OpportunityDiscoveryError("loan amounts must be positive integers")
        if amount in seen_amounts:
            raise OpportunityDiscoveryError("loan amount domain contains duplicates")
        seen_amounts.add(amount)
        normalized_amounts.append(amount)

    evaluated: list[OpportunityCandidate] = []
    for token_a, token_b in pairs:
        if not isinstance(token_a, str) or not token_a.strip() or not isinstance(token_b, str) or not token_b.strip():
            raise OpportunityDiscoveryError("token pair identities must be non-empty")
        if token_a.lower() == token_b.lower():
            raise OpportunityDiscoveryError("token pair cannot contain the same asset")
        for amount in normalized_amounts:
            try:
                simulation = evaluate_route(token_a, token_b, amount)
            except Exception as exc:
                raise OpportunityDiscoveryError(
                    f"route evaluation failed for {token_a}->{token_b} amount={amount}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            if not isinstance(simulation, RouteSimulation):
                raise OpportunityDiscoveryError("route evaluator returned an invalid simulation")
            if simulation.initial_amount != amount:
                raise OpportunityDiscoveryError("route evaluator returned a mismatched initial amount")
            if simulation.legs[0].token_in.lower() != token_a.lower():
                raise OpportunityDiscoveryError("simulation does not bind token_a")
            if simulation.legs[-1].token_out.lower() != token_a.lower():
                raise OpportunityDiscoveryError("simulation does not return to token_a")
            evaluated.append(
                OpportunityCandidate(
                    token_a=token_a,
                    token_b=token_b,
                    venue_path=venue_path,
                    loan_amount=amount,
                    simulation=simulation,
                )
            )

    blocks = {(item.simulation.chain_id, item.simulation.block_number) for item in evaluated}
    if len(blocks) != 1:
        raise OpportunityDiscoveryError("all discovered candidates must share one chain and pinned block")

    return OpportunityDiscoveryResult(evaluated=tuple(evaluated))
