"""Atomic nonce allocation + later intent binding for Phase 19.

The final execution intent contains the allocated nonce, so the nonce must be
reserved before the intent hash can exist. This adapter adds that missing
bridge to the existing unified SQLite store without exposing RPC or signing
authority.
"""
from __future__ import annotations

from .durable_nonce import DurableNonceInvariantError, DurableNonceRecord, NonceStatus
from .sqlite_execution_store import SQLiteExecutionStore


class ExecutionNonceBinding:
    """Small transactional extension around the unified execution store."""

    def __init__(self, store: SQLiteExecutionStore) -> None:
        self.store = store

    def reserve(self, sender: str, reservation_id: str, *, chain_pending_nonce: int) -> DurableNonceRecord:
        sender = self.store._sender(sender)
        if not reservation_id:
            raise DurableNonceInvariantError("reservation_id is required")
        if chain_pending_nonce < 0:
            raise DurableNonceInvariantError("chain pending nonce must be non-negative")
        with self.store._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT next_nonce FROM nonce_cursors WHERE sender=?", (sender,)).fetchone()
                nonce = (chain_pending_nonce if row is None else max(int(row[0]), chain_pending_nonce))
                db.execute("INSERT OR IGNORE INTO nonce_cursors(sender,next_nonce) VALUES(?,?)", (sender, nonce))
                current = int(db.execute("SELECT next_nonce FROM nonce_cursors WHERE sender=?", (sender,)).fetchone()[0])
                nonce = max(current, chain_pending_nonce)
                db.execute("INSERT INTO nonce_records(sender,nonce,reservation_id,intent_hash,status) VALUES(?,?,?,?,?)", (sender, nonce, reservation_id, "", NonceStatus.RESERVED.value))
                db.execute("UPDATE nonce_cursors SET next_nonce=? WHERE sender=?", (nonce + 1, sender))
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        return self.store.get_nonce(sender, nonce)

    def bind(self, *, sender: str, nonce: int, reservation_id: str, intent_hash: str) -> DurableNonceRecord:
        sender = self.store._sender(sender)
        if nonce < 0 or not reservation_id or not intent_hash:
            raise DurableNonceInvariantError("sender, nonce, reservation_id and intent_hash are required")
        with self.store._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT reservation_id,intent_hash,status FROM nonce_records WHERE sender=? AND nonce=?", (sender, nonce)).fetchone()
                if row is None:
                    raise DurableNonceInvariantError("unknown nonce reservation")
                if row[0] != reservation_id or row[2] != NonceStatus.RESERVED.value:
                    raise DurableNonceInvariantError("nonce reservation identity/state mismatch")
                if row[1] not in ("", intent_hash):
                    raise DurableNonceInvariantError("nonce already bound to another intent")
                db.execute("UPDATE nonce_records SET intent_hash=? WHERE sender=? AND nonce=? AND reservation_id=? AND status=?", (intent_hash, sender, nonce, reservation_id, NonceStatus.RESERVED.value))
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        return self.store.get_nonce(sender, nonce)

    def release(self, *, sender: str, nonce: int, reservation_id: str) -> DurableNonceRecord:
        sender = self.store._sender(sender)
        if nonce < 0 or not reservation_id:
            raise DurableNonceInvariantError("sender, nonce and reservation_id are required")
        with self.store._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT reservation_id,status,tx_hash FROM nonce_records WHERE sender=? AND nonce=?", (sender, nonce)).fetchone()
                if row is None:
                    raise DurableNonceInvariantError("unknown nonce reservation")
                if row[0] != reservation_id or row[1] != NonceStatus.RESERVED.value or row[2] is not None:
                    raise DurableNonceInvariantError("only an unsigned RESERVED reservation may be released")
                db.execute("UPDATE nonce_records SET status=? WHERE sender=? AND nonce=? AND reservation_id=? AND status=?", (NonceStatus.RELEASED.value, sender, nonce, reservation_id, NonceStatus.RESERVED.value))
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        return self.store.get_nonce(sender, nonce)
