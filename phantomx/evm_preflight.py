"""Fail-closed EVM preflight gate for the Phase-19 execution spine.

This layer does not sign or submit transactions. It proves that the exact
transaction envelope still matches the already-proven route, simulation,
economic proof, authorization, and executable calldata semantics immediately
before the signer boundary.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal

from .economic_proof import EconomicProof, EconomicProofError
from .execution import Authorization, ExecutionIntent, TransactionEnvelope
from .executor_calldata import ExecutorCalldataError, decode_executor_calldata
from .hashing import keccak256_hex
from .route_simulator import RouteSimulation, RouteSimulationError


class EVMPreflightError(ValueError):
    """Raised when an execution candidate fails the preflight gate."""


def simulation_hash(simulation: RouteSimulation) -> str:
    """Return the canonical hash that an ExecutionIntent binds as simulation proof."""
    payload = {
        "schema_version": simulation.schema_version,
        "chain_id": simulation.chain_id,
        "block_number": simulation.block_number,
        "initial_amount": simulation.initial_amount,
        "final_amount": simulation.final_amount,
        "route_hash": simulation.route_hash.lower(),
        "quote_hashes": [leg.quote_hash.lower() for leg in simulation.legs],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return keccak256_hex(encoded)


@dataclass(frozen=True)
class EVMPreflightResult:
    """Immutable evidence that the exact envelope passed all preflight gates."""

    chain_id: int
    block_number: int
    intent_hash: str
    route_hash: str
    economic_proof_hash: str
    simulation_proof_hash: str
    calldata_hash: str
    passed: bool = True

    def __post_init__(self) -> None:
        if not self.passed:
            raise EVMPreflightError("a preflight result cannot claim a failed pass")
        for name in (
            "intent_hash",
            "route_hash",
            "economic_proof_hash",
            "simulation_proof_hash",
            "calldata_hash",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
                raise EVMPreflightError(f"{name} must be a 32-byte 0x hash")


def _validate_executor_calldata(
    *,
    intent: ExecutionIntent,
    envelope: TransactionEnvelope,
    simulation: RouteSimulation,
    expected_route_commitment: str | None = None,
) -> None:
    """Verify executor calldata semantics, not merely its outer calldata hash."""
    decoded = decode_executor_calldata(envelope.calldata)
    first_leg, second_leg = simulation.legs

    if decoded.asset.lower() != intent.loan_asset.lower():
        raise EVMPreflightError("executor calldata asset does not match intent")
    if decoded.token_mid.lower() != first_leg.token_out.lower():
        raise EVMPreflightError("executor calldata middle token does not match simulation")
    if decoded.amount != simulation.initial_amount:
        raise EVMPreflightError("executor calldata loan amount does not match simulation")
    if decoded.deadline != intent.deadline:
        raise EVMPreflightError("executor calldata deadline does not match intent")
    if decoded.route_hash.lower() != simulation.route_hash.lower():
        raise EVMPreflightError("executor calldata route does not match simulation")
    if decoded.intent_commitment_hash.lower() != intent.execution_commitment_hash().lower():
        raise EVMPreflightError("executor calldata commitment does not match intent")
    if decoded.route_commitment == "0x" + "00" * 32:
        raise EVMPreflightError("executor calldata route commitment is empty")
    if expected_route_commitment is not None:
        if not isinstance(expected_route_commitment, str) or len(expected_route_commitment) != 66 or not expected_route_commitment.startswith("0x"):
            raise EVMPreflightError("expected route commitment must be a 32-byte 0x hash")
        if decoded.route_commitment.lower() != expected_route_commitment.lower():
            raise EVMPreflightError("executor calldata route commitment changed before preflight")
    if intent.minimum_surplus_token_amount <= 0:
        raise EVMPreflightError("intent minimum surplus settlement floor must be positive")
    if decoded.minimum_surplus != intent.minimum_surplus_token_amount:
        raise EVMPreflightError("executor calldata minimum surplus does not match intent")

    first_is_quick = "quickswap" in first_leg.dex.lower()
    first_is_uni = "uniswap" in first_leg.dex.lower()
    second_is_quick = "quickswap" in second_leg.dex.lower()
    second_is_uni = "uniswap" in second_leg.dex.lower()
    if first_is_quick and second_is_uni:
        expected_uni_fee = second_leg.fee_raw
    elif first_is_uni and second_is_quick:
        expected_uni_fee = first_leg.fee_raw
    else:
        raise EVMPreflightError("simulation venue order is not a supported two-venue route")

    if decoded.first_on_quickswap != first_is_quick:
        raise EVMPreflightError("executor calldata direction does not match venue order")
    if decoded.uniswap_fee != expected_uni_fee:
        raise EVMPreflightError("executor calldata Uniswap fee does not match simulation")
    if decoded.amount_out_min_first > first_leg.amount_out:
        raise EVMPreflightError("executor calldata first minimum exceeds proven quote")
    if decoded.amount_out_min_second > second_leg.amount_out:
        raise EVMPreflightError("executor calldata second minimum exceeds proven quote")
    if decoded.minimum_surplus <= 0:
        raise EVMPreflightError("executor calldata minimum surplus must be positive")


def preflight_execution(
    *,
    intent: ExecutionIntent,
    authorization: Authorization,
    envelope: TransactionEnvelope,
    simulation: RouteSimulation,
    economic_proof: EconomicProof,
    now: int,
    expected_chain_id: int = 137,
    expected_route_commitment: str | None = None,
) -> EVMPreflightResult:
    """Fail closed unless every execution-critical identity remains unchanged."""
    try:
        if expected_chain_id <= 0:
            raise EVMPreflightError("expected chain id must be positive")
        if now < 0:
            raise EVMPreflightError("current time cannot be negative")
        if intent.chain_id != expected_chain_id or envelope.chain_id != expected_chain_id:
            raise EVMPreflightError("execution is not on the expected chain")
        if simulation.chain_id != expected_chain_id:
            raise EVMPreflightError("simulation chain does not match expected chain")
        if simulation.block_number < 0:
            raise EVMPreflightError("invalid simulation block")

        if not authorization.matches_envelope(envelope, now, intent):
            raise EVMPreflightError("authorization does not match exact intent and envelope")

        if intent.route_hash.lower() != simulation.route_hash.lower():
            raise EVMPreflightError("intent route binding does not match simulation")
        if intent.simulation_proof_hash.lower() != simulation_hash(simulation).lower():
            raise EVMPreflightError("intent simulation proof does not match simulation")
        if economic_proof.route_hash.lower() != simulation.route_hash.lower():
            raise EVMPreflightError("economic proof route binding does not match simulation")
        expected_quotes = tuple(leg.quote_hash.lower() for leg in simulation.legs)
        if tuple(economic_proof.quote_hashes) != expected_quotes:
            raise EVMPreflightError("economic proof quote binding does not match simulation")
        if economic_proof.proof_hash.lower() != intent.economic_proof_hash.lower():
            raise EVMPreflightError("intent economic proof binding does not match proof")
        if not economic_proof.economically_valid:
            raise EVMPreflightError("economic proof is not above the strict profit floor")
        if intent.minimum_net_profit_usd != str(economic_proof.minimum_net_profit_usd):
            raise EVMPreflightError("intent minimum profit is not bound to economic proof")

        first_leg = simulation.legs[0]
        if intent.loan_amount != simulation.initial_amount:
            raise EVMPreflightError("loan amount does not match exact route input")
        if intent.loan_asset.lower() != first_leg.token_in.lower():
            raise EVMPreflightError("loan asset does not match exact route input asset")
        if simulation.final_amount <= 0:
            raise EVMPreflightError("final route settlement must be positive")

        _validate_executor_calldata(
            intent=intent,
            envelope=envelope,
            simulation=simulation,
            expected_route_commitment=expected_route_commitment,
        )

        if envelope.gas_limit <= 0:
            raise EVMPreflightError("gas limit must be positive")
        if envelope.max_priority_fee_per_gas < 0:
            raise EVMPreflightError("priority fee cannot be negative")
        if envelope.max_fee_per_gas < envelope.max_priority_fee_per_gas:
            raise EVMPreflightError("max fee must cover priority fee")
        if envelope.nonce < 0:
            raise EVMPreflightError("nonce cannot be negative")
        if intent.deadline < now:
            raise EVMPreflightError("execution deadline has expired")

        if Decimal(economic_proof.worst_case_net_profit_usd) <= Decimal(economic_proof.minimum_net_profit_usd):
            raise EVMPreflightError("worst-case economics fail the strict gate")

        return EVMPreflightResult(
            chain_id=intent.chain_id,
            block_number=simulation.block_number,
            intent_hash=intent.intent_hash(),
            route_hash=intent.route_hash,
            economic_proof_hash=intent.economic_proof_hash,
            simulation_proof_hash=intent.simulation_proof_hash,
            calldata_hash=envelope.calldata_hash,
        )
    except (ExecutorCalldataError, EconomicProofError, RouteSimulationError) as exc:
        raise EVMPreflightError(str(exc)) from exc
