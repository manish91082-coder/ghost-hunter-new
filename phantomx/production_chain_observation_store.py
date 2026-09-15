"""Durable storage and admission checks for quorum-backed Polygon observations."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .chain_observer import ChainObservationState
from .production_chain_observation import QuorumChainObservation
from .sqlite_execution_store import SQLiteExecutionStore

_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


class ProductionChainObservationStoreError(ValueError):
    """Raised when quorum observation evidence cannot be durably admitted."""


@dataclass(frozen=True)
class PersistedQuorumChainObservation:
    sequence: int
    intent_hash: str
    tx_hash: str
    state: ChainObservationState
    chain_id: int
    common_observed_block: int
    attesting_provider_names: tuple[str, ...]
    evidence_hash: str


def _ensure_schema(store: SQLiteExecutionStore) -> None:
    with store._connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS quorum_chain_observations(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                intent_hash TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                chain_id INTEGER NOT NULL,
                common_observed_block INTEGER NOT NULL,
                attesting_provider_names TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                UNIQUE(intent_hash,tx_hash,evidence_hash)
            )"""
        )


def _validate_hex(value: str, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ProductionChainObservationStoreError(f"{field} must be a 32-byte 0x hash")
    return value.lower()


def persist_quorum_chain_observation(
    *,
    store: SQLiteExecutionStore,
    intent_hash: str,
    observation: QuorumChainObservation,
) -> PersistedQuorumChainObservation:
    """Atomically retain one quorum observation and its attester provenance."""
    _ensure_schema(store)
    intent_hash = _validate_hex(intent_hash, "intent hash")
    if not isinstance(observation, QuorumChainObservation):
        raise ProductionChainObservationStoreError("observation must be QuorumChainObservation")
    if observation.chain_id != 137:
        raise ProductionChainObservationStoreError("production observation is Polygon-only")
    if _validate_hex(observation.tx_hash, "transaction hash") != observation.decision.tx_hash.lower():
        raise ProductionChainObservationStoreError("transaction hash does not match decision")
    if observation.common_observed_block < 0:
        raise ProductionChainObservationStoreError("common observed block must be non-negative")
    names = tuple(observation.attesting_provider_names)
    if not names or len(set(names)) != len(names):
        raise ProductionChainObservationStoreError("attesting provider names must be unique and non-empty")
    with store._connect() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT sequence FROM quorum_chain_observations WHERE intent_hash=? AND tx_hash=? AND evidence_hash=?",
            (intent_hash, observation.tx_hash.lower(), observation.evidence_hash.lower()),
        ).fetchone()
        if existing is None:
            db.execute(
                "INSERT INTO quorum_chain_observations(intent_hash,tx_hash,state,chain_id,common_observed_block,attesting_provider_names,evidence_hash) VALUES(?,?,?,?,?,?,?)",
                (
                    intent_hash,
                    observation.tx_hash.lower(),
                    observation.decision.state.value,
                    observation.chain_id,
                    observation.common_observed_block,
                    json.dumps(list(names), separators=(",", ":")),
                    observation.evidence_hash.lower(),
                ),
            )
            sequence = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        else:
            sequence = int(existing[0])
        db.execute("COMMIT")
    return PersistedQuorumChainObservation(
        sequence=sequence,
        intent_hash=intent_hash,
        tx_hash=observation.tx_hash.lower(),
        state=observation.decision.state,
        chain_id=observation.chain_id,
        common_observed_block=observation.common_observed_block,
        attesting_provider_names=names,
        evidence_hash=observation.evidence_hash.lower(),
    )


def require_quorum_chain_observation(
    *,
    store: SQLiteExecutionStore,
    intent_hash: str,
    observation: QuorumChainObservation,
    current_observed_block: int,
    maximum_age_blocks: int,
    minimum_attesting_providers: int = 1,
) -> PersistedQuorumChainObservation:
    """Require an exact, fresh, previously persisted quorum observation."""
    if current_observed_block < 0:
        raise ProductionChainObservationStoreError("current observed block must be non-negative")
    if maximum_age_blocks <= 0:
        raise ProductionChainObservationStoreError("maximum age must be positive")
    if minimum_attesting_providers <= 0:
        raise ProductionChainObservationStoreError("minimum attesting providers must be positive")
    intent_hash = _validate_hex(intent_hash, "intent hash")
    _ensure_schema(store)
    with store._connect() as db:
        row = db.execute(
            "SELECT sequence,tx_hash,state,chain_id,common_observed_block,attesting_provider_names,evidence_hash FROM quorum_chain_observations WHERE intent_hash=? AND tx_hash=? AND evidence_hash=?",
            (intent_hash, observation.tx_hash.lower(), observation.evidence_hash.lower()),
        ).fetchone()
    if row is None:
        raise ProductionChainObservationStoreError("quorum observation is not durably persisted")
    names = tuple(json.loads(row[5]))
    if row[2] != observation.decision.state.value or row[3] != observation.chain_id or row[4] != observation.common_observed_block or names != tuple(observation.attesting_provider_names):
        raise ProductionChainObservationStoreError("persisted quorum observation does not exactly match supplied evidence")
    if len(names) < minimum_attesting_providers:
        raise ProductionChainObservationStoreError("quorum attester count is below policy")
    if current_observed_block < observation.common_observed_block:
        raise ProductionChainObservationStoreError("quorum observation is future-dated")
    if current_observed_block - observation.common_observed_block > maximum_age_blocks:
        raise ProductionChainObservationStoreError("quorum observation is stale")
    return PersistedQuorumChainObservation(
        sequence=int(row[0]),
        intent_hash=intent_hash,
        tx_hash=row[1].lower(),
        state=observation.decision.state,
        chain_id=int(row[3]),
        common_observed_block=int(row[4]),
        attesting_provider_names=names,
        evidence_hash=row[6].lower(),
    )
