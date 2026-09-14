"""Fail-closed private transaction submission boundary for Phase 19.

This module is deliberately narrower than an RPC client. It accepts only an
immutable signed artifact that is still governed, then submits it exclusively
to an explicitly configured private relay. There is no public-RPC fallback,
no generic ``send_raw_transaction`` path, and no signing responsibility here.

A relay adapter is an injected dependency so deterministic tests never need
network access. Production wiring must explicitly identify a private Polygon
relay and must not silently substitute a public RPC endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .execution import Authorization, ExecutionIntent, TransactionEnvelope
from .governor import GovernorDecision
from .hashing import keccak256_hex
from .signer import SignedTransaction


class PrivateSubmitError(ValueError):
    """Raised when private submission cannot be safely performed."""


class PrivateRelay(Protocol):
    """Minimal private-only transport contract."""

    name: str
    is_private: bool

    def submit_raw_transaction(self, raw_transaction: bytes) -> str:
        """Submit raw bytes to the configured private relay and return tx hash."""


@dataclass(frozen=True)
class PrivateSubmission:
    """Immutable evidence of a successful private submission attempt."""

    intent_hash: str
    governor_decision_hash: str
    transaction_hash: str
    relay_name: str
    relay_private: bool

    def __post_init__(self) -> None:
        for name in (
            "intent_hash",
            "governor_decision_hash",
            "transaction_hash",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
                raise PrivateSubmitError(f"{name} must be a 32-byte 0x hash")
        if not isinstance(self.relay_name, str) or not self.relay_name:
            raise PrivateSubmitError("relay name is required")
        if self.relay_private is not True:
            raise PrivateSubmitError("submission evidence must identify a private relay")


def submit_governed_transaction(
    *,
    relay: PrivateRelay,
    signed_transaction: SignedTransaction,
    governor: GovernorDecision,
    intent: ExecutionIntent,
    authorization: Authorization,
    envelope: TransactionEnvelope,
    now: int,
) -> PrivateSubmission:
    """Submit an exact governed signed transaction to a private relay only.

    Any relay that is not explicitly marked private is rejected before network
    I/O. Relay failures are surfaced as submission failures and never trigger
    a public endpoint fallback.
    """
    if not governor.approved:
        raise PrivateSubmitError("governor did not approve private submission")
    if now < 0:
        raise PrivateSubmitError("current time cannot be negative")
    if intent.deadline < now:
        raise PrivateSubmitError("execution deadline has expired")
    if not getattr(relay, "is_private", False):
        raise PrivateSubmitError("configured relay is not explicitly private")
    relay_name = getattr(relay, "name", None)
    if not isinstance(relay_name, str) or not relay_name:
        raise PrivateSubmitError("private relay identity is required")

    expected_intent_hash = intent.intent_hash()
    if signed_transaction.intent_hash.lower() != expected_intent_hash.lower():
        raise PrivateSubmitError("signed transaction intent identity does not match current intent")
    if signed_transaction.governor_decision_hash.lower() != governor.decision_hash.lower():
        raise PrivateSubmitError("signed transaction governor identity does not match current decision")
    if signed_transaction.transaction_hash.lower() != keccak256_hex(signed_transaction.raw_transaction):
        raise PrivateSubmitError("signed transaction hash does not match raw transaction")
    if governor.intent_hash.lower() != expected_intent_hash.lower():
        raise PrivateSubmitError("governor intent identity does not match current intent")
    if governor.calldata_hash.lower() != envelope.calldata_hash.lower():
        raise PrivateSubmitError("governor calldata identity does not match envelope")
    if governor.route_hash.lower() != intent.route_hash.lower():
        raise PrivateSubmitError("governor route identity does not match intent")
    if governor.economic_proof_hash.lower() != intent.economic_proof_hash.lower():
        raise PrivateSubmitError("governor economic proof identity does not match intent")
    if governor.simulation_proof_hash.lower() != intent.simulation_proof_hash.lower():
        raise PrivateSubmitError("governor simulation proof identity does not match intent")
    if not authorization.matches_envelope(envelope, now, intent):
        raise PrivateSubmitError("authorization does not match exact submission envelope")

    try:
        returned_hash = relay.submit_raw_transaction(signed_transaction.raw_transaction)
    except Exception as exc:
        raise PrivateSubmitError(f"private relay submission failed: {exc}") from exc

    if not isinstance(returned_hash, str) or len(returned_hash) != 66 or not returned_hash.startswith("0x"):
        raise PrivateSubmitError("private relay returned an invalid transaction hash")
    if returned_hash.lower() != signed_transaction.transaction_hash.lower():
        raise PrivateSubmitError("private relay returned a transaction hash different from signed artifact")

    return PrivateSubmission(
        intent_hash=expected_intent_hash,
        governor_decision_hash=governor.decision_hash,
        transaction_hash=signed_transaction.transaction_hash,
        relay_name=relay_name,
        relay_private=True,
    )
