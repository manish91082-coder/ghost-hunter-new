"""Durable binding of chain observation evidence to Phase-19 execution state."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .chain_observer import ChainObservationState, ObservationDecision
from .execution import ExecutionIntent, ExecutionState
from .hashing import keccak256_hex
from .production_chain_observation import QuorumChainObservation
from .production_chain_observation_store import require_quorum_chain_observation
from .sqlite_execution_store import SQLiteExecutionStore
from .durable_nonce import NonceStatus

_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


class ExecutionObservationError(ValueError):
    """Raised when chain evidence cannot be durably bound to an execution."""


@dataclass(frozen=True)
class PersistedObservation:
    sequence: int
    transaction_record_hash: str
    observation: ObservationDecision
    transaction_state: ExecutionState
    nonce_state: NonceStatus
    evidence_hash: str


def _ensure_schema(store: SQLiteExecutionStore) -> None:
    with store._connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS chain_observations(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_record_hash TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                replacement_tx_hash TEXT,
                evidence_reason TEXT NOT NULL,
                sequence_tx_nonce INTEGER NOT NULL,
                pending_nonce INTEGER,
                block_hash TEXT,
                block_number INTEGER,
                canonical_block_hash TEXT,
                evidence_hash TEXT NOT NULL,
                UNIQUE(transaction_record_hash,tx_hash,state,evidence_hash)
            )"""
        )


def persist_chain_observation(
    *,
    store: SQLiteExecutionStore,
    intent: ExecutionIntent,
    observation: ObservationDecision,
    tx_nonce: int,
    pending_nonce: int | None = None,
    block_hash: str | None = None,
    block_number: int | None = None,
    canonical_block_hash: str | None = None,
) -> PersistedObservation:
    """Persist one safe observation and advance only evidence-proven lifecycle state.

    PENDING leaves the durable nonce SUBMITTED unless the execution was
    previously REORGED, in which case canonical re-observation restores
    SUBMITTED. INCLUDED advances the nonce to INCLUDED. A reverted receipt
    terminates the execution as PROFIT_FAILED and advances the nonce to
    INCLUDED. A transaction left in SUBMISSION_IN_FLIGHT by an uncertain relay
    outcome follows the same observation rules, but it can never be restored to
    SIGNED by chain observation. A SIGNED nonce is therefore accepted only while
    the transaction itself is SUBMISSION_IN_FLIGHT and is immediately advanced
    to the evidence-proven submitted/included terminal lifecycle.
    Drop, replacement and reorg evidence use the dedicated recovery adapter.
    """
    _ensure_schema(store)
    if not _TX_HASH.fullmatch(observation.tx_hash):
        raise ExecutionObservationError("invalid transaction hash")
    if tx_nonce < 0 or (pending_nonce is not None and pending_nonce < 0):
        raise ExecutionObservationError("invalid nonce evidence")
    if observation.state is ChainObservationState.INCLUDED and (not block_hash or not canonical_block_hash or block_hash.lower() != canonical_block_hash.lower()):
        raise ExecutionObservationError("INCLUDED observation requires matching canonical block identity")
    if observation.state is ChainObservationState.REVERTED and (not block_hash or not canonical_block_hash or block_hash.lower() != canonical_block_hash.lower()):
        raise ExecutionObservationError("REVERTED observation requires matching canonical block identity")

    payload = {
        "tx_hash": observation.tx_hash.lower(),
        "state": observation.state.value,
        "replacement_tx_hash": observation.replacement_tx_hash.lower() if observation.replacement_tx_hash else None,
        "evidence_reason": observation.evidence_reason,
        "tx_nonce": tx_nonce,
        "pending_nonce": pending_nonce,
        "block_hash": block_hash.lower() if block_hash else None,
        "block_number": block_number,
        "canonical_block_hash": canonical_block_hash.lower() if canonical_block_hash else None,
    }
    evidence_hash = keccak256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())

    with store._connect() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record_hash,intent_hash,tx_hash,state,sender,nonce FROM transaction_records WHERE intent_hash=?",
                (intent.intent_hash().lower(),),
            ).fetchone()
            if row is None:
                raise ExecutionObservationError("unknown durable transaction for execution intent")
            if row[2].lower() != observation.tx_hash.lower():
                raise ExecutionObservationError("observed tx hash does not match durable transaction")
            if int(row[5]) != tx_nonce:
                raise ExecutionObservationError("observed nonce does not match durable transaction")
            tx_state = ExecutionState(row[3])
            nrow = db.execute("SELECT status,intent_hash FROM nonce_records WHERE sender=? AND nonce=?", (row[4], int(row[5]))).fetchone()
            if nrow is None or nrow[1].lower() != intent.intent_hash().lower():
                raise ExecutionObservationError("durable nonce binding is missing")
            nonce_state = NonceStatus(nrow[0])

            in_flight_signed_nonce = tx_state is ExecutionState.SUBMISSION_IN_FLIGHT and nonce_state is NonceStatus.SIGNED

            if observation.state is ChainObservationState.PENDING:
                allowed_nonce = {NonceStatus.SUBMITTED, NonceStatus.REORGED}
                if in_flight_signed_nonce:
                    allowed_nonce.add(NonceStatus.SIGNED)
                if tx_state not in {ExecutionState.PRIVATE_SUBMITTED, ExecutionState.SUBMISSION_IN_FLIGHT, ExecutionState.PENDING, ExecutionState.REORGED} or nonce_state not in allowed_nonce:
                    raise ExecutionObservationError("PENDING evidence conflicts with durable lifecycle")
                target_tx, target_nonce = ExecutionState.PENDING, NonceStatus.SUBMITTED
            elif observation.state is ChainObservationState.INCLUDED:
                allowed_nonce = {NonceStatus.SUBMITTED, NonceStatus.INCLUDED, NonceStatus.REORGED}
                if in_flight_signed_nonce:
                    allowed_nonce.add(NonceStatus.SIGNED)
                if tx_state not in {ExecutionState.PRIVATE_SUBMITTED, ExecutionState.SUBMISSION_IN_FLIGHT, ExecutionState.PENDING, ExecutionState.INCLUDED, ExecutionState.REORGED} or nonce_state not in allowed_nonce:
                    raise ExecutionObservationError("INCLUDED evidence conflicts with durable lifecycle")
                target_tx, target_nonce = ExecutionState.INCLUDED, NonceStatus.INCLUDED
            elif observation.state is ChainObservationState.REVERTED:
                allowed_nonce = {NonceStatus.SUBMITTED, NonceStatus.INCLUDED, NonceStatus.REORGED}
                if in_flight_signed_nonce:
                    allowed_nonce.add(NonceStatus.SIGNED)
                if tx_state not in {ExecutionState.PRIVATE_SUBMITTED, ExecutionState.SUBMISSION_IN_FLIGHT, ExecutionState.PENDING, ExecutionState.INCLUDED, ExecutionState.REORGED} or nonce_state not in allowed_nonce:
                    raise ExecutionObservationError("REVERTED evidence conflicts with durable lifecycle")
                target_tx, target_nonce = ExecutionState.PROFIT_FAILED, NonceStatus.INCLUDED
            else:
                raise ExecutionObservationError(f"observation state {observation.state.value} requires a dedicated recovery path")

            existing = db.execute("SELECT sequence FROM chain_observations WHERE transaction_record_hash=? AND tx_hash=? AND state=? AND evidence_hash=?", (row[0].lower(), observation.tx_hash.lower(), observation.state.value, evidence_hash)).fetchone()
            if existing is not None:
                db.execute("COMMIT")
                return PersistedObservation(int(existing[0]), row[0], observation, target_tx, target_nonce, evidence_hash)

            db.execute(
                "INSERT INTO chain_observations(transaction_record_hash,tx_hash,state,replacement_tx_hash,evidence_reason,sequence_tx_nonce,pending_nonce,block_hash,block_number,canonical_block_hash,evidence_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (row[0].lower(), observation.tx_hash.lower(), observation.state.value, observation.replacement_tx_hash.lower() if observation.replacement_tx_hash else None, observation.evidence_reason, tx_nonce, pending_nonce, block_hash.lower() if block_hash else None, block_number, canonical_block_hash.lower() if canonical_block_hash else None, evidence_hash),
            )
            sequence = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])
            db.execute("UPDATE transaction_records SET state=? WHERE record_hash=?", (target_tx.value, row[0].lower()))
            if nonce_state is not target_nonce:
                db.execute("UPDATE nonce_records SET status=? WHERE sender=? AND nonce=?", (target_nonce.value, row[4], int(row[5])))
            db.execute("COMMIT")
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise

    return PersistedObservation(sequence, row[0], observation, target_tx, target_nonce, evidence_hash)


