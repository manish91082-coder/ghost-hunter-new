"""Phase-19 nonce reservation policy model.

This module is intentionally dependency-free and does not talk to Polygon.
It models the invariants required by the future durable nonce service:
- one reservation per sequence number
- monotonic allocation
- explicit reconciliation of externally observed pending nonce
- no silent rollback

It is not a production concurrency primitive. Production integration must
provide durable atomic storage/locking and reconcile against chain state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NonceReservation:
    sender: str
    nonce: int
    reservation_id: str


class NonceManager:
    """Deterministic policy model for nonce allocation and chain reconciliation."""

    def __init__(self, starting_nonce: int = 0) -> None:
        if starting_nonce < 0:
            raise ValueError("starting nonce must be non-negative")
        self._next = starting_nonce
        self._last_reserved: dict[str, int] = {}
        self._reservations: dict[str, NonceReservation] = {}

    def reserve(self, sender: str, reservation_id: str) -> NonceReservation:
        sender = sender.lower()
        if not sender:
            raise ValueError("sender is required")
        if not reservation_id:
            raise ValueError("reservation_id is required")
        if reservation_id in self._reservations:
            raise ValueError("reservation replay detected")

        nonce = self._next
        self._next += 1
        previous = self._last_reserved.get(sender)
        if previous is not None and nonce <= previous:
            raise RuntimeError("nonce allocation regressed")

        reservation = NonceReservation(sender, nonce, reservation_id)
        self._reservations[reservation_id] = reservation
        self._last_reserved[sender] = nonce
        return reservation

    def reconcile_pending_nonce(self, chain_pending_nonce: int) -> None:
        if chain_pending_nonce < 0:
            raise ValueError("chain pending nonce must be non-negative")
        # Never move the allocator backwards. If chain state has advanced,
        # move our next candidate forward so stale reservations cannot recur.
        if chain_pending_nonce > self._next:
            self._next = chain_pending_nonce

    def reservation(self, reservation_id: str) -> NonceReservation:
        try:
            return self._reservations[reservation_id]
        except KeyError as exc:
            raise KeyError("unknown nonce reservation") from exc

    @property
    def next_nonce(self) -> int:
        return self._next
