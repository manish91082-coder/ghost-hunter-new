"""Unified single-host durable execution store for Phase 19.

Nonce state, transaction identity and recovery evidence share one SQLite
transaction boundary. No RPC, signing, relay or broadcast authority exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from .durable_nonce import DurableNonceInvariantError, DurableNonceRecord, NonceStatus
from .execution import ExecutionIntent, ExecutionState
from .nonce_binding import BoundNonce
from .recovery_coordinator import RecoveryAction, RecoveryDecision
from .transaction_record import TransactionRecord

_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")
_NONCE_TRANSITIONS = {
    NonceStatus.RESERVED: {NonceStatus.SIGNED, NonceStatus.RELEASED},
    NonceStatus.SIGNED: {NonceStatus.SUBMITTED, NonceStatus.RELEASED},
    NonceStatus.SUBMITTED: {NonceStatus.INCLUDED, NonceStatus.REPLACED, NonceStatus.DROPPED, NonceStatus.REORGED},
    NonceStatus.INCLUDED: {NonceStatus.REORGED},
    NonceStatus.REPLACED: {NonceStatus.SUBMITTED, NonceStatus.INCLUDED, NonceStatus.DROPPED},
    NonceStatus.DROPPED: {NonceStatus.RELEASED},
    NonceStatus.REORGED: {NonceStatus.SUBMITTED, NonceStatus.DROPPED},
    NonceStatus.RELEASED: set(),
}
_TX_TRANSITIONS = {
    ExecutionState.SIGNED: {ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PROFIT_FAILED},
    ExecutionState.PRIVATE_SUBMITTED: {ExecutionState.PENDING, ExecutionState.PROFIT_FAILED},
    ExecutionState.PENDING: {ExecutionState.INCLUDED, ExecutionState.PROFIT_FAILED},
    ExecutionState.INCLUDED: {ExecutionState.RECONCILED, ExecutionState.PROFIT_FAILED},
    ExecutionState.RECONCILED: {ExecutionState.PROFIT_CONFIRMED, ExecutionState.PROFIT_FAILED},
    ExecutionState.PROFIT_CONFIRMED: set(),
    ExecutionState.PROFIT_FAILED: set(),
}

@dataclass(frozen=True)
class RecoveryApplication:
    journal_sequence: int
    transaction: TransactionRecord
    nonce: DurableNonceRecord

class SQLiteExecutionStore:
    """Atomic durable boundary for nonce + transaction + recovery journal."""
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
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS nonce_cursors(sender TEXT PRIMARY KEY,next_nonce INTEGER NOT NULL CHECK(next_nonce>=0));
            CREATE TABLE IF NOT EXISTS nonce_records(sender TEXT NOT NULL,nonce INTEGER NOT NULL CHECK(nonce>=0),reservation_id TEXT NOT NULL UNIQUE,intent_hash TEXT NOT NULL,status TEXT NOT NULL,tx_hash TEXT,replacement_of TEXT,PRIMARY KEY(sender,nonce),FOREIGN KEY(sender) REFERENCES nonce_cursors(sender));
            CREATE TABLE IF NOT EXISTS transaction_records(record_hash TEXT PRIMARY KEY,intent_hash TEXT NOT NULL,authorization_hash TEXT NOT NULL,reservation_id TEXT NOT NULL,chain_id INTEGER NOT NULL CHECK(chain_id>0),sender TEXT NOT NULL,executor TEXT NOT NULL,nonce INTEGER NOT NULL CHECK(nonce>=0),calldata_hash TEXT NOT NULL,gas_limit INTEGER NOT NULL CHECK(gas_limit>0),max_fee_per_gas INTEGER NOT NULL CHECK(max_fee_per_gas>=0),max_priority_fee_per_gas INTEGER NOT NULL CHECK(max_priority_fee_per_gas>=0),tx_hash TEXT NOT NULL UNIQUE,state TEXT NOT NULL,replacement_of TEXT,FOREIGN KEY(replacement_of) REFERENCES transaction_records(tx_hash));
            CREATE TABLE IF NOT EXISTS recovery_journal(sequence INTEGER PRIMARY KEY AUTOINCREMENT,record_hash TEXT NOT NULL,action TEXT NOT NULL,chain_state TEXT NOT NULL,tx_hash TEXT NOT NULL,replacement_tx_hash TEXT,reason TEXT NOT NULL,applied INTEGER NOT NULL DEFAULT 0 CHECK(applied IN(0,1)),UNIQUE(record_hash,tx_hash,action));
            CREATE INDEX IF NOT EXISTS idx_tx_nonce ON transaction_records(sender,nonce);
            CREATE INDEX IF NOT EXISTS idx_nonce_tx ON nonce_records(tx_hash);
            """)

    @staticmethod
    def _sender(sender: str) -> str:
        value = sender.strip().lower()
        if not value:
            raise DurableNonceInvariantError("sender is required")
        return value

    def reserve_nonce(self, sender: str, reservation_id: str, intent_hash: str, *, chain_pending_nonce: int | None = None) -> DurableNonceRecord:
        sender = self._sender(sender)
        if not reservation_id or not intent_hash:
            raise DurableNonceInvariantError("reservation_id and intent_hash are required")
        if chain_pending_nonce is not None and chain_pending_nonce < 0:
            raise DurableNonceInvariantError("chain pending nonce must be non-negative")
        with self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT next_nonce FROM nonce_cursors WHERE sender=?", (sender,)).fetchone()
                nonce = (chain_pending_nonce or 0) if row is None else int(row[0])
                if chain_pending_nonce is not None:
                    nonce = max(nonce, chain_pending_nonce)
                db.execute("INSERT OR IGNORE INTO nonce_cursors(sender,next_nonce) VALUES(?,?)", (sender, nonce))
                current = int(db.execute("SELECT next_nonce FROM nonce_cursors WHERE sender=?", (sender,)).fetchone()[0])
                nonce = max(current, chain_pending_nonce) if chain_pending_nonce is not None else current
                db.execute("INSERT INTO nonce_records(sender,nonce,reservation_id,intent_hash,status) VALUES(?,?,?,?,?)", (sender, nonce, reservation_id, intent_hash, NonceStatus.RESERVED.value))
                db.execute("UPDATE nonce_cursors SET next_nonce=? WHERE sender=?", (nonce + 1, sender))
                db.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                if db.in_transaction: db.execute("ROLLBACK")
                raise DurableNonceInvariantError("reservation or nonce already exists") from exc
            except Exception:
                if db.in_transaction: db.execute("ROLLBACK")
                raise
        return self.get_nonce(sender, nonce)

    def get_nonce(self, sender: str, nonce: int) -> DurableNonceRecord:
        sender = self._sender(sender)
        with self._connect() as db:
            row = db.execute("SELECT sender,nonce,reservation_id,intent_hash,status,tx_hash,replacement_of FROM nonce_records WHERE sender=? AND nonce=?", (sender, nonce)).fetchone()
        if row is None: raise KeyError("unknown nonce reservation")
        return DurableNonceRecord(sender=row[0], nonce=int(row[1]), reservation_id=row[2], intent_hash=row[3], status=NonceStatus(row[4]), tx_hash=row[5], replacement_of=row[6])

    @staticmethod
    def _record_from_row(row: tuple[object, ...]) -> TransactionRecord:
        return TransactionRecord(intent_hash=row[1], authorization_hash=row[2], reservation_id=row[3], chain_id=int(row[4]), sender=row[5], executor=row[6], nonce=int(row[7]), calldata_hash=row[8], gas_limit=int(row[9]), max_fee_per_gas=int(row[10]), max_priority_fee_per_gas=int(row[11]), tx_hash=row[12], state=ExecutionState(row[13]), replacement_of=row[14])

    def create_signed_transaction(self, record: TransactionRecord, *, intent: ExecutionIntent, bound_nonce: BoundNonce) -> TransactionRecord:
        if record.state is not ExecutionState.SIGNED: raise ValueError("new transaction must start SIGNED")
        if not _TX_HASH.fullmatch(record.tx_hash): raise ValueError("invalid transaction hash")
        if record.intent_hash.lower() != intent.intent_hash().lower(): raise ValueError("transaction intent mismatch")
        if (record.sender.lower(), record.nonce, record.reservation_id) != (bound_nonce.sender.lower(), bound_nonce.nonce, bound_nonce.reservation_id): raise ValueError("transaction nonce binding mismatch")
        payload = record.canonical()
        with self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                nrow = db.execute("SELECT status,intent_hash,reservation_id FROM nonce_records WHERE sender=? AND nonce=?", (record.sender.lower(), record.nonce)).fetchone()
                if nrow is None or nrow[1].lower() != intent.intent_hash().lower() or nrow[2] != bound_nonce.reservation_id: raise ValueError("durable nonce reservation does not match transaction")
                if nrow[0] != NonceStatus.RESERVED.value: raise ValueError("nonce reservation is not RESERVED")
                db.execute("UPDATE nonce_records SET status=? WHERE sender=? AND nonce=? AND status=?", (NonceStatus.SIGNED.value, record.sender.lower(), record.nonce, NonceStatus.RESERVED.value))
                db.execute("INSERT INTO transaction_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (record.record_hash(), payload["intent_hash"], payload["authorization_hash"], payload["reservation_id"], payload["chain_id"], payload["sender"], payload["executor"], payload["nonce"], payload["calldata_hash"], payload["gas_limit"], payload["max_fee_per_gas"], payload["max_priority_fee_per_gas"], payload["tx_hash"], payload["state"], payload["replacement_of"]))
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction: db.execute("ROLLBACK")
                raise
        return self.get_transaction(record.record_hash())

    def get_transaction(self, record_hash: str) -> TransactionRecord:
        with self._connect() as db:
            row = db.execute("SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of FROM transaction_records WHERE record_hash=?", (record_hash.lower(),)).fetchone()
        if row is None: raise KeyError("unknown transaction record")
        record = self._record_from_row(row)
        if record.record_hash().lower() != record_hash.lower(): raise ValueError("stored transaction identity mismatch")
        return record

    def persist_signed_replacement(
        self,
        *,
        source_record_hash: str,
        replacement_record: TransactionRecord,
        replacement_nonce: DurableNonceRecord,
    ) -> TransactionRecord:
        """Atomically mark a replaceable source as REPLACED and install its signed successor.

        This is a dedicated transition because replacing a DROPPED/REPLACED
        transaction intentionally resets the active nonce lifecycle to SIGNED;
        that cross-state move is not part of the ordinary linear transition map.
        """
        if replacement_record.state is not ExecutionState.SIGNED:
            raise ValueError("replacement transaction must start SIGNED")
        if not _TX_HASH.fullmatch(replacement_record.tx_hash):
            raise ValueError("invalid replacement transaction hash")
        if not _TX_HASH.fullmatch(source_record_hash):
            raise ValueError("invalid source record hash")
        if replacement_record.replacement_of is None or not _TX_HASH.fullmatch(replacement_record.replacement_of):
            raise ValueError("replacement source transaction hash is required")

        source_record_hash = source_record_hash.lower()
        replacement_of = replacement_record.replacement_of.lower()
        if replacement_record.tx_hash.lower() == replacement_of:
            raise ValueError("replacement transaction hash must differ from source")

        with self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of FROM transaction_records WHERE record_hash=?",
                    (source_record_hash,),
                ).fetchone()
                if row is None:
                    raise KeyError("unknown source transaction record")
                source = self._record_from_row(row)
                if source.state not in {ExecutionState.DROPPED, ExecutionState.REPLACED}:
                    raise ValueError("source transaction is not in a replaceable durable state")
                if source.tx_hash.lower() != replacement_of:
                    raise ValueError("replacement source hash does not match source record")
                if source.intent_hash.lower() != replacement_record.intent_hash.lower():
                    raise ValueError("replacement intent does not match source")
                if source.sender.lower() != replacement_record.sender.lower() or source.executor.lower() != replacement_record.executor.lower():
                    raise ValueError("replacement identity does not match source")
                if source.nonce != replacement_record.nonce or source.reservation_id != replacement_record.reservation_id:
                    raise ValueError("replacement nonce binding does not match source")

                nrow = db.execute(
                    "SELECT sender,nonce,reservation_id,intent_hash,status,tx_hash,replacement_of FROM nonce_records WHERE sender=? AND nonce=?",
                    (replacement_nonce.sender.lower(), replacement_nonce.nonce),
                ).fetchone()
                if nrow is None:
                    raise ValueError("replacement durable nonce does not exist")
                if nrow[2] != source.reservation_id or nrow[3].lower() != source.intent_hash.lower():
                    raise ValueError("replacement durable nonce binding does not match source")
                current_nonce = NonceStatus(nrow[4])
                if current_nonce not in {NonceStatus.DROPPED, NonceStatus.REPLACED}:
                    raise ValueError("replacement durable nonce is not in a replaceable state")
                if nrow[5] is not None and nrow[5].lower() != source.tx_hash.lower():
                    raise ValueError("replacement durable nonce active hash does not match source")

                replacement_payload = replacement_record.canonical()
                db.execute(
                    "INSERT INTO transaction_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        replacement_record.record_hash(),
                        replacement_payload["intent_hash"],
                        replacement_payload["authorization_hash"],
                        replacement_payload["reservation_id"],
                        replacement_payload["chain_id"],
                        replacement_payload["sender"],
                        replacement_payload["executor"],
                        replacement_payload["nonce"],
                        replacement_payload["calldata_hash"],
                        replacement_payload["gas_limit"],
                        replacement_payload["max_fee_per_gas"],
                        replacement_payload["max_priority_fee_per_gas"],
                        replacement_payload["tx_hash"],
                        replacement_payload["state"],
                        replacement_payload["replacement_of"],
                    ),
                )
                db.execute(
                    "UPDATE transaction_records SET state=? WHERE record_hash=? AND state IN (?,?)",
                    (ExecutionState.REPLACED.value, source_record_hash, ExecutionState.DROPPED.value, ExecutionState.REPLACED.value),
                )
                db.execute(
                    "UPDATE nonce_records SET status=?,tx_hash=?,replacement_of=? WHERE sender=? AND nonce=? AND status IN (?,?)",
                    (
                        NonceStatus.SIGNED.value,
                        replacement_record.tx_hash.lower(),
                        source.tx_hash.lower(),
                        source.sender.lower(),
                        source.nonce,
                        NonceStatus.DROPPED.value,
                        NonceStatus.REPLACED.value,
                    ),
                )
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction: db.execute("ROLLBACK")
                raise
        return self.get_transaction(replacement_record.record_hash())

    def apply_recovery(self, *, decision: RecoveryDecision, chain_state: str, tx_hash: str, replacement_tx_hash: str | None, transaction_state: ExecutionState, nonce_state: NonceStatus, intent: ExecutionIntent) -> RecoveryApplication:
        """Journal evidence and update transaction + nonce state in one commit."""
        tx_hash = tx_hash.lower()
        with self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                existing = db.execute("SELECT sequence,applied FROM recovery_journal WHERE record_hash=? AND tx_hash=? AND action=?", (decision.record_hash.lower(), tx_hash, decision.action.value)).fetchone()
                if existing is not None:
                    row = db.execute("SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of FROM transaction_records WHERE record_hash=?", (decision.record_hash.lower(),)).fetchone()
                    if row is None: raise KeyError("journal references missing transaction")
                    record = self._record_from_row(row)
                    nrow = db.execute("SELECT sender,nonce,reservation_id,intent_hash,status,tx_hash,replacement_of FROM nonce_records WHERE sender=? AND nonce=?", (record.sender, record.nonce)).fetchone()
                    if nrow is None: raise KeyError("journal references missing nonce")
                    nonce = DurableNonceRecord(sender=nrow[0], nonce=int(nrow[1]), reservation_id=nrow[2], intent_hash=nrow[3], status=NonceStatus(nrow[4]), tx_hash=nrow[5], replacement_of=nrow[6])
                    db.execute("COMMIT")
                    return RecoveryApplication(int(existing[0]), record, nonce)
                row = db.execute("SELECT record_hash,intent_hash,sender,nonce,state,tx_hash FROM transaction_records WHERE record_hash=?", (decision.record_hash.lower(),)).fetchone()
                if row is None: raise KeyError("unknown transaction record")
                if row[1].lower() != intent.intent_hash().lower() or row[5].lower() != tx_hash: raise ValueError("recovery transaction binding mismatch")
                current_tx = ExecutionState(row[4])
                if transaction_state not in _TX_TRANSITIONS[current_tx]: raise ValueError(f"invalid transaction transition: {current_tx} -> {transaction_state}")
                nrow = db.execute("SELECT status,reservation_id,intent_hash,tx_hash FROM nonce_records WHERE sender=? AND nonce=?", (row[2], int(row[3]))).fetchone()
                if nrow is None or nrow[2].lower() != intent.intent_hash().lower(): raise ValueError("recovery nonce binding mismatch")
                current_nonce = NonceStatus(nrow[0])
                if nonce_state not in _NONCE_TRANSITIONS[current_nonce]: raise ValueError(f"invalid nonce transition: {current_nonce} -> {nonce_state}")
                db.execute("INSERT INTO recovery_journal(record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason) VALUES(?,?,?,?,?,?)", (decision.record_hash.lower(), decision.action.value, chain_state, tx_hash, replacement_tx_hash.lower() if replacement_tx_hash else None, decision.reason))
                sequence = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])
                db.execute("UPDATE transaction_records SET state=? WHERE record_hash=? AND state=?", (transaction_state.value, decision.record_hash.lower(), current_tx.value))
                db.execute("UPDATE nonce_records SET status=? WHERE sender=? AND nonce=? AND status=?", (nonce_state.value, row[2], int(row[3]), current_nonce.value))
                db.execute("UPDATE recovery_journal SET applied=1 WHERE sequence=?", (sequence,))
                db.execute("COMMIT")
            except Exception:
                if db.in_transaction: db.execute("ROLLBACK")
                raise
        return RecoveryApplication(sequence, self.get_transaction(decision.record_hash), self.get_nonce(row[2], int(row[3])))

    def pending_journal(self) -> list[tuple[int, str, str]]:
        with self._connect() as db:
            rows = db.execute("SELECT sequence,record_hash,action FROM recovery_journal WHERE applied=0 ORDER BY sequence").fetchall()
        return [(int(r[0]), str(r[1]), str(r[2])) for r in rows]
