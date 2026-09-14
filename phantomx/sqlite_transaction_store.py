"""Durable TransactionRecord persistence for Phase 19.

This store persists the forensic transaction identity independently from the
nonce allocator while binding every record to the same sender, nonce and
reservation identity. It performs no signing, RPC observation or submission.

The store is deliberately single-host SQLite, matching SQLiteNonceStore's
crash-safety boundary. Multi-host execution must move both persistence layers
to one transactional service before production.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from .execution import ExecutionIntent, ExecutionState
from .nonce_binding import BoundNonce
from .transaction_record import TransactionRecord

_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")

_ALLOWED_TRANSITIONS = {
    ExecutionState.SIGNED: {ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PROFIT_FAILED},
    ExecutionState.PRIVATE_SUBMITTED: {ExecutionState.PENDING, ExecutionState.PROFIT_FAILED},
    ExecutionState.PENDING: {ExecutionState.INCLUDED, ExecutionState.PROFIT_FAILED},
    ExecutionState.INCLUDED: {ExecutionState.RECONCILED, ExecutionState.PROFIT_FAILED},
    ExecutionState.RECONCILED: {ExecutionState.PROFIT_CONFIRMED, ExecutionState.PROFIT_FAILED},
    ExecutionState.PROFIT_CONFIRMED: set(),
    ExecutionState.PROFIT_FAILED: set(),
}


class SQLiteTransactionStore:
    """Crash-persistent transaction records with atomic lifecycle transitions."""

    def __init__(self, path: str | Path, *, timeout_seconds: float = 30.0) -> None:
        self.path = str(path)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout_seconds, isolation_level=None)
        connection.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds * 1000)}")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS transaction_records (
                    record_hash TEXT PRIMARY KEY,
                    intent_hash TEXT NOT NULL,
                    authorization_hash TEXT NOT NULL,
                    reservation_id TEXT NOT NULL,
                    chain_id INTEGER NOT NULL CHECK (chain_id > 0),
                    sender TEXT NOT NULL,
                    executor TEXT NOT NULL,
                    nonce INTEGER NOT NULL CHECK (nonce >= 0),
                    calldata_hash TEXT NOT NULL,
                    gas_limit INTEGER NOT NULL CHECK (gas_limit > 0),
                    max_fee_per_gas INTEGER NOT NULL CHECK (max_fee_per_gas >= 0),
                    max_priority_fee_per_gas INTEGER NOT NULL CHECK (max_priority_fee_per_gas >= 0),
                    tx_hash TEXT NOT NULL UNIQUE,
                    state TEXT NOT NULL,
                    replacement_of TEXT,
                    FOREIGN KEY (replacement_of) REFERENCES transaction_records(tx_hash)
                );
                CREATE INDEX IF NOT EXISTS idx_tx_records_intent ON transaction_records(intent_hash);
                CREATE INDEX IF NOT EXISTS idx_tx_records_nonce ON transaction_records(sender, nonce);
                CREATE INDEX IF NOT EXISTS idx_tx_records_reservation ON transaction_records(reservation_id);
                """
            )

    @staticmethod
    def _validate_record(record: TransactionRecord) -> None:
        if not _TX_HASH.fullmatch(record.tx_hash):
            raise ValueError("invalid transaction hash")
        if record.replacement_of is not None and not _TX_HASH.fullmatch(record.replacement_of):
            raise ValueError("invalid replacement transaction hash")
        if record.chain_id <= 0 or record.nonce < 0 or record.gas_limit <= 0:
            raise ValueError("invalid transaction record numeric fields")

    @staticmethod
    def _row_to_record(row: tuple[object, ...]) -> TransactionRecord:
        return TransactionRecord(
            intent_hash=str(row[1]),
            authorization_hash=str(row[2]),
            reservation_id=str(row[3]),
            chain_id=int(row[4]),
            sender=str(row[5]),
            executor=str(row[6]),
            nonce=int(row[7]),
            calldata_hash=str(row[8]),
            gas_limit=int(row[9]),
            max_fee_per_gas=int(row[10]),
            max_priority_fee_per_gas=int(row[11]),
            tx_hash=str(row[12]),
            state=ExecutionState(str(row[13])),
            replacement_of=str(row[14]) if row[14] is not None else None,
        )

    def create(
        self,
        record: TransactionRecord,
        *,
        intent: ExecutionIntent,
        bound_nonce: BoundNonce,
    ) -> TransactionRecord:
        """Persist a signed record only when its intent/nonce binding is exact.

        Full Authorization/Envelope objects remain mandatory at record
        construction time. This persistence layer never attempts to rebuild
        them from hashes, which prevents a false sense of cryptographic proof.
        """
        self._validate_record(record)
        if record.intent_hash.lower() != intent.intent_hash().lower():
            raise ValueError("transaction record intent mismatch")
        if record.sender.lower() != bound_nonce.sender.lower() or record.nonce != bound_nonce.nonce:
            raise ValueError("transaction record nonce binding mismatch")
        if record.reservation_id != bound_nonce.reservation_id:
            raise ValueError("transaction record reservation mismatch")
        if record.state is not ExecutionState.SIGNED:
            raise ValueError("new durable transaction record must start SIGNED")
        record_hash = record.record_hash()
        payload = record.canonical()
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT record_hash FROM transaction_records WHERE tx_hash = ?", (record.tx_hash.lower(),)
                ).fetchone()
                if existing is not None:
                    raise ValueError("transaction hash already recorded")
                connection.execute(
                    "INSERT INTO transaction_records(record_hash,intent_hash,authorization_hash,reservation_id,"
                    "chain_id,sender,executor,nonce,calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,"
                    "tx_hash,state,replacement_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        record_hash,
                        payload["intent_hash"], payload["authorization_hash"], payload["reservation_id"],
                        payload["chain_id"], payload["sender"], payload["executor"], payload["nonce"],
                        payload["calldata_hash"], payload["gas_limit"], payload["max_fee_per_gas"],
                        payload["max_priority_fee_per_gas"], payload["tx_hash"], payload["state"], payload["replacement_of"],
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return record

    def get(self, record_hash: str) -> TransactionRecord:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,"
                "calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of "
                "FROM transaction_records WHERE record_hash = ?",
                (record_hash.lower(),),
            ).fetchone()
        if row is None:
            raise KeyError("unknown transaction record")
        record = self._row_to_record(row)
        if record.record_hash().lower() != record_hash.lower():
            raise ValueError("stored transaction record hash mismatch")
        return record

    def get_by_tx_hash(self, tx_hash: str) -> TransactionRecord:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,"
                "calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of "
                "FROM transaction_records WHERE tx_hash = ?",
                (tx_hash.lower(),),
            ).fetchone()
        if row is None:
            raise KeyError("unknown transaction hash")
        return self._row_to_record(row)

    def transition(self, record_hash: str, new_state: ExecutionState) -> TransactionRecord:
        """Atomically advance one record; invalid transitions leave state unchanged."""
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,"
                    "calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of "
                    "FROM transaction_records WHERE record_hash = ?",
                    (record_hash.lower(),),
                ).fetchone()
                if row is None:
                    raise KeyError("unknown transaction record")
                current = ExecutionState(str(row[13]))
                if new_state not in _ALLOWED_TRANSITIONS[current]:
                    raise ValueError(f"invalid transaction transition: {current} -> {new_state}")
                connection.execute(
                    "UPDATE transaction_records SET state = ? WHERE record_hash = ? AND state = ?",
                    (new_state.value, record_hash.lower(), current.value),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return self.get(record_hash)

    def create_replacement(
        self,
        replacement: TransactionRecord,
        *,
        intent: ExecutionIntent,
        bound_nonce: BoundNonce,
        replaces_tx_hash: str,
    ) -> TransactionRecord:
        """Create a new signed record for the same nonce with explicit linkage."""
        self._validate_record(replacement)
        replaces_tx_hash = replaces_tx_hash.lower()
        if replacement.replacement_of != replaces_tx_hash:
            raise ValueError("replacement_of must identify the transaction being replaced")
        if replacement.sender.lower() != bound_nonce.sender.lower() or replacement.nonce != bound_nonce.nonce:
            raise ValueError("replacement nonce binding mismatch")
        if replacement.reservation_id != bound_nonce.reservation_id:
            raise ValueError("replacement reservation mismatch")
        if replacement.intent_hash.lower() != intent.intent_hash().lower():
            raise ValueError("replacement intent mismatch")
        if replacement.state is not ExecutionState.SIGNED:
            raise ValueError("replacement record must start SIGNED")
        previous = self.get_by_tx_hash(replaces_tx_hash)
        if previous.sender.lower() != replacement.sender.lower() or previous.nonce != replacement.nonce:
            raise ValueError("replacement must preserve sender and nonce")
        if previous.state not in {ExecutionState.SIGNED, ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PENDING}:
            raise ValueError("replacement source is not replaceable")
        return self.create(replacement, intent=intent, bound_nonce=bound_nonce)

    def records(self) -> list[TransactionRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,"
                "calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of "
                "FROM transaction_records ORDER BY rowid"
            ).fetchall()
        return [self._row_to_record(row) for row in rows]
