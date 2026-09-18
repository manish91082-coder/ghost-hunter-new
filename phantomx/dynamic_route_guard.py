"""Exact route-level dynamic loan ceiling guard.

The guard is market-aware but policy-deterministic:
- Aave liquidity remains the absolute borrowing ceiling upstream.
- Each route size is tested with the actual two-leg quote path.
- A fixed safety policy caps effective route-rate degradation relative to the
  smallest successful probe size.
- Failures are recorded as unavailable sizes, never converted into profit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .route_simulator import RouteSimulation


class DynamicRouteGuardError(ValueError):
    """Raised when the route-domain guard cannot produce safe evidence."""


@dataclass(frozen=True)
class RouteSizeEvidence:
    amount: int
    forward: RouteSimulation | None
    reverse: RouteSimulation | None
    forward_degradation_bps: int | None
    reverse_degradation_bps: int | None
    safe: bool
    failure: str | None = None


@dataclass(frozen=True)
class DynamicRouteCeiling:
    """Maximum safe size over the explicit, supplied domain."""

    max_safe_amount: int
    reference_amount: int
    max_degradation_bps: int
    evaluated: tuple[RouteSizeEvidence, ...]


def _validate_amounts(amounts: tuple[int, ...]) -> None:
    if not amounts:
        raise DynamicRouteGuardError("loan amount domain cannot be empty")
    if tuple(sorted(set(amounts))) != amounts:
        raise DynamicRouteGuardError("loan amount domain must be strictly increasing")
    if any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in amounts):
        raise DynamicRouteGuardError("loan amounts must be positive integers")


def compute_rate_degradation_bps(
    reference: RouteSimulation,
    candidate: RouteSimulation,
) -> int:
    """Measure effective route-rate deterioration without floating point."""
    if reference.chain_id != candidate.chain_id or reference.block_number != candidate.block_number:
        raise DynamicRouteGuardError("reference and candidate must share chain/block")
    if reference.initial_amount <= 0 or candidate.initial_amount <= 0:
        raise DynamicRouteGuardError("route amounts must be positive")

    reference_rate_numer = reference.final_amount
    reference_rate_denom = reference.initial_amount
    candidate_rate_numer = candidate.final_amount
    candidate_rate_denom = candidate.initial_amount

    lhs = reference_rate_numer * candidate_rate_denom
    rhs = candidate_rate_numer * reference_rate_denom
    if rhs >= lhs:
        return 0
    denominator = lhs
    return ((lhs - rhs) * 10_000) // denominator


def evaluate_dynamic_route_domain(
    amounts: tuple[int, ...],
    *,
    evaluate_forward: Callable[[int], RouteSimulation],
    evaluate_reverse: Callable[[int], RouteSimulation],
    max_degradation_bps: int = 100,
) -> DynamicRouteCeiling:
    """Evaluate an explicit route domain and derive its maximum safe size.

    The result is exact over the supplied discrete domain only. It is not a
    claim that an arbitrary continuous amount between supplied candidates is
    equally safe. A route must be available in both directions for a size to be
    considered common-route-safe.
    """
    _validate_amounts(amounts)
    if not isinstance(max_degradation_bps, int) or isinstance(max_degradation_bps, bool):
        raise DynamicRouteGuardError("max_degradation_bps must be an integer")
    if not 0 <= max_degradation_bps <= 10_000:
        raise DynamicRouteGuardError("max_degradation_bps must be between 0 and 10000")

    forward_results: dict[int, RouteSimulation] = {}
    reverse_results: dict[int, RouteSimulation] = {}
    failures: dict[int, str] = {}

    for amount in amounts:
        try:
            forward_results[amount] = evaluate_forward(amount)
        except Exception as exc:
            failures[amount] = f"forward:{type(exc).__name__}"
        try:
            reverse_results[amount] = evaluate_reverse(amount)
        except Exception as exc:
            previous = failures.get(amount)
            suffix = f",reverse:{type(exc).__name__}"
            failures[amount] = (previous + suffix) if previous else suffix

    common = sorted(set(forward_results) & set(reverse_results))
    if not common:
        raise DynamicRouteGuardError("no common executable route size")

    reference_amount = common[0]
    reference_forward = forward_results[reference_amount]
    reference_reverse = reverse_results[reference_amount]

    evaluated: list[RouteSizeEvidence] = []
    safe_amounts: list[int] = []
    for amount in amounts:
        forward = forward_results.get(amount)
        reverse = reverse_results.get(amount)
        if forward is None or reverse is None:
            evaluated.append(RouteSizeEvidence(
                amount=amount,
                forward=forward,
                reverse=reverse,
                forward_degradation_bps=None,
                reverse_degradation_bps=None,
                safe=False,
                failure=failures.get(amount, "route unavailable"),
            ))
            continue

        forward_degradation = compute_rate_degradation_bps(reference_forward, forward)
        reverse_degradation = compute_rate_degradation_bps(reference_reverse, reverse)
        safe = (
            forward_degradation <= max_degradation_bps
            and reverse_degradation <= max_degradation_bps
        )
        if safe:
            safe_amounts.append(amount)
        evaluated.append(RouteSizeEvidence(
            amount=amount,
            forward=forward,
            reverse=reverse,
            forward_degradation_bps=forward_degradation,
            reverse_degradation_bps=reverse_degradation,
            safe=safe,
        ))

    if not safe_amounts:
        raise DynamicRouteGuardError("no route size remains inside the fixed impact policy")

    return DynamicRouteCeiling(
        max_safe_amount=max(safe_amounts),
        reference_amount=reference_amount,
        max_degradation_bps=max_degradation_bps,
        evaluated=tuple(evaluated),
    )


def evaluate_simulation_domain(
    *,
    forward: tuple[RouteSimulation, ...],
    reverse: tuple[RouteSimulation, ...],
    max_degradation_bps: int = 100,
) -> DynamicRouteCeiling:
    """Derive a dynamic route ceiling from already-observed exact simulations.

    This is deliberately a post-processing step. It performs no RPC calls and
    therefore must be used after one complete cross-venue discovery pass.
    """
    if not forward or not reverse:
        raise DynamicRouteGuardError("both route directions require exact observations")
    forward_by_amount = {item.initial_amount: item for item in forward}
    reverse_by_amount = {item.initial_amount: item for item in reverse}
    amounts = tuple(sorted(set(forward_by_amount) | set(reverse_by_amount)))
    _validate_amounts(amounts)
    if not isinstance(max_degradation_bps, int) or isinstance(max_degradation_bps, bool):
        raise DynamicRouteGuardError("max_degradation_bps must be an integer")
    if not 0 <= max_degradation_bps <= 10_000:
        raise DynamicRouteGuardError("max_degradation_bps must be between 0 and 10000")

    common = sorted(set(forward_by_amount) & set(reverse_by_amount))
    if not common:
        raise DynamicRouteGuardError("no common executable route size")
    reference_amount = common[0]
    ref_forward = forward_by_amount[reference_amount]
    ref_reverse = reverse_by_amount[reference_amount]

    evaluated: list[RouteSizeEvidence] = []
    safe_amounts: list[int] = []
    for amount in amounts:
        fwd = forward_by_amount.get(amount)
        rev = reverse_by_amount.get(amount)
        if fwd is None or rev is None:
            evaluated.append(RouteSizeEvidence(
                amount=amount, forward=fwd, reverse=rev,
                forward_degradation_bps=None, reverse_degradation_bps=None,
                safe=False, failure="route direction unavailable",
            ))
            continue
        fd = compute_rate_degradation_bps(ref_forward, fwd)
        rd = compute_rate_degradation_bps(ref_reverse, rev)
        safe = fd <= max_degradation_bps and rd <= max_degradation_bps
        if safe:
            safe_amounts.append(amount)
        evaluated.append(RouteSizeEvidence(
            amount=amount, forward=fwd, reverse=rev,
            forward_degradation_bps=fd, reverse_degradation_bps=rd,
            safe=safe,
        ))

    if not safe_amounts:
        raise DynamicRouteGuardError("no route size remains inside the fixed impact policy")
    return DynamicRouteCeiling(
        max_safe_amount=max(safe_amounts),
        reference_amount=reference_amount,
        max_degradation_bps=max_degradation_bps,
        evaluated=tuple(evaluated),
    )
