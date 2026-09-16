"""Canonical MVP pipeline for one evidence-backed Polygon arbitrage candidate.

This module is the missing orchestration bridge between the existing exact
quote/route/economic primitives and the execution assembly boundary. It is
read-only and pre-execution: it does not sign, submit, broadcast, or touch live
capital.

The pipeline accepts externally supplied USD valuation and cost evidence. It
never manufactures a price, gas cost, relay cost, or profit number.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol, Sequence

from .cross_venue_route import build_quickswap_to_uniswap_route
from .economics import CostBreakdown
from .economic_proof import EconomicProof, build_economic_proof
from .execution_assembly import ExecutionAssembly, assemble_execution
from .quickswap_v2 import QuickSwapV2ExactQuoter
from .route_simulator import RouteSimulation
from .uniswap_v3 import UniswapV3ExactQuoter


class MvpPipelineError(ValueError):
    """Raised when an MVP candidate cannot cross the deterministic pipeline."""


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform a read-only JSON-RPC request."""


@dataclass(frozen=True)
class UsdValuation:
    """External valuation evidence for one exact route snapshot."""

    valuation_hash: str
    final_settlement_usd: Decimal
    loan_principal_usd: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.valuation_hash, str) or not self.valuation_hash.startswith("0x"):
            raise MvpPipelineError("valuation_hash must be a 0x-prefixed digest")
        if len(self.valuation_hash) != 66:
            raise MvpPipelineError("valuation_hash must be a 32-byte digest")
        try:
            int(self.valuation_hash[2:], 16)
        except ValueError as exc:
            raise MvpPipelineError("valuation_hash must be hexadecimal") from exc
        for field in ("final_settlement_usd", "loan_principal_usd"):
            value = Decimal(getattr(self, field))
            if not value.is_finite() or value < 0:
                raise MvpPipelineError(f"{field} must be finite and non-negative")
            object.__setattr__(self, field, value)


@dataclass(frozen=True)
class MvpPipelineRequest:
    """All non-secret inputs required to assemble a Polygon MVP candidate."""

    amount_in: int
    token_a: str
    token_b: str
    uniswap_fee: int
    aave_pool: str
    quickswap_router: str
    uniswap_v3_router: str
    executor: str
    sender: str
    nonce: int
    deadline: int
    amount_out_min_first: int
    amount_out_min_second: int
    minimum_surplus: int
    gas_limit: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    max_gas_usd: Decimal
    max_relay_usd: Decimal
    valuation: UsdValuation
    costs: CostBreakdown


@dataclass(frozen=True)
class MvpCandidate:
    """Proven candidate plus the exact pre-execution assembly artifact."""

    simulation: RouteSimulation
    economic_proof: EconomicProof
    assembly: ExecutionAssembly

    @property
    def route_hash(self) -> str:
        return self.simulation.route_hash

    @property
    def intent_hash(self) -> str:
        return self.assembly.intent_hash

    @property
    def economically_valid(self) -> bool:
        return self.economic_proof.economically_valid


def build_mvp_candidate(
    rpc: RpcTransport,
    quickswap: QuickSwapV2ExactQuoter,
    uniswap: UniswapV3ExactQuoter,
    request: MvpPipelineRequest,
) -> MvpCandidate:
    """Run the canonical MVP path through route, economics, and assembly.

    The function intentionally stops before signer/submission. Every value that
    can affect economics or execution must be supplied explicitly.
    """
    if request.amount_in <= 0:
        raise MvpPipelineError("amount_in must be positive")
    if request.nonce < 0:
        raise MvpPipelineError("nonce cannot be negative")
    if request.deadline <= 0:
        raise MvpPipelineError("deadline must be positive")
    if request.gas_limit <= 0:
        raise MvpPipelineError("gas_limit must be positive")
    if request.max_fee_per_gas < request.max_priority_fee_per_gas >= 0:
        pass
    elif request.max_priority_fee_per_gas < 0 or request.max_fee_per_gas < request.max_priority_fee_per_gas:
        raise MvpPipelineError("invalid EIP-1559 fee bounds")
    if request.amount_out_min_first <= 0 or request.amount_out_min_second <= 0:
        raise MvpPipelineError("per-leg minimum outputs must be positive")

    simulation = build_quickswap_to_uniswap_route(
        rpc,
        quickswap,
        uniswap,
        amount_in=request.amount_in,
        token_a=request.token_a,
        token_b=request.token_b,
        uniswap_fee=request.uniswap_fee,
        block=None,
    )

    economic_proof = build_economic_proof(
        route_hash=simulation.route_hash,
        quote_hashes=(leg.quote_hash for leg in simulation.legs),
        valuation_hash=request.valuation.valuation_hash,
        final_settlement_usd=request.valuation.final_settlement_usd,
        loan_principal_usd=request.valuation.loan_principal_usd,
        costs=request.costs,
        max_gas_usd=request.max_gas_usd,
        max_relay_usd=request.max_relay_usd,
    )

    assembly = assemble_execution(
        simulation=simulation,
        economic_proof=economic_proof,
        executor=request.executor,
        sender=request.sender,
        nonce=request.nonce,
        deadline=request.deadline,
        first_on_quickswap=True,
        amount_out_min_first=request.amount_out_min_first,
        amount_out_min_second=request.amount_out_min_second,
        minimum_surplus=request.minimum_surplus,
        aave_pool=request.aave_pool,
        quickswap_router=request.quickswap_router,
        uniswap_v3_router=request.uniswap_v3_router,
        gas_limit=request.gas_limit,
        max_fee_per_gas=request.max_fee_per_gas,
        max_priority_fee_per_gas=request.max_priority_fee_per_gas,
    )

    if assembly.intent_hash == "0x" + "00" * 32:
        raise MvpPipelineError("intent hash cannot be empty")
    return MvpCandidate(simulation=simulation, economic_proof=economic_proof, assembly=assembly)
