"""Dependency-free execution integrity primitives for Phase 19 tests."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any


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

    def intent_hash(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        return "0x" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def with_field(self, **changes: Any) -> "ExecutionIntent":
        """Testing helper: mutation creates a distinct intent/hash."""
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
            and self.intent_hash == intent.intent_hash()
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
