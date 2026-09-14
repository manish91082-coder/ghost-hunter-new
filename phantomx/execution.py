"""Execution integrity primitives.

Production-facing hash methods use Ethereum Keccak-256 through
``phantomx.hashing`` and fail closed when no compatible backend exists.
The legacy SHA-256 fingerprint remains available only as an explicitly named
TEST-ONLY helper so old dependency-free tests cannot accidentally become a
production authorization primitive.
"""

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
            "nonce": self.nonce,
            "deadline": self.deadline,
            "minimum_net_profit_usd": self.minimum_net_profit_usd,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def intent_hash(self) -> str:
        """Canonical Ethereum Keccak-256 intent digest."""
        return keccak256_hex(self.canonical_bytes())

    def test_only_sha256_fingerprint(self) -> str:
        """Legacy dependency-free fingerprint; never use for authorization."""
        return "0x" + hashlib.sha256(self.canonical_bytes()).hexdigest()

    def with_field(self, **changes: Any) -> "ExecutionIntent":
        return replace(self, **changes)


@dataclass(frozen=True)
class Authorization:
    intent_hash: str
    calldata_hash: str
    chain_id: int
    executor: str
    sender: str
    nonce: int
    deadline: int

    def matches(self, intent: ExecutionIntent, now: int) -> bool:
        return (
            now <= self.deadline
            and self.intent_hash.lower() == intent.intent_hash().lower()
            and self.calldata_hash.lower() == intent.calldata_hash.lower()
            and self.chain_id == intent.chain_id
            and self.executor.lower() == intent.executor.lower()
            and self.sender.lower() == intent.sender.lower()
            and self.nonce == intent.nonce
        )


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
