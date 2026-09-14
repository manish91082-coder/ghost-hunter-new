"""Execution integrity primitives."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any

from .hashing import keccak256_hex


class ExecutionState(str, Enum):
    CREATED = "CREATED"
    SIMULATED = "SIMULATED"
    AUTHORIZED = "AUTHORIZED"
    NONCE_RESERVED = "NONCE_RESERVED"
    BUILT = "BUILT"
    VERIFIED = "VERIFIED"
    SIGNED = "SIGNED"
    PRIVATE_SUBMITTED = "PRIVATE_SUBMITTED"
    PENDING = "PENDING"
    INCLUDED = "INCLUDED"
    RECONCILED = "RECONCILED"
    PROFIT_CONFIRMED = "PROFIT_CONFIRMED"
    PROFIT_FAILED = "PROFIT_FAILED"


@dataclass(frozen=True)
class ExecutionIntent:
    chain_id: int
    executor: str
    sender: str
    loan_asset: str
    loan_amount: int
    route_hash: str
    calldata_hash: str
    economic_proof_hash: str
    simulation_proof_hash: str
    nonce: int
    deadline: int
    minimum_net_profit_usd: str = "0.20"

    def canonical(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "executor": self.executor.lower(),
            "sender": self.sender.lower(),
            "loan_asset": self.loan_asset.lower(),
            "loan_amount": self.loan_amount,
            "route_hash": self.route_hash.lower(),
            "calldata_hash": self.calldata_hash.lower(),
            "economic_proof_hash": self.economic_proof_hash.lower(),
            "simulation_proof_hash": self.simulation_proof_hash.lower(),
            "nonce": self.nonce,
            "deadline": self.deadline,
            "minimum_net_profit_usd": self.minimum_net_profit_usd,
        }

    def commitment_canonical(self) -> dict[str, Any]:
        """Canonical intent commitment excluding calldata_hash to avoid a hash cycle."""
        return {
            "chain_id": self.chain_id,
            "executor": self.executor.lower(),
            "sender": self.sender.lower(),
            "loan_asset": self.loan_asset.lower(),
            "loan_amount": self.loan_amount,
            "route_hash": self.route_hash.lower(),
            "economic_proof_hash": self.economic_proof_hash.lower(),
            "simulation_proof_hash": self.simulation_proof_hash.lower(),
            "nonce": self.nonce,
            "deadline": self.deadline,
            "minimum_net_profit_usd": self.minimum_net_profit_usd,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def commitment_bytes(self) -> bytes:
        return json.dumps(self.commitment_canonical(), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def intent_hash(self) -> str:
        return keccak256_hex(self.canonical_bytes())

    def execution_commitment_hash(self) -> str:
        """Stable on-chain execution identity that excludes calldata_hash."""
        return keccak256_hex(self.commitment_bytes())

    def test_only_sha256_fingerprint(self) -> str:
        return "0x" + hashlib.sha256(self.canonical_bytes()).hexdigest()

    def with_field(self, **changes: Any) -> "ExecutionIntent":
        return replace(self, **changes)


@dataclass(frozen=True)
class TransactionEnvelope:
    chain_id: int
    sender: str
    executor: str
    nonce: int
    calldata: bytes
    gas_limit: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int

    @property
    def calldata_hash(self) -> str:
        return keccak256_hex(self.calldata)

    @property
    def test_only_sha256_calldata_fingerprint(self) -> str:
        return "0x" + hashlib.sha256(self.calldata).hexdigest()

    def canonical(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "sender": self.sender.lower(),
            "executor": self.executor.lower(),
            "nonce": self.nonce,
            "calldata_hash": self.calldata_hash,
            "gas_limit": self.gas_limit,
            "max_fee_per_gas": self.max_fee_per_gas,
            "max_priority_fee_per_gas": self.max_priority_fee_per_gas,
        }


@dataclass(frozen=True)
class Authorization:
    """Immutable authorization binding intent and transaction envelope fields."""

    intent_hash: str
    calldata_hash: str
    economic_proof_hash: str
    simulation_proof_hash: str
    chain_id: int
    executor: str
    sender: str
    nonce: int
    deadline: int
    gas_limit: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int

    def matches(self, intent: ExecutionIntent, now: int) -> bool:
        return (
            now <= self.deadline
            and self.intent_hash.lower() == intent.intent_hash().lower()
            and self.calldata_hash.lower() == intent.calldata_hash.lower()
            and self.economic_proof_hash.lower() == intent.economic_proof_hash.lower()
            and self.simulation_proof_hash.lower() == intent.simulation_proof_hash.lower()
            and self.chain_id == intent.chain_id
            and self.executor.lower() == intent.executor.lower()
            and self.sender.lower() == intent.sender.lower()
            and self.nonce == intent.nonce
            and self.gas_limit > 0
            and self.max_fee_per_gas >= self.max_priority_fee_per_gas >= 0
        )

    def matches_envelope(self, envelope: TransactionEnvelope, now: int, intent: ExecutionIntent) -> bool:
        """Return true only when the transaction envelope is fully authorization-bound."""
        return (
            self.matches(intent, now)
            and envelope.chain_id == self.chain_id
            and envelope.sender.lower() == self.sender.lower()
            and envelope.executor.lower() == self.executor.lower()
            and envelope.nonce == self.nonce
            and envelope.calldata_hash.lower() == self.calldata_hash.lower()
            and envelope.gas_limit == self.gas_limit
            and envelope.max_fee_per_gas == self.max_fee_per_gas
            and envelope.max_priority_fee_per_gas == self.max_priority_fee_per_gas
        )