def persist_quorum_chain_observation(
    *,
    store: SQLiteExecutionStore,
    intent: ExecutionIntent,
    quorum_observation: QuorumChainObservation,
    observation: ObservationDecision,
    tx_nonce: int,
    current_observed_block: int,
    maximum_age_blocks: int,
    minimum_attesting_providers: int = 1,
    pending_nonce: int | None = None,
    block_hash: str | None = None,
    block_number: int | None = None,
    canonical_block_hash: str | None = None,
) -> PersistedObservation:
    """Admit only a durable, fresh quorum observation before lifecycle mutation.

    The supplied full chain evidence remains the source for canonical block
    validation and hashing. The quorum admission record is an independent,
    exact/fresh gate proving that the recovery observation originated from
    persisted provider quorum evidence.
    """
    if not isinstance(quorum_observation, QuorumChainObservation):
        raise ExecutionObservationError("quorum observation is required")
    if observation.tx_hash.lower() != quorum_observation.tx_hash.lower():
        raise ExecutionObservationError("quorum observation transaction hash mismatch")
    if observation.state is not quorum_observation.decision.state:
        raise ExecutionObservationError("quorum observation state mismatch")
    if (observation.replacement_tx_hash or None) != (quorum_observation.decision.replacement_tx_hash or None):
        raise ExecutionObservationError("quorum observation replacement binding mismatch")

    require_quorum_chain_observation(
        store=store,
        intent_hash=intent.intent_hash(),
        observation=quorum_observation,
        current_observed_block=current_observed_block,
        maximum_age_blocks=maximum_age_blocks,
        minimum_attesting_providers=minimum_attesting_providers,
    )
    return persist_chain_observation(
        store=store,
        intent=intent,
        observation=observation,
        tx_nonce=tx_nonce,
        pending_nonce=pending_nonce,
        block_hash=block_hash,
        block_number=block_number,
        canonical_block_hash=canonical_block_hash,
    )
