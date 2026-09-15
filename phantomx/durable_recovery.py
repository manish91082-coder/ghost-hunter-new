"""Durable recovery-state integration for Phase 19 execution records.

This adapter turns explicit chain-observer recovery evidence into durable
execution and nonce states. It never signs, submits, releases a nonce, or
creates a replacement transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .chain_observer import ChainObservationState, ObservationDecision
from .durable_nonce import NonceStatus
from .execution import ExecutionIntent, ExecutionState
from .hashing import keccak256_hex
from .recovery_coordinator import RecoveryAction, recover
from .sqlite_execution_store import SQLiteExecutionStore

_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


class DurableRecoveryError(ValueError):
    """Raised when recovery evidence cannot be safely persisted."""


@dataclass(frozen=True)
class PersistedRecovery:
    sequence: int
    transaction_record_hash: str
    observation: ObservationDecision
    action: RecoveryAction
    transaction_state: ExecutionState
    nonce_state: NonceStatus
    evidence_hash: str


def _ensure_schema(store: SQLiteExecutionStore) -> None:
    with store._connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS execution_recovery_observations(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_record_hash TEXT NOT NULL,
                action TEXT NOT NULL,
                chain_state TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                replacement_tx_hash TEXT,
                tx_nonce INTEGER NOT NULL,
                pending_nonce INTEGER,
                block_hash TEXT,
                block_number INTEGER,
                canonical_block_hash TEXT,
                reason TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                UNIQUE(transaction_record_hash,tx_hash,action,evidence_hash)
            )"""
        )


def _require_hash(value: str | None, label: str) -> None:
    if value is not None and not _TX_HASH.fullmatch(value):
        raise DurableRecoveryError(f"invalid {label}")


def _tx_transition_allowed(current: ExecutionState, target: ExecutionState) -> bool:
    return target in {
        ExecutionState.SIGNED: {ExecutionState.DROPPED},
        ExecutionState.PRIVATE_SUBMITTED: {ExecutionState.DROPPED, ExecutionState.REPLACED, ExecutionState.PENDING, ExecutionState.PROFIT_FAILED},
        ExecutionState.PENDING: {ExecutionState.DROPPED, ExecutionState.REPLACED, ExecutionState.REORGED, ExecutionState.INCLUDED, ExecutionState.PROFIT_FAILED},
        ExecutionState.INCLUDED: {ExecutionState.REORGED},
        ExecutionState.REORGED: {ExecutionState.PENDING, ExecutionState.DROPPED},
    }.get(current, set())


def _nonce_transition_allowed(current: NonceStatus, target: NonceStatus) -> bool:
    return target in {
        NonceStatus.SIGNED: {NonceStatus.RELEASED, NonceStatus.SUBMITTED, NonceStatus.DROPPED},
        NonceStatus.SUBMITTED: {NonceStatus.INCLUDED, NonceStatus.REPLACED, NonceStatus.DROPPED, NonceStatus.REORGED},
        NonceStatus.INCLUDED: {NonceStatus.REORGED},
        NonceStatus.REORGED: {NonceStatus.SUBMITTED, NonceStatus.DROPPED},
    }.get(current, set())


