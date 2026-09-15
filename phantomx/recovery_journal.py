"""Durable recovery journal for crash-window reconciliation.

This journal records intent-level recovery decisions before external side
 effects. It does not itself mutate nonce or transaction stores and has no
 signing/submission authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from .chain_observer import ObservationDecision
from .recovery_coordinator import RecoveryAction, RecoveryDecision


@dataclass(frozen=True)
class RecoveryJournalEntry:
    sequence: int
    record_hash: str
    action: RecoveryAction
    chain_state: str
    tx_hash: str
    replacement_tx_hash: str | None
    reason: str
    applied: bool = False


class SQLiteRecoveryJournal:
    """Append-only decision journal with idempotent application markers."""

    def __init__(self, path: str | Path, *, timeout_seconds: float = 30.0) -> None:
        self.path = str(path)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=self.timeout_seconds, isolation_level=None)
        db.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds * 1000)}")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS recovery_journal (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_hash TEXT NOT NULL,
                    action TEXT NOT NULL,
                    chain_state TEXT NOT NULL,
                    tx_hash TEXT NOT NULL,
                    replacement_tx_hash TEXT,
                    reason TEXT NOT NULL,
                    applied INTEGER NOT NULL DEFAULT 0 CHECK (applied IN (0,1)),
                    UNIQUE(record_hash, tx_hash, action)
                )"""
            )

    def append(self, decision: RecoveryDecision, observation: ObservationDecision) -> RecoveryJournalEntry:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT sequence,record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason,applied "
                    "FROM recovery_journal WHERE record_hash=? AND tx_hash=? AND action=?",
                    (decision.record_hash.lower(), observation.tx_hash.lower(), decision.action.value),
                ).fetchone()
                if row is None:
                    db.execute(
                        "INSERT INTO recovery_journal(record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason) VALUES (?,?,?,?,?,?)",
                        (decision.record_hash.lower(), decision.action.value, observation.state.value, observation.tx_hash.lower(),
                         observation.replacement_tx_hash.lower() if observation.replacement_tx_hash else None, decision.reason),
                    )
                    row = db.execute(
                        "SELECT sequence,record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason,applied "
                        "FROM recovery_journal WHERE rowid=last_insert_rowid()"
                    ).fetchone()
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        return self._row(row)

    def mark_applied(self, sequence: int) -> RecoveryJournalEntry:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("UPDATE recovery_journal SET applied=1 WHERE sequence=?", (sequence,))
                row = db.execute(
                    "SELECT sequence,record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason,applied FROM recovery_journal WHERE sequence=?",
                    (sequence,),
                ).fetchone()
                if row is None:
                    raise KeyError("unknown recovery journal sequence")
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        return self._row(row)

    def pending(self) -> list[RecoveryJournalEntry]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT sequence,record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason,applied "
                "FROM recovery_journal WHERE applied=0 ORDER BY sequence"
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: tuple[object, ...]) -> RecoveryJournalEntry:
        return RecoveryJournalEntry(
            sequence=int(row[0]), record_hash=str(row[1]), action=RecoveryAction(str(row[2])),
            chain_state=str(row[3]), tx_hash=str(row[4]),
            replacement_tx_hash=str(row[5]) if row[5] is not None else None,
            reason=str(row[6]), applied=bool(row[7]),
        )
