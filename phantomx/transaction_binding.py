"""Fail-closed binding between an authorization and transaction envelope.

This is a deterministic policy model for Phase 19. It does not sign or
broadcast transactions. Production integration must additionally validate the
same fields immediately before signing and submission against live chain
state.
"""

from __future__ import annotations

from dataclasses import dataclass

from .execution import Authorization, ExecutionIntent, TransactionEnvelope


@dataclass(frozen=True)
class VerifiedTransaction:
    intent_hash: str
    calldata_hash: str
    nonce: int


class TransactionBindingVerifier:
    """Verify that the envelope is exactly the authorized execution envelope."""

    def verify(
        self,
        authorization: Authorization,
        intent: ExecutionIntent,
        envelope: TransactionEnvelope,
        now: int,
    ) -> VerifiedTransaction:
        if not authorization.matches(intent, now):
            raise ValueError("authorization is invalid, expired, or mismatched")

        if envelope.chain_id != intent.chain_id:
            raise ValueError("chain id mismatch")
        if envelope.sender.lower() != intent.sender.lower():
            raise ValueError("sender mismatch")
        if envelope.executor.lower() != intent.executor.lower():
            raise ValueError("executor mismatch")
        if envelope.nonce != intent.nonce:
            raise ValueError("nonce mismatch")
        if envelope.calldata_hash.lower() != intent.calldata_hash.lower():
            raise ValueError("calldata hash mismatch")

        return VerifiedTransaction(
            intent_hash=intent.intent_hash(),
            calldata_hash=envelope.calldata_hash,
            nonce=envelope.nonce,
        )
