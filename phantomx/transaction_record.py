"""Immutable transaction record binding for Phase 19."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re

from .execution import Authorization, ExecutionIntent, ExecutionState, TransactionEnvelope
from .hashing import keccak256_hex
from .nonce_binding import BoundNonce

_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class TransactionRecord:
    intent_hash: str
    authorization_hash: str
    reservation_id: str
    chain_id: int
    sender: str
    executor: str
    nonce: int
    calldata_hash: str
    gas_limit: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    tx_hash: str
    state: ExecutionState = ExecutionState.SIGNED
    replacement_of: str | None = None

    def canonical(self) -> dict[str, object]:
        return {
            "intent_hash": self.intent_hash.lower(),
            "authorization_hash": self.authorization_hash.lower(),
            "reservation_id": self.reservation_id,
            "chain_id": self.chain_id,
            "sender": self.sender.lower(),
            "executor": self.executor.lower(),
            "nonce": self.nonce,
            "calldata_hash": self.calldata_hash.lower(),
            "gas_limit": self.gas_limit,
            "max_fee_per_gas": self.max_fee_per_gas,
            "max_priority_fee_per_gas": self.max_priority_fee_per_gas,
            "tx_hash": self.tx_hash.lower(),
            "state": self.state.value,
            "replacement_of": self.replacement_of.lower() if self.replacement_of else None,
        }

    def record_hash(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode()
        return keccak256_hex(payload)

    def with_state(self, state: ExecutionState) -> "TransactionRecord":
        return replace(self, state=state)

    def validate_binding(
        self,
        intent: ExecutionIntent,
        authorization: Authorization,
        envelope: TransactionEnvelope,
        bound_nonce: BoundNonce,
    ) -> None:
        if self.intent_hash.lower() != intent.intent_hash().lower():
            raise ValueError("transaction record intent hash mismatch")
        if self.authorization_hash.lower() != _authorization_hash(authorization).lower():
            raise ValueError("transaction record authorization hash mismatch")
        if bound_nonce.reservation_id != self.reservation_id:
            raise ValueError("transaction record reservation mismatch")
        if self.chain_id != intent.chain_id or self.chain_id != envelope.chain_id:
            raise ValueError("transaction record chain mismatch")
        if self.sender.lower() != intent.sender.lower() or self.sender.lower() != envelope.sender.lower():
            raise ValueError("transaction record sender mismatch")
        if self.executor.lower() != intent.executor.lower() or self.executor.lower() != envelope.executor.lower():
            raise ValueError("transaction record executor mismatch")
        if self.nonce != intent.nonce or self.nonce != envelope.nonce or self.nonce != bound_nonce.nonce:
            raise ValueError("transaction record nonce mismatch")
        if self.calldata_hash.lower() != envelope.calldata_hash.lower() or self.calldata_hash.lower() != intent.calldata_hash.lower():
            raise ValueError("transaction record calldata mismatch")
        if self.gas_limit != envelope.gas_limit or self.max_fee_per_gas != envelope.max_fee_per_gas or self.max_priority_fee_per_gas != envelope.max_priority_fee_per_gas:
            raise ValueError("transaction record gas envelope mismatch")
        if not _TX_HASH.fullmatch(self.tx_hash):
            raise ValueError("invalid transaction hash")


def _authorization_hash(authorization: Authorization) -> str:
    payload = {
        "intent_hash": authorization.intent_hash.lower(),
        "calldata_hash": authorization.calldata_hash.lower(),
        "economic_proof_hash": authorization.economic_proof_hash.lower(),
        "simulation_proof_hash": authorization.simulation_proof_hash.lower(),
        "chain_id": authorization.chain_id,
        "executor": authorization.executor.lower(),
        "sender": authorization.sender.lower(),
        "nonce": authorization.nonce,
        "deadline": authorization.deadline,
        "gas_limit": authorization.gas_limit,
        "max_fee_per_gas": authorization.max_fee_per_gas,
        "max_priority_fee_per_gas": authorization.max_priority_fee_per_gas,
    }
    return keccak256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def build_signed_record(
    intent: ExecutionIntent,
    authorization: Authorization,
    envelope: TransactionEnvelope,
    bound_nonce: BoundNonce,
    tx_hash: str,
    *,
    now: int = 0,
) -> TransactionRecord:
    """Construct a signed-state record only after exact binding and deadline validation."""
    if not authorization.matches_envelope(envelope, now=now, intent=intent):
        raise ValueError("authorization and transaction envelope do not match or authorization expired")
    if bound_nonce.sender.lower() != envelope.sender.lower() or bound_nonce.nonce != envelope.nonce:
        raise ValueError("nonce reservation does not bind transaction envelope")
    if bound_nonce.intent_hash.lower() != intent.intent_hash().lower():
        raise ValueError("bound nonce does not bind execution intent")
    if not _TX_HASH.fullmatch(tx_hash):
        raise ValueError("invalid transaction hash")
    record = TransactionRecord(
        intent_hash=intent.intent_hash(),
        authorization_hash=_authorization_hash(authorization),
        reservation_id=bound_nonce.reservation_id,
        chain_id=envelope.chain_id,
        sender=envelope.sender,
        executor=envelope.executor,
        nonce=envelope.nonce,
        calldata_hash=envelope.calldata_hash,
        gas_limit=envelope.gas_limit,
        max_fee_per_gas=envelope.max_fee_per_gas,
        max_priority_fee_per_gas=envelope.max_priority_fee_per_gas,
        tx_hash=tx_hash,
    )
    record.validate_binding(intent, authorization, envelope, bound_nonce)
    return record
