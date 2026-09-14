"""Fail-closed signer boundary for Phase 19.

The signer accepts only a Governor-approved transaction whose exact intent,
authorization, and envelope identities still match. It never talks to an RPC
or broadcaster. A real private-key implementation can be attached later
without changing the authorization contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .execution import Authorization, ExecutionIntent, TransactionEnvelope
from .governor import GovernorDecision
from .hashing import keccak256_hex


class SignerError(ValueError):
    """Raised when a transaction is unsafe or impossible to sign."""


class TransactionSigner(Protocol):
    def sign(self, envelope: TransactionEnvelope) -> bytes:
        """Return the serialized signed transaction bytes."""


@dataclass(frozen=True)
class SignedTransaction:
    """Immutable signed artifact bound to the exact governed envelope."""

    intent_hash: str
    governor_decision_hash: str
    transaction_hash: str
    raw_transaction: bytes

    def __post_init__(self) -> None:
        for name in ("intent_hash", "governor_decision_hash", "transaction_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
                raise SignerError(f"{name} must be a 32-byte 0x hash")
        if not isinstance(self.raw_transaction, bytes) or not self.raw_transaction:
            raise SignerError("signed transaction bytes are required")
        expected = keccak256_hex(self.raw_transaction)
        if self.transaction_hash.lower() != expected:
            raise SignerError("signed transaction hash does not match raw transaction")


def sign_governed_transaction(
    *,
    signer: TransactionSigner,
    governor: GovernorDecision,
    intent: ExecutionIntent,
    authorization: Authorization,
    envelope: TransactionEnvelope,
    now: int,
) -> SignedTransaction:
    """Sign only an exact, approved, still-authorized transaction envelope."""
    if not governor.approved:
        raise SignerError("governor did not approve signing")
    if now < 0:
        raise SignerError("current time cannot be negative")
    if intent.deadline < now:
        raise SignerError("execution deadline has expired")
    if governor.intent_hash.lower() != intent.intent_hash().lower():
        raise SignerError("governor intent identity does not match current intent")
    if governor.calldata_hash.lower() != envelope.calldata_hash.lower():
        raise SignerError("governor calldata identity does not match envelope")
    if governor.route_hash.lower() != intent.route_hash.lower():
        raise SignerError("governor route identity does not match intent")
    if governor.economic_proof_hash.lower() != intent.economic_proof_hash.lower():
        raise SignerError("governor economic proof identity does not match intent")
    if governor.simulation_proof_hash.lower() != intent.simulation_proof_hash.lower():
        raise SignerError("governor simulation proof identity does not match intent")
    if not authorization.matches_envelope(envelope, now, intent):
        raise SignerError("authorization does not match exact signing envelope")

    raw = signer.sign(envelope)
    if not isinstance(raw, bytes) or not raw:
        raise SignerError("signer returned empty or invalid transaction bytes")

    return SignedTransaction(
        intent_hash=intent.intent_hash(),
        governor_decision_hash=governor.decision_hash,
        transaction_hash=keccak256_hex(raw),
        raw_transaction=raw,
    )
