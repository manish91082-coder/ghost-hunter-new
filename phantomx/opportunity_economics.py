"""Bind concrete discovered routes to authoritative economic proof inputs.

Discovery supplies exact route evidence. This layer joins each discovered
candidate to externally supplied valuation/cost evidence and constructs the
canonical ``EconomicProof``. It never fetches prices, signs, submits, or
assumes that gross spread is net profit.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable

from .economic_proof import EconomicProof, EconomicProofError, build_economic_proof
from .economics import CostBreakdown, STRICT_MIN_NET_PROFIT_USD
from .opportunity_discovery import OpportunityCandidate


class OpportunityEconomicsError(ValueError):
    """Raised when discovered opportunity economics cannot be proven safely."""


@dataclass(frozen=True)
class OpportunityEconomicEvaluation:
    """One discovered route joined to a deterministic economic proof."""

    candidate: OpportunityCandidate
    proof: EconomicProof

    def __post_init__(self) -> None:
        if self.proof.route_hash.lower() != self.candidate.simulation.route_hash.lower():
            raise OpportunityEconomicsError("economic proof route does not match discovered candidate")
        expected_quotes = tuple(leg.quote_hash.lower() for leg in self.candidate.simulation.legs)
        if tuple(item.lower() for item in self.proof.quote_hashes) != expected_quotes:
            raise OpportunityEconomicsError("economic proof quotes do not match discovered candidate")
        if self.proof.loan_principal_usd < 0:
            raise OpportunityEconomicsError("loan principal valuation cannot be negative")

    @property
    def net_profit_usd(self) -> Decimal:
        return self.proof.worst_case_net_profit_usd

    @property
    def economically_valid(self) -> bool:
        return self.proof.economically_valid


@dataclass(frozen=True)
class OpportunityEconomicsResult:
    """Complete economic evaluation of a discovered frontier."""

    evaluated: tuple[OpportunityEconomicEvaluation, ...]
    best: OpportunityEconomicEvaluation

    @property
    def profitable(self) -> tuple[OpportunityEconomicEvaluation, ...]:
        return tuple(item for item in self.evaluated if item.economically_valid)


def evaluate_discovered_opportunities(
    candidates: Iterable[OpportunityCandidate],
    build_proof_for: Callable[[OpportunityCandidate], EconomicProof],
) -> OpportunityEconomicsResult:
    """Evaluate every discovered candidate without silently skipping failures.

    ``build_proof_for`` is the boundary where real valuation and complete
    transaction-attributable cost evidence must be supplied. Discovery itself
    remains valuation-independent. No partial economic ranking is returned if
    any candidate fails proof construction.
    """
    items = tuple(candidates)
    if not items:
        raise OpportunityEconomicsError("discovered candidate set cannot be empty")

    evaluations: list[OpportunityEconomicEvaluation] = []
    for candidate in items:
        try:
            proof = build_proof_for(candidate)
        except EconomicProofError as exc:
            raise OpportunityEconomicsError("economic proof construction failed") from exc
        except Exception as exc:
            raise OpportunityEconomicsError("economic evaluator failed") from exc
        if not isinstance(proof, EconomicProof):
            raise OpportunityEconomicsError("economic evaluator returned an invalid proof")
        evaluations.append(OpportunityEconomicEvaluation(candidate=candidate, proof=proof))

    chain_block = {
        (item.candidate.simulation.chain_id, item.candidate.simulation.block_number)
        for item in evaluations
    }
    if len(chain_block) != 1:
        raise OpportunityEconomicsError("economic evaluations must share one chain and pinned block")

    valid = [item for item in evaluations if item.economically_valid]
    if not valid:
        raise OpportunityEconomicsError(
            f"no discovered candidate exceeds strict minimum net profit of {STRICT_MIN_NET_PROFIT_USD}"
        )

    best = max(
        valid,
        key=lambda item: (
            item.net_profit_usd,
            -item.candidate.loan_amount,
        ),
    )
    return OpportunityEconomicsResult(evaluated=tuple(evaluations), best=best)


def make_economic_proof_builder(
    *,
    valuation_for: Callable[[OpportunityCandidate], tuple[str, Decimal | int | str, Decimal | int | str]],
    costs_for: Callable[[OpportunityCandidate], CostBreakdown],
    max_gas_usd: Decimal | int | str,
    max_relay_usd: Decimal | int | str,
    minimum_net_profit_usd: Decimal | int | str = STRICT_MIN_NET_PROFIT_USD,
) -> Callable[[OpportunityCandidate], EconomicProof]:
    """Create an explicit-proof builder from caller-supplied valuation/cost evidence.

    ``valuation_for`` returns ``(valuation_hash, final_settlement_usd,
    loan_principal_usd)``. The caller remains responsible for providing genuine,
    evidence-backed valuation data.
    """
    def build(candidate: OpportunityCandidate) -> EconomicProof:
        valuation_hash, final_settlement_usd, loan_principal_usd = valuation_for(candidate)
        costs = costs_for(candidate)
        return build_economic_proof(
            route_hash=candidate.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in candidate.simulation.legs),
            valuation_hash=valuation_hash,
            final_settlement_usd=final_settlement_usd,
            loan_principal_usd=loan_principal_usd,
            costs=costs,
            max_gas_usd=max_gas_usd,
            max_relay_usd=max_relay_usd,
            minimum_net_profit_usd=minimum_net_profit_usd,
        )
    return build
