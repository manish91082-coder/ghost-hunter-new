"""Phase-19 nonce-to-authorization binding policy.

This module contains no RPC, signing, or broadcast capability. It provides a
small deterministic boundary that binds one nonce reservation to one immutable
ExecutionIntent and its Authorization before a transaction can be built.
"""

from __future__ import annotations

from dataclasses import dataclass

from .execution import Authorization, ExecutionIntent
from .nonce_manager import NonceReservation


@dataclass(frozen=True)
class BoundNonce:
    reservation_id: str
    sender: str
    nonce: int
    intent_hash: str


def bind_nonce(reservation: NonceReservation, intent: ExecutionIntent, authorization: Authorization) -> BoundNonce:
    if reservation.sender.lower() != intent.sender.lower():
        raise ValueError("nonce reservation sender does not match intent sender")
    if reservation.nonce != intent.nonce:
        raise ValueError("nonce reservation does not match intent nonce")
    if authorization.sender.lower() != reservation.sender.lower():
        raise ValueError("authorization sender does not match nonce reservation")
    if authorization.nonce != reservation.nonce:
        raise ValueError("authorization nonce does not match nonce reservation")
    expected_intent_hash = intent.intent_hash()
    if authorization.intent_hash != expected_intent_hash:
        raise ValueError("authorization intent hash does not match intent")
    return BoundNonce(reservation.reservation_id, reservation.sender, reservation.nonce, expected_intent_hash)
