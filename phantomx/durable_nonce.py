"""Phase-19 durable-nonce state-machine contract.

This module is deliberately storage-agnostic. It defines the state and
invariants a production nonce repository must provide without pretending that
an in-memory object is durable. A real adapter must implement atomic compare-
and-set/transaction semantics across workers and survive process restarts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NonceStatus(str, Enum):
    RESERVED = "RESERVED"
    SIGNED = "SIGNED"
    SUBMITTED = "SUBMITTED"
    INCLUDED = "INCLUDED"
    REPLACED = "REPLACED"
    DROPPED = "DROPPED"
    REORGED = "REORGED"
    RELEASED = "RELEASED"


@dataclass(frozen=True)
class DurableNonceRecord:
    sender: str
    nonce: int
    reservation_id: str
    intent_hash: str
    status: NonceStatus
    tx_hash: str | None = None
    replacement_of: str | None = None


class DurableNonceInvariantError(ValueError):
    pass


class DurableNonceStore:
    """Reference state machine; storage adapter remains intentionally external."""

    def __init__(self) -> None:
        self._records: dict[str, DurableNonceRecord] = {}

    def create(self, record: DurableNonceRecord) -> None:
        key = f"{record.sender.lower()}:{record.nonce}"
        if key in self._records:
            raise DurableNonceInvariantError("nonce already reserved")
        if record.nonce < 0 or not record.sender or not record.reservation_id or not record.intent_hash:
            raise DurableNonceInvariantError("invalid nonce record")
        self._records[key] = record

    def transition(self, sender: str, nonce: int, new_status: NonceStatus, *, tx_hash: str | None = None, replacement_of: str | None = None) -> DurableNonceRecord:
        key = f"{sender.lower()}:{nonce}"
        try:
            current = self._records[key]
        except KeyError as exc:
            raise DurableNonceInvariantError("unknown nonce reservation") from exc

        allowed = {
            NonceStatus.RESERVED: {NonceStatus.SIGNED, NonceStatus.RELEASED},
            NonceStatus.SIGNED: {NonceStatus.SUBMITTED, NonceStatus.RELEASED},
            NonceStatus.SUBMITTED: {NonceStatus.INCLUDED, NonceStatus.REPLACED, NonceStatus.DROPPED, NonceStatus.REORGED},
            NonceStatus.INCLUDED: {NonceStatus.REORGED},
            NonceStatus.REPLACED: {NonceStatus.SUBMITTED, NonceStatus.INCLUDED, NonceStatus.DROPPED},
            NonceStatus.DROPPED: {NonceStatus.RELEASED},
            NonceStatus.REORGED: {NonceStatus.SUBMITTED, NonceStatus.DROPPED},
            NonceStatus.RELEASED: set(),
        }
        if new_status not in allowed[current.status]:
            raise DurableNonceInvariantError(f"invalid nonce transition: {current.status} -> {new_status}")
        if new_status in {NonceStatus.SUBMITTED, NonceStatus.INCLUDED, NonceStatus.REPLACED} and not tx_hash:
            raise DurableNonceInvariantError("transaction hash required for submitted/included/replaced state")
        updated = DurableNonceRecord(
            current.sender, current.nonce, current.reservation_id, current.intent_hash,
            new_status, tx_hash or current.tx_hash, replacement_of or current.replacement_of,
        )
        self._records[key] = updated
        return updated

    def get(self, sender: str, nonce: int) -> DurableNonceRecord:
        return self._records[f"{sender.lower()}:{nonce}"]
