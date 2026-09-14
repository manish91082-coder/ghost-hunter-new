"""Startup recovery audit for the unified Phase-19 execution store.

This module deliberately audits and reports. It does not guess that an absent
transaction was dropped, does not sign, replace, submit, or broadcast anything.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .durable_nonce import NonceStatus
from .execution import ExecutionState
from .sqlite_execution_store import SQLiteExecutionStore


class RecoveryAuditState(str, Enum):
    CLEAN = "CLEAN"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True)
class RecoveryAudit:
    state: RecoveryAuditState
    checked_transactions: int
    checked_nonces: int
    pending_journal_entries: int
    anomalies: tuple[str, ...]


def audit_store(store: SQLiteExecutionStore) -> RecoveryAudit:
    """Audit cross-table invariants after process restart.

    SIGNED is a legitimate pre-submission state: its durable transaction row
    already carries the transaction hash, while the nonce row may intentionally
    remain hash-free until submission. SUBMITTED/INCLUDED require the nonce row
    to carry the active transaction hash.
    """
    anomalies: list[str] = []
    with store._connect() as db:
        tx_rows = db.execute(
            "SELECT record_hash,intent_hash,reservation_id,sender,nonce,tx_hash,state "
            "FROM transaction_records ORDER BY record_hash"
        ).fetchall()
        nonce_rows = db.execute(
            "SELECT sender,nonce,reservation_id,intent_hash,status,tx_hash,replacement_of "
            "FROM nonce_records ORDER BY sender,nonce"
        ).fetchall()
        pending_journal = int(db.execute("SELECT COUNT(*) FROM recovery_journal WHERE applied=0").fetchone()[0])

        for record_hash, intent_hash, reservation_id, sender, nonce, tx_hash, state in tx_rows:
            nrow = db.execute(
                "SELECT reservation_id,intent_hash,status,tx_hash FROM nonce_records WHERE sender=? AND nonce=?",
                (sender, nonce),
            ).fetchone()
            if nrow is None:
                anomalies.append(f"transaction {record_hash}: missing nonce record")
                continue
            if nrow[0] != reservation_id:
                anomalies.append(f"transaction {record_hash}: reservation mismatch")
            if nrow[1].lower() != intent_hash.lower():
                anomalies.append(f"transaction {record_hash}: intent mismatch")
            if nrow[3] is not None and nrow[3].lower() != tx_hash.lower():
                anomalies.append(f"transaction {record_hash}: nonce tx hash mismatch")
            expected = {
                ExecutionState.SIGNED.value: NonceStatus.SIGNED.value,
                ExecutionState.PRIVATE_SUBMITTED.value: NonceStatus.SUBMITTED.value,
                ExecutionState.PENDING.value: NonceStatus.SUBMITTED.value,
                ExecutionState.INCLUDED.value: NonceStatus.INCLUDED.value,
            }.get(state)
            if expected is not None and nrow[2] != expected:
                anomalies.append(f"transaction {record_hash}: lifecycle mismatch {state}/{nrow[2]}")

        for sender, nonce, reservation_id, intent_hash, status, tx_hash, replacement_of in nonce_rows:
            if status in {NonceStatus.SUBMITTED.value, NonceStatus.INCLUDED.value} and not tx_hash:
                anomalies.append(f"nonce {sender}:{nonce}: active submitted state without tx hash")
            if replacement_of and not tx_hash:
                anomalies.append(f"nonce {sender}:{nonce}: replacement linkage without active tx hash")
            tx = db.execute(
                "SELECT reservation_id,intent_hash,sender,nonce,tx_hash FROM transaction_records WHERE sender=? AND nonce=?",
                (sender, nonce),
            ).fetchall()
            if status != NonceStatus.RELEASED.value and len(tx) == 0:
                anomalies.append(f"nonce {sender}:{nonce}: no transaction record")

    if anomalies:
        state = RecoveryAuditState.INCONSISTENT
    elif pending_journal:
        state = RecoveryAuditState.ACTION_REQUIRED
    else:
        state = RecoveryAuditState.CLEAN
    return RecoveryAudit(state, len(tx_rows), len(nonce_rows), pending_journal, tuple(anomalies))
