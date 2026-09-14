"""Phase-19 durable, process-safe nonce persistence.

This adapter turns the Phase-19 nonce policy/state machine into a persistent
single-host store using SQLite transactions. It is intentionally limited to
nonce state and does not perform RPC, signing, or transaction submission.

Design boundary:
- every reservation/reconciliation/transition is one atomic transaction;
- sender+nonce is unique;
- reservation_id is globally unique;
- BEGIN IMMEDIATE serializes competing writers before the cursor is read;
- WAL + synchronous=FULL provide local crash-safe transactional semantics;
- this store is for processes sharing one local host/filesystem, not a
  network filesystem or multi-host database service.

A future production deployment may replace this adapter with PostgreSQL or
another transactional service if the execution topology becomes multi-host.
The public interface and invariants should remain compatible.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Iterator

from .durable_nonce import (
    DurableNonceInvariantError,
    DurableNonceRecord,
    NonceStatus,
)


_ALLOWED_TRANSITIONS = {
    NonceStatus.RESERVED: {NonceStatus.SIGNED, NonceStatus.RELEASED},
    NonceStatus.SIGNED: {NonceStatus.SUBMITTED, NonceStatus.RELEASED},
    NonceStatus.SUBMITTED: {
        NonceStatus.INCLUDED,
        NonceStatus.REPLACED,
        NonceStatus.DROPPED,
        NonceStatus.REORGED,
    },
    NonceStatus.INCLUDED: {NonceStatus.REORGED},
    NonceStatus.REPLACED: {
        NonceStatus.SUBMITTED,
        NonceStatus.INCLUDED,
        NonceStatus.DROPPED,
    },
    NonceStatus.DROPPED: {NonceStatus.RELEASED},
    NonceStatus.REORGED: {NonceStatus.SUBMITTED, NonceStatus.DROPPED},
    NonceStatus.RELEASED: set(),
}


class SQLiteNonceStore:
    """Persistent nonce allocator/state machine with atomic writer semantics."""

    def __init__(self, path: str | Path, *, timeout_seconds: float = 30.0) -> None:
        self.path = str(path)
        self.timeout_seconds = timeout_seconds
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        connection.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds * 1000)}")
        connection.execute("PRAGMA foreign_keys=ON")

        # journal_mode is a database-level transition and can briefly return
        # SQLITE_BUSY when several processes open a fresh database together.
        # Retry only this setup operation. Transactional writers still use
        # BEGIN IMMEDIATE below, so allocation remains serialized atomically.
        delay = 0.005
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                connection.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or time.monotonic() >= deadline:
                    connection.close()
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 0.1)

        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS nonce_cursors (
                    sender TEXT PRIMARY KEY,
                    next_nonce INTEGER NOT NULL CHECK (next_nonce >= 0)
                );

                CREATE TABLE IF NOT EXISTS nonce_records (
                    sender TEXT NOT NULL,
                    nonce INTEGER NOT NULL CHECK (nonce >= 0),
                    reservation_id TEXT NOT NULL UNIQUE,
                    intent_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tx_hash TEXT,
                    replacement_of TEXT,
                    PRIMARY KEY (sender, nonce),
                    FOREIGN KEY (sender) REFERENCES nonce_cursors(sender)
                );

                CREATE INDEX IF NOT EXISTS idx_nonce_records_tx_hash
                    ON nonce_records(tx_hash);
                CREATE INDEX IF NOT EXISTS idx_nonce_records_intent_hash
                    ON nonce_records(intent_hash);
                """
            )

    @staticmethod
    def _sender(sender: str) -> str:
        normalized = sender.strip().lower()
        if not normalized:
            raise DurableNonceInvariantError("sender is required")
        return normalized

    @staticmethod
    def _validate_reservation_inputs(sender: str, reservation_id: str, intent_hash: str) -> None:
        if not reservation_id:
            raise DurableNonceInvariantError("reservation_id is required")
        if not intent_hash:
            raise DurableNonceInvariantError("intent_hash is required")

    def reserve(
        self,
        sender: str,
        reservation_id: str,
        intent_hash: str,
        *,
        chain_pending_nonce: int | None = None,
    ) -> DurableNonceRecord:
        """Atomically allocate one nonce for a sender.

        ``chain_pending_nonce`` is an observed lower bound from the chain. The
        allocator advances to it when necessary and never moves backwards.
        """
        sender = self._sender(sender)
        self._validate_reservation_inputs(sender, reservation_id, intent_hash)
        if chain_pending_nonce is not None and chain_pending_nonce < 0:
            raise DurableNonceInvariantError("chain pending nonce must be non-negative")

        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT next_nonce FROM nonce_cursors WHERE sender = ?",
                    (sender,),
                ).fetchone()
                if row is None:
                    next_nonce = chain_pending_nonce or 0
                    connection.execute(
                        "INSERT INTO nonce_cursors(sender, next_nonce) VALUES (?, ?)",
                        (sender, next_nonce),
                    )
                else:
                    next_nonce = int(row[0])
                    if chain_pending_nonce is not None and chain_pending_nonce > next_nonce:
                        next_nonce = chain_pending_nonce
                        connection.execute(
                            "UPDATE nonce_cursors SET next_nonce = ? WHERE sender = ?",
                            (next_nonce, sender),
                        )

                try:
                    connection.execute(
                        "INSERT INTO nonce_records(sender, nonce, reservation_id, intent_hash, status) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (sender, next_nonce, reservation_id, intent_hash, NonceStatus.RESERVED.value),
                    )
                except sqlite3.IntegrityError as exc:
                    if "reservation_id" in str(exc):
                        raise DurableNonceInvariantError("reservation replay detected") from exc
                    raise DurableNonceInvariantError("nonce already reserved") from exc

                connection.execute(
                    "UPDATE nonce_cursors SET next_nonce = ? WHERE sender = ?",
                    (next_nonce + 1, sender),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

        return DurableNonceRecord(
            sender=sender,
            nonce=next_nonce,
            reservation_id=reservation_id,
            intent_hash=intent_hash,
            status=NonceStatus.RESERVED,
        )

    def reconcile_pending_nonce(self, sender: str, chain_pending_nonce: int) -> int:
        """Advance a sender cursor to observed chain state, never backwards."""
        sender = self._sender(sender)
        if chain_pending_nonce < 0:
            raise DurableNonceInvariantError("chain pending nonce must be non-negative")

        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT next_nonce FROM nonce_cursors WHERE sender = ?",
                    (sender,),
                ).fetchone()
                current = 0 if row is None else int(row[0])
                updated = max(current, chain_pending_nonce)
                if row is None:
                    connection.execute(
                        "INSERT INTO nonce_cursors(sender, next_nonce) VALUES (?, ?)",
                        (sender, updated),
                    )
                elif updated != current:
                    connection.execute(
                        "UPDATE nonce_cursors SET next_nonce = ? WHERE sender = ?",
                        (updated, sender),
                    )
                connection.execute("COMMIT")
                return updated
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def next_nonce(self, sender: str) -> int:
        sender = self._sender(sender)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT next_nonce FROM nonce_cursors WHERE sender = ?",
                (sender,),
            ).fetchone()
        return 0 if row is None else int(row[0])

    def get(self, sender: str, nonce: int) -> DurableNonceRecord:
        sender = self._sender(sender)
        if nonce < 0:
            raise DurableNonceInvariantError("nonce must be non-negative")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT sender, nonce, reservation_id, intent_hash, status, tx_hash, replacement_of "
                "FROM nonce_records WHERE sender = ? AND nonce = ?",
                (sender, nonce),
            ).fetchone()
        if row is None:
            raise DurableNonceInvariantError("unknown nonce reservation")
        return DurableNonceRecord(
            sender=row[0],
            nonce=int(row[1]),
            reservation_id=row[2],
            intent_hash=row[3],
            status=NonceStatus(row[4]),
            tx_hash=row[5],
            replacement_of=row[6],
        )

    def transition(
        self,
        sender: str,
        nonce: int,
        new_status: NonceStatus,
        *,
        tx_hash: str | None = None,
        replacement_of: str | None = None,
    ) -> DurableNonceRecord:
        """Atomically validate and apply one state transition."""
        sender = self._sender(sender)
        if nonce < 0:
            raise DurableNonceInvariantError("nonce must be non-negative")
        if new_status in {
            NonceStatus.SUBMITTED,
            NonceStatus.INCLUDED,
            NonceStatus.REPLACED,
        } and not tx_hash:
            raise DurableNonceInvariantError(
                "transaction hash required for submitted/included/replaced state"
            )
        if new_status is NonceStatus.REPLACED and not replacement_of:
            raise DurableNonceInvariantError("replacement_of required for replacement state")

        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT status, reservation_id, intent_hash, tx_hash, replacement_of "
                    "FROM nonce_records WHERE sender = ? AND nonce = ?",
                    (sender, nonce),
                ).fetchone()
                if row is None:
                    raise DurableNonceInvariantError("unknown nonce reservation")

                current_status = NonceStatus(row[0])
                if new_status not in _ALLOWED_TRANSITIONS[current_status]:
                    raise DurableNonceInvariantError(
                        f"invalid nonce transition: {current_status} -> {new_status}"
                    )

                if new_status is NonceStatus.REPLACED and replacement_of != row[3]:
                    raise DurableNonceInvariantError(
                        "replacement_of must match the currently active transaction hash"
                    )

                next_tx_hash = tx_hash or row[3]
                next_replacement_of = replacement_of or row[4]
                connection.execute(
                    "UPDATE nonce_records SET status = ?, tx_hash = ?, replacement_of = ? "
                    "WHERE sender = ? AND nonce = ? AND status = ?",
                    (
                        new_status.value,
                        next_tx_hash,
                        next_replacement_of,
                        sender,
                        nonce,
                        current_status.value,
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

        return DurableNonceRecord(
            sender=sender,
            nonce=nonce,
            reservation_id=row[1],
            intent_hash=row[2],
            status=new_status,
            tx_hash=next_tx_hash,
            replacement_of=next_replacement_of,
        )

    def records(self) -> Iterator[DurableNonceRecord]:
        """Return a committed snapshot iterator for diagnostics/tests."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT sender, nonce, reservation_id, intent_hash, status, tx_hash, replacement_of "
                "FROM nonce_records ORDER BY sender, nonce"
            ).fetchall()
        for row in rows:
            yield DurableNonceRecord(
                sender=row[0],
                nonce=int(row[1]),
                reservation_id=row[2],
                intent_hash=row[3],
                status=NonceStatus(row[4]),
                tx_hash=row[5],
                replacement_of=row[6],
            )
