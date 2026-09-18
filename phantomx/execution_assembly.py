"""Assembly bridge from proven route/economics evidence to an exact executor call.

This module is deliberately network-free. It does not quote, value, sign, or
submit. It only assembles already-proven evidence into the exact immutable
objects consumed by the preflight/governor/signer boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass

from .economic_proof import EconomicProof
from .execution import Authorization, ExecutionIntent
from .evm_preflight import simulation_hash
from .executor_calldata import BoundExecutorCall, build_executor_transaction
from .route_simulator import RouteSimulation


class ExecutionAssemblyError(ValueError):
    """Raised when execution-critical evidence cannot be assembled safely."""


@dataclass(frozen=True)
class ExecutionAssembly:
    """Complete deterministic hand-off from route/economics to authorization."""

    simulation: RouteSimulation
    economic_proof: EconomicProof
    bound_call: BoundExecutorCall
    authorization: Authorization

    @property
    def intent(self) -> ExecutionIntent:
        return self.bound_call.bound_intent

    @property
    def envelope(self):
        return self.bound_call.envelope

    @property
    def intent_hash(self) -> str:
        return self.intent.intent_hash()

    @property
    def simulation_proof_hash(self) -> str:
        return simulation_hash(self.simulation)


def _same_hash_sequence(actual: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    return tuple(item.lower() for item in actual) == tuple(item.lower() for item in expected)


def assemble_execution(
    *,
    simulation: RouteSimulation,
    economic_proof: EconomicProof,
    executor: str,
    sender: str,
    nonce: int,
    deadline: int,
    first_on_quickswap: bool,
    quickswap_venue_kind: int,
    amount_out_min_first: int,
    amount_out_min_second: int,
    minimum_surplus: int,
    aave_pool: str,
    quickswap_v2_router: str,
    quickswap_v3_router: str,
    uniswap_v3_router: str,
    gas_limit: int,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
) -> ExecutionAssembly:
    """Assemble one exact execution package from already-proven evidence.

    The route and economic proof are treated as authoritative inputs. The
    assembly rejects any mismatch before constructing calldata. The final
    intent hash is produced only after calldata_hash exists, while calldata
    carries the cycle-free execution commitment hash.
    """
    if simulation.chain_id != 137:
        raise ExecutionAssemblyError("Phase-19 execution is Polygon-only")
    if not economic_proof.economically_valid:
        raise ExecutionAssemblyError("economic proof is not above the strict floor")
    if economic_proof.route_hash.lower() != simulation.route_hash.lower():
        raise ExecutionAssemblyError("economic proof route does not match simulation")

    expected_quotes = tuple(leg.quote_hash for leg in simulation.legs)
    if not _same_hash_sequence(economic_proof.quote_hashes, expected_quotes):
        raise ExecutionAssemblyError("economic proof quotes do not match simulation")

    if not simulation_hash(simulation).startswith("0x"):
        raise ExecutionAssemblyError("simulation hash construction failed")
    if simulation.initial_amount <= 0:
        raise ExecutionAssemblyError("simulation initial amount must be positive")
    if deadline <= 0:
        raise ExecutionAssemblyError("deadline must be positive")
    if nonce < 0:
        raise ExecutionAssemblyError("nonce cannot be negative")
    if minimum_surplus <= 0:
        raise ExecutionAssemblyError("minimum surplus must be positive")

    first = simulation.legs[0]
    second = simulation.legs[1]
    if first_on_quickswap:
        if "quickswap" not in first.dex.lower() or "uniswap" not in second.dex.lower():
            raise ExecutionAssemblyError("route venue order does not match QuickSwap→Uniswap")
        uniswap_fee = second.fee_raw
    else:
        if "uniswap" not in first.dex.lower() or "quickswap" not in second.dex.lower():
            raise ExecutionAssemblyError("route venue order does not match Uniswap→QuickSwap")
        uniswap_fee = first.fee_raw

    if uniswap_fee <= 0 or uniswap_fee > 0xFFFFFF:
        raise ExecutionAssemblyError("route does not contain a valid Uniswap uint24 fee")
    if amount_out_min_first <= 0 or amount_out_min_second <= 0:
        raise ExecutionAssemblyError("per-leg minimum outputs must be positive")
    if amount_out_min_first > first.amount_out:
        raise ExecutionAssemblyError("first-leg minimum exceeds the proven quote")
    if amount_out_min_second > second.amount_out:
        raise ExecutionAssemblyError("second-leg minimum exceeds the proven quote")

    simulation_digest = simulation_hash(simulation)
    seed_intent = ExecutionIntent(
        chain_id=simulation.chain_id,
        executor=executor,
        sender=sender,
        loan_asset=first.token_in,
        loan_amount=simulation.initial_amount,
        route_hash=simulation.route_hash,
        calldata_hash="0x" + "00" * 32,
        economic_proof_hash=economic_proof.proof_hash,
        simulation_proof_hash=simulation_digest,
        nonce=nonce,
        deadline=deadline,
        minimum_net_profit_usd=str(economic_proof.minimum_net_profit_usd),
        minimum_surplus_token_amount=minimum_surplus,
    )

    bound_call = build_executor_transaction(
        seed_intent,
        token_mid=first.token_out,
        first_on_quickswap=first_on_quickswap,
        quickswap_venue_kind=quickswap_venue_kind,
        uniswap_fee=uniswap_fee,
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

    intent = bound_call.bound_intent
    envelope = bound_call.envelope
    if envelope.calldata_hash.lower() != intent.calldata_hash.lower():
        raise ExecutionAssemblyError("calldata hash is not bound into final intent")
    if intent.route_hash.lower() != simulation.route_hash.lower():
        raise ExecutionAssemblyError("final intent route does not match simulation")
    if intent.economic_proof_hash.lower() != economic_proof.proof_hash.lower():
        raise ExecutionAssemblyError("final intent economic proof does not match proof")
    if intent.simulation_proof_hash.lower() != simulation_digest.lower():
        raise ExecutionAssemblyError("final intent simulation proof does not match simulation")
    if intent.loan_asset.lower() != first.token_in.lower() or intent.loan_amount != simulation.initial_amount:
        raise ExecutionAssemblyError("final intent loan binding does not match route")
    if intent.minimum_surplus_token_amount != minimum_surplus:
        raise ExecutionAssemblyError("final intent minimum surplus does not match executor settlement floor")

    authorization = Authorization(
        intent_hash=intent.intent_hash(),
        calldata_hash=envelope.calldata_hash,
        economic_proof_hash=economic_proof.proof_hash,
        simulation_proof_hash=simulation_digest,
        chain_id=envelope.chain_id,
        executor=envelope.executor,
        sender=envelope.sender,
        nonce=envelope.nonce,
        deadline=intent.deadline,
        gas_limit=envelope.gas_limit,
        max_fee_per_gas=envelope.max_fee_per_gas,
        max_priority_fee_per_gas=envelope.max_priority_fee_per_gas,
    )
    if not authorization.matches_envelope(envelope, 0, intent):
        raise ExecutionAssemblyError("constructed authorization does not match exact envelope")

    return ExecutionAssembly(
        simulation=simulation,
        economic_proof=economic_proof,
        bound_call=bound_call,
        authorization=authorization,
    )