def persist_recovery_observation(
    *,
    store: SQLiteExecutionStore,
    intent: ExecutionIntent,
    observation: ObservationDecision,
    tx_nonce: int,
    pending_nonce: int | None = None,
    block_hash: str | None = None,
    block_number: int | None = None,
    canonical_block_hash: str | None = None,
) -> PersistedRecovery:
    """Persist DROP, REPLACED or REORGED evidence exactly once per evidence hash."""
    _ensure_schema(store)
    if observation.state not in {
        ChainObservationState.DROPPED,
        ChainObservationState.REPLACED,
        ChainObservationState.REORGED,
    }:
        raise DurableRecoveryError("observation requires dedicated recovery evidence")
    if not _TX_HASH.fullmatch(observation.tx_hash):
        raise DurableRecoveryError("invalid transaction hash")
    _require_hash(observation.replacement_tx_hash, "replacement transaction hash")
    _require_hash(block_hash, "block hash")
    _require_hash(canonical_block_hash, "canonical block hash")
    if tx_nonce < 0 or (pending_nonce is not None and pending_nonce < 0):
        raise DurableRecoveryError("invalid nonce evidence")

    if observation.state is ChainObservationState.DROPPED:
        if pending_nonce is None or pending_nonce <= tx_nonce:
            raise DurableRecoveryError("DROP requires pending nonce advancement")
        if block_hash is not None or canonical_block_hash is not None or block_number is not None:
            raise DurableRecoveryError("DROP cannot carry receipt block evidence")
        action = RecoveryAction.ELIGIBLE_FOR_REPLACEMENT_REVIEW
        target_tx, target_nonce = ExecutionState.DROPPED, NonceStatus.DROPPED
    elif observation.state is ChainObservationState.REPLACED:
        if observation.replacement_tx_hash is None:
            raise DurableRecoveryError("REPLACED requires replacement transaction hash")
        if observation.replacement_tx_hash.lower() == observation.tx_hash.lower():
            raise DurableRecoveryError("replacement transaction must differ from original")
        action = RecoveryAction.REVIEW_REPLACEMENT
        target_tx, target_nonce = ExecutionState.REPLACED, NonceStatus.REPLACED
    else:
        if not block_hash or not canonical_block_hash or block_hash.lower() == canonical_block_hash.lower():
            raise DurableRecoveryError("REORGED requires changed canonical block identity")
        if block_number is None or block_number < 0:
            raise DurableRecoveryError("REORGED requires non-negative block number")
        action = RecoveryAction.REOBSERVE
        target_tx, target_nonce = ExecutionState.REORGED, NonceStatus.REORGED

    payload = {
        "tx_hash": observation.tx_hash.lower(),
        "state": observation.state.value,
        "replacement_tx_hash": observation.replacement_tx_hash.lower() if observation.replacement_tx_hash else None,
        "tx_nonce": tx_nonce,
        "pending_nonce": pending_nonce,
        "block_hash": block_hash.lower() if block_hash else None,
        "block_number": block_number,
        "canonical_block_hash": canonical_block_hash.lower() if canonical_block_hash else None,
        "reason": observation.evidence_reason,
        "action": action.value,
    }
    evidence_hash = keccak256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())

    with store._connect() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record_hash,intent_hash,sender,nonce,state,tx_hash FROM transaction_records WHERE intent_hash=? AND tx_hash=?",
                (intent.intent_hash().lower(), observation.tx_hash.lower()),
            ).fetchone()
            if row is None:
                raise DurableRecoveryError("unknown durable transaction for execution intent and observed transaction hash")
            if int(row[3]) != tx_nonce:
                raise DurableRecoveryError("recovery evidence does not match durable transaction nonce")
            nrow = db.execute(
                "SELECT reservation_id,intent_hash,status,tx_hash FROM nonce_records WHERE sender=? AND nonce=?",
                (row[2], int(row[3])),
            ).fetchone()
            if nrow is None or nrow[1].lower() != intent.intent_hash().lower():
                raise DurableRecoveryError("durable nonce binding is missing")

            existing = db.execute(
                "SELECT sequence FROM execution_recovery_observations WHERE transaction_record_hash=? AND tx_hash=? AND action=? AND evidence_hash=?",
                (row[0].lower(), observation.tx_hash.lower(), action.value, evidence_hash),
            ).fetchone()
            if existing is not None:
                db.execute("COMMIT")
                return PersistedRecovery(
                    int(existing[0]), row[0], observation, action, ExecutionState(row[4]), NonceStatus(nrow[2]), evidence_hash
                )

            current_tx = ExecutionState(row[4])
            current_nonce = NonceStatus(nrow[2])
            valid_current_tx = {
                ChainObservationState.DROPPED: {ExecutionState.SIGNED, ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PENDING},
                ChainObservationState.REPLACED: {ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PENDING},
                ChainObservationState.REORGED: {ExecutionState.PENDING, ExecutionState.INCLUDED, ExecutionState.REORGED},
            }[observation.state]
            valid_current_nonce = {
                ChainObservationState.DROPPED: {NonceStatus.SIGNED, NonceStatus.SUBMITTED},
                ChainObservationState.REPLACED: {NonceStatus.SUBMITTED},
                ChainObservationState.REORGED: {NonceStatus.SUBMITTED, NonceStatus.INCLUDED, NonceStatus.REORGED},
            }[observation.state]
            if current_tx not in valid_current_tx or current_nonce not in valid_current_nonce:
                raise DurableRecoveryError(
                    f"recovery state conflicts with durable lifecycle: {current_tx.value}/{current_nonce.value}"
                )
            if not _tx_transition_allowed(current_tx, target_tx):
                raise DurableRecoveryError(f"invalid transaction recovery transition: {current_tx} -> {target_tx}")
            if not _nonce_transition_allowed(current_nonce, target_nonce):
                raise DurableRecoveryError(f"invalid nonce recovery transition: {current_nonce} -> {target_nonce}")

            db.execute(
                "INSERT INTO execution_recovery_observations(transaction_record_hash,action,chain_state,tx_hash,replacement_tx_hash,tx_nonce,pending_nonce,block_hash,block_number,canonical_block_hash,reason,evidence_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row[0].lower(), action.value, observation.state.value, observation.tx_hash.lower(),
                    observation.replacement_tx_hash.lower() if observation.replacement_tx_hash else None,
                    tx_nonce, pending_nonce, block_hash.lower() if block_hash else None, block_number,
                    canonical_block_hash.lower() if canonical_block_hash else None, observation.evidence_reason, evidence_hash,
                ),
            )
            sequence = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])
            db.execute("UPDATE transaction_records SET state=? WHERE record_hash=? AND state=?", (target_tx.value, row[0].lower(), current_tx.value))
            if observation.state is ChainObservationState.REPLACED:
                db.execute(
                    "UPDATE nonce_records SET status=?,tx_hash=?,replacement_of=? WHERE sender=? AND nonce=? AND status=?",
                    (
                        target_nonce.value,
                        observation.replacement_tx_hash.lower(),
                        observation.tx_hash.lower(),
                        row[2],
                        int(row[3]),
                        current_nonce.value,
                    ),
                )
            else:
                db.execute(
                    "UPDATE nonce_records SET status=? WHERE sender=? AND nonce=? AND status=?",
                    (target_nonce.value, row[2], int(row[3]), current_nonce.value),
                )
            db.execute("COMMIT")
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise

    return PersistedRecovery(sequence, row[0], observation, action, target_tx, target_nonce, evidence_hash)
