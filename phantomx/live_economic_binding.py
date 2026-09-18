"""Deterministic live-candidate economic binding for exact USDC routes.

Exact AMM quote settlement already includes the venue swap fees and price
impact reflected by the quote path. They are therefore NOT subtracted a second
time here. External costs such as Aave flash premium, transaction gas and
relay fees remain explicit costs.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .economic_proof import EconomicProof
from .economics import CostBreakdown, STRICT_MIN_NET_PROFIT_USD
from .gas_cost import GasCostEvidence
from .opportunity_discovery import OpportunityCandidate
from .native_valuation import ConservativeNativeValuation

@dataclass(frozen=True)
class LiveEconomicBinding:
    proof: EconomicProof
    quote_embedded_dex_fees: bool = True
    quote_embedded_price_impact: bool = True

    @property
    def net_profit_usd(self) -> Decimal:
        return self.proof.worst_case_net_profit_usd

    @property
    def economically_valid(self) -> bool:
        return self.proof.economically_valid

def bind_live_economic_proof(
    candidate: OpportunityCandidate,
    *,
    flash_loan_premium_bps: int,
    gas_cost: GasCostEvidence,
    native_valuation: ConservativeNativeValuation,
    max_relay_usd: Decimal | int | str = Decimal("0"),
    other_cost_usd: Decimal | int | str = Decimal("0"),
    minimum_net_profit_usd: Decimal | int | str = STRICT_MIN_NET_PROFIT_USD,
) -> LiveEconomicBinding:
    """Bind exact route settlement and external transaction costs into EconomicProof."""
    if candidate.simulation.chain_id != 137 or candidate.loan_amount <= 0:
        raise ValueError("candidate must be a positive Polygon route")
    if candidate.simulation.block_number != native_valuation.block_number:
        raise ValueError("valuation and route must share the pinned block")
    if gas_cost.gas_observation.block_number != candidate.simulation.block_number:
        raise ValueError("gas evidence and route must share the pinned block")
    if not isinstance(flash_loan_premium_bps, int) or isinstance(flash_loan_premium_bps, bool) or flash_loan_premium_bps < 0 or flash_loan_premium_bps > 10_000:
        raise ValueError("flash_loan_premium_bps is invalid")
    max_relay = Decimal(max_relay_usd)
    other = Decimal(other_cost_usd)
    if max_relay < 0 or other < 0:
        raise ValueError("additional costs cannot be negative")

    principal_usd = Decimal(candidate.loan_amount) / Decimal(10**6)
    settlement_usd = Decimal(candidate.simulation.final_amount) / Decimal(10**6)
    flash_fee_usd = (principal_usd * Decimal(flash_loan_premium_bps)) / Decimal(10_000)

    if gas_cost.valuation_evidence_hash.lower() not in {h.lower() for h in native_valuation.evidence_hashes}:
        raise ValueError("gas valuation evidence is not bound to native price evidence")

    costs = CostBreakdown(
        flash_loan_fee=flash_fee_usd,
        dex_fees=Decimal("0"),
        price_impact=Decimal("0"),
        gas=gas_cost.max_gas_cost_usd,
        relay=max_relay,
        other=other,
    )
    proof = EconomicProof(
        schema_version=1,
        route_hash=candidate.simulation.route_hash,
        quote_hashes=tuple(leg.quote_hash for leg in candidate.simulation.legs),
        valuation_hash=gas_cost.valuation_evidence_hash,
        final_settlement_usd=settlement_usd,
        loan_principal_usd=principal_usd,
        costs=costs,
        max_gas_usd=gas_cost.max_gas_cost_usd,
        max_relay_usd=max_relay,
        minimum_net_profit_usd=minimum_net_profit_usd,
    )
    return LiveEconomicBinding(proof=proof)
