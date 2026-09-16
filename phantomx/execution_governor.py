"""Fail-closed policy governor immediately before the signer boundary.

The governor consumes only an already-passed EVM preflight artifact and the
immutable execution assembly. It applies explicit operator policy limits, but
never signs, submits, broadcasts, or moves live capital.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .evm_preflight import EVMPreflightResult
from .execution_assembly import ExecutionAssembly
from .hashing import keccak256_hex


class ExecutionGovernorError(ValueError):
    """Raised when an execution candidate violates governor policy."""


def _decimal(value: Decimal | int | str, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ExecutionGovernorError(f"{field} is not a valid decimal") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ExecutionGovernorError(f"{field} must be a finite non-negative decimal")
    return parsed


def _address(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ExecutionGovernorError(f"{field} must be a 20-byte 0x address")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ExecutionGovernorError(f"{field} is not valid hexadecimal") from exc
    if value[2:] == "00" * 20:
        raise ExecutionGovernorError(f"{field} must be non-zero")
    return value.lower()


@dataclass(frozen=True)
class GovernorPolicy:
    """Explicit upper bounds and identity constraints for one execution lane."""

    enabled: bool = True
    expected_chain_id: int = 137
    expected_executor: str = ""
    expected_sender: str = ""
    max_loan_amount: int = 0
    max_gas_limit: int = 0
    max_fee_per_gas: int = 0
    max_priority_fee_per_gas: int = 0
    max_deadline_seconds: int = 30
    minimum_net_profit_usd: Decimal | int | str = Decimal("0.20")

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ExecutionGovernorError("enabled must be boolean")
        if not isinstance(self.expected_chain_id, int) or isinstance(self.expected_chain_id, bool) or self.expected_chain_id <= 0:
            raise ExecutionGovernorError("expected chain id must be positive")
        object.__setattr__(self, "expected_executor", _address(self.expected_executor, "expected executor"))
        object.__setattr__(self, "expected_sender", _address(self.expected_sender, "expected sender"))
        for name in ("max_loan_amount", "max_gas_limit", "max_fee_per_gas", "max_priority_fee_per_gas", "max_deadline_seconds"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ExecutionGovernorError(f"{name} must be a positive integer")
        if self.max_fee_per_gas < self.max_priority_fee_per_gas:
            raise ExecutionGovernorError("max fee policy must cover max priority fee policy")
        minimum = _decimal(self.minimum_net_profit_usd, "minimum_net_profit_usd")
        if minimum < Decimal("0.20"):
            raise ExecutionGovernorError("minimum net profit policy cannot be below the project floor")
        object.__setattr__(self, "minimum_net_profit_usd", minimum)

    def canonical(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "expected_chain_id": self.expected_chain_id,
            "expected_executor": self.expected_executor,
            "expected_sender": self.expected_sender,
            "max_loan_amount": self.max_loan_amount,
            "max_gas_limit": self.max_gas_limit,
            "max_fee_per_gas": self.max_fee_per_gas,
            "max_priority_fee_per_gas": self.max_priority_fee_per_gas,
            "max_deadline_seconds": self.max_deadline_seconds,
            "minimum_net_profit_usd": str(self.minimum_net_profit_usd),
        }

    def policy_hash(self) -> str:
        encoded = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return keccak256_hex(encoded)


@dataclass(frozen=True)
class GovernorDecision:
    """Immutable evidence that one exact preflight artifact passed governor policy."""

    intent_hash: str
    simulation_proof_hash: str
    economic_proof_hash: str
    calldata_hash: str
    policy_hash: str
    block_number: int
    approved: bool = True

    def __post_init__(self) -> None:
        if not self.approved:
            raise ExecutionGovernorError("a governor decision cannot claim approval=false")
        for name in ("intent_hash", "simulation_proof_hash", "economic_proof_hash", "calldata_hash", "policy_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
                raise ExecutionGovernorError(f"{name} must be a 32-byte 0x hash")
            try:
                int(value[2:], 16)
            except ValueError as exc:
                raise ExecutionGovernorError(f"{name} must be hexadecimal") from exc
            object.__setattr__(self, name, value.lower())
        if not isinstance(self.block_number, int) or isinstance(self.block_number, bool) or self.block_number < 0:
            raise ExecutionGovernorError("block_number must be a non-negative integer")


def govern_execution(
    *,
    preflight: EVMPreflightResult,
    assembly: ExecutionAssembly,
    policy: GovernorPolicy,
    now: int,
) -> GovernorDecision:
    """Approve only an exact preflight artifact that remains within policy."""
    if not isinstance(preflight, EVMPreflightResult):
        raise ExecutionGovernorError("preflight result is required")
    if not isinstance(assembly, ExecutionAssembly):
        raise ExecutionGovernorError("execution assembly is required")
    if not isinstance(policy, GovernorPolicy):
        raise ExecutionGovernorError("governor policy is required")
    if not isinstance(now, int) or isinstance(now, bool) or now < 0:
        raise ExecutionGovernorError("current time must be a non-negative integer")
    if not policy.enabled:
        raise ExecutionGovernorError("governor kill switch is active")
    if not preflight.passed:
        raise ExecutionGovernorError("EVM preflight has not passed")

    intent = assembly.intent
    envelope = assembly.envelope
    proof = assembly.economic_proof

    if preflight.intent_hash.lower() != assembly.intent_hash.lower():
        raise ExecutionGovernorError("preflight intent hash does not match assembly")
    if preflight.simulation_proof_hash.lower() != assembly.simulation_proof_hash.lower():
        raise ExecutionGovernorError("preflight simulation proof does not match assembly")
    if preflight.economic_proof_hash.lower() != proof.proof_hash.lower():
        raise ExecutionGovernorError("preflight economic proof does not match assembly")
    if preflight.calldata_hash.lower() != envelope.calldata_hash.lower():
        raise ExecutionGovernorError("preflight calldata hash does not match envelope")
    if preflight.chain_id != policy.expected_chain_id or intent.chain_id != policy.expected_chain_id:
        raise ExecutionGovernorError("governor chain policy mismatch")
    if intent.executor.lower() != policy.expected_executor:
        raise ExecutionGovernorError("governor executor identity mismatch")
    if intent.sender.lower() != policy.expected_sender:
        raise ExecutionGovernorError("governor sender identity mismatch")
    if intent.loan_amount <= 0 or intent.loan_amount > policy.max_loan_amount:
        raise ExecutionGovernorError("loan amount exceeds governor policy")
    if envelope.gas_limit <= 0 or envelope.gas_limit > policy.max_gas_limit:
        raise ExecutionGovernorError("gas limit exceeds governor policy")
    if envelope.max_fee_per_gas < envelope.max_priority_fee_per_gas:
        raise ExecutionGovernorError("transaction fee bounds are invalid")
    if envelope.max_fee_per_gas > policy.max_fee_per_gas:
        raise ExecutionGovernorError("max fee per gas exceeds governor policy")
    if envelope.max_priority_fee_per_gas > policy.max_priority_fee_per_gas:
        raise ExecutionGovernorError("priority fee exceeds governor policy")
    if intent.deadline < now:
        raise ExecutionGovernorError("execution deadline has expired")
    if intent.deadline - now > policy.max_deadline_seconds:
        raise ExecutionGovernorError("execution deadline is too far from current time")
    if proof.minimum_net_profit_usd < policy.minimum_net_profit_usd:
        raise ExecutionGovernorError("economic proof minimum profit is below governor policy")
    if proof.worst_case_net_profit_usd <= policy.minimum_net_profit_usd:
        raise ExecutionGovernorError("worst-case economics do not satisfy governor profit floor")

    return GovernorDecision(
        intent_hash=preflight.intent_hash,
        simulation_proof_hash=preflight.simulation_proof_hash,
        economic_proof_hash=preflight.economic_proof_hash,
        calldata_hash=preflight.calldata_hash,
        policy_hash=policy.policy_hash(),
        block_number=preflight.block_number,
    )


__all__ = ["ExecutionGovernorError", "GovernorPolicy", "GovernorDecision", "govern_execution"]
