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
class OpportunityFailure:
    """One exact route-evaluation failure retained as evidence."""

    token_a: str
    token_b: str
    venue_path: str
    loan_amount: int
    error_type: str
    error_message: str
    retryable: bool


@dataclass(frozen=True)
class OpportunityDiscoveryResult:
    """Evaluated frontier plus explicit success/failure evidence."""

    evaluated: tuple[OpportunityCandidate, ...]
    failures: tuple[OpportunityFailure, ...] = ()

    @property
    def retryable_failures(self) -> tuple[OpportunityFailure, ...]:
        return tuple(item for item in self.failures if item.retryable)

    @property
    def terminal_failures(self) -> tuple[OpportunityFailure, ...]:
        return tuple(item for item in self.failures if not item.retryable)

    @property
    def gross_positive(self) -> tuple[OpportunityCandidate, ...]:
        return tuple(item for item in self.evaluated if item.gross_positive)


def _is_retryable_failure(exc: BaseException) -> bool:
    """Only explicit RPC/infrastructure failures are retryable."""
    infrastructure_types = {
        "RPCPoolError",
        "PolygonRPCHTTPError",
        "URLError",
        "TimeoutError",
    }
    retry_markers = (
        "rpc error",
        "missing result",
        "historical state",
        "missing trie",
        "connection reset",
        "connection refused",
        "rate limit",
        "too many requests",
        "gateway",
        "service unavailable",
        "temporarily unavailable",
        "timeout",
        "timed out",
    )
    terminal_market_markers = (
        "no pair",
        "pool does not exist",
        "returned zero output",
        "zero output",
    )
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        # An exhausted bounded RPC recovery pass is itself an unresolved
        # infrastructure result, even if its collected provider errors mention
        # execution reverted. Preserve that unresolved state for fail-closed
        # coverage handling instead of converting it into a semantic market verdict.
        message = str(current).lower()
        if "all bounded polygon rpc recovery passes failed" in message:
            return True
        # Semantic EVM execution reverts are deterministic market/call outcomes
        # when they carry a concrete reason or occur on the default fail-closed
        # RPC path. They are not blindly retried by this discovery layer.
        if "execution reverted" in message:
            return False
        if type(current).__name__ in infrastructure_types:
            return True
        cause_type = getattr(current, "cause_type", None)
        if cause_type in infrastructure_types:
            return True
        message = str(current).lower()
        if any(marker in message for marker in terminal_market_markers):
            return False
        if any(marker in message for marker in retry_markers):
            return True
        current = current.__cause__
    return False


def discover_exact_opportunities(
    *,
    token_pairs: Iterable[tuple[str, str]],
    loan_amounts: Iterable[int],
    evaluate_route: Callable[[str, str, int], RouteSimulation],
    venue_path: str,
    continue_on_error: bool = False,
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
    failures: list[OpportunityFailure] = []
    for token_a, token_b in pairs:
        if not isinstance(token_a, str) or not token_a.strip() or not isinstance(token_b, str) or not token_b.strip():
            raise OpportunityDiscoveryError("token pair identities must be non-empty")
        if token_a.lower() == token_b.lower():
            raise OpportunityDiscoveryError("token pair cannot contain the same asset")
        for amount in normalized_amounts:
            try:
                simulation = evaluate_route(token_a, token_b, amount)
            except Exception as exc:
                if not continue_on_error:
                    raise OpportunityDiscoveryError(
                        f"route evaluation failed for {token_a}->{token_b} amount={amount}: "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
                failures.append(OpportunityFailure(
                    token_a=token_a,
                    token_b=token_b,
                    venue_path=venue_path,
                    loan_amount=amount,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    retryable=_is_retryable_failure(exc),
                ))
                continue
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
        if continue_on_error and failures and not evaluated:
            return OpportunityDiscoveryResult(
                evaluated=tuple(),
                failures=tuple(failures),
            )
        raise OpportunityDiscoveryError("all discovered candidates must share one chain and pinned block")

    return OpportunityDiscoveryResult(
        evaluated=tuple(evaluated),
        failures=tuple(failures),
    )
