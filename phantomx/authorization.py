"""One-shot authorization control model for Phase 19.

This module is a deterministic policy model, not a production signer or
persistent nonce service. It makes authorization consumption explicit so a
future production controller can preserve the same safety invariants.
"""

from __future__ import annotations

from dataclasses import dataclass

from .execution import Authorization, ExecutionIntent


@dataclass(frozen=True)
class AuthorizationReceipt:
    """Evidence that a specific authorization was consumed once."""

    intent_hash: str
    nonce: int


class AuthorizationController:
    """Fail-closed, single-use authorization controller for tests."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()
        self._nonces: dict[str, int] = {}

    def authorize(self, authorization: Authorization, intent: ExecutionIntent, now: int) -> AuthorizationReceipt:
        if not authorization.matches(intent, now):
            raise ValueError("authorization does not match current intent")

        intent_hash = intent.intent_hash().lower()
        if intent_hash in self._consumed:
            raise ValueError("authorization replay detected")

        previous_nonce = self._nonces.get(intent.sender.lower())
        if previous_nonce is not None and intent.nonce <= previous_nonce:
            raise ValueError("nonce is not strictly increasing for sender")

        self._consumed.add(intent_hash)
        self._nonces[intent.sender.lower()] = intent.nonce
        return AuthorizationReceipt(intent_hash=intent_hash, nonce=intent.nonce)

    def is_consumed(self, intent_hash: str) -> bool:
        return intent_hash.lower() in self._consumed

    def last_nonce(self, sender: str) -> int | None:
        return self._nonces.get(sender.lower())
