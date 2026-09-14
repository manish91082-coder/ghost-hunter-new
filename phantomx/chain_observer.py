"""Fail-closed chain observation model for transaction recovery.

This module models evidence collection and decisions without making network
calls. A production adapter must supply observations from approved Polygon
RPC providers and preserve the raw evidence used for each decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChainObservationState(str, Enum):
    PENDING = "PENDING"
    INCLUDED = "INCLUDED"
    REVERTED = "REVERTED"
    NOT_FOUND = "NOT_FOUND"
    DROPPED = "DROPPED"
    REPLACED = "REPLACED"
    REORGED = "REORGED"
    UNKNOWN = "UNKNOWN"


class ChainObservationError(ValueError):
    """Raised when supplied chain evidence is contradictory or insufficient."""


@dataclass(frozen=True)
class ChainEvidence:
    tx_hash: str
    tx_nonce: int
    pending_nonce: int | None
    tx_present: bool
    receipt_present: bool
    receipt_status: int | None
    block_hash: str | None
    block_number: int | None
    canonical_block_hash: str | None
    replacement_tx_hash: str | None = None


@dataclass(frozen=True)
class ObservationDecision:
    state: ChainObservationState
    tx_hash: str
    replacement_tx_hash: str | None
    evidence_reason: str


def observe(evidence: ChainEvidence) -> ObservationDecision:
    """Convert one internally consistent chain observation into a state.

    A missing transaction is never treated as dropped. Drop requires the
    sender's pending nonce to have advanced beyond the transaction nonce.
    A reorg requires a previously known block identity to disappear from the
    canonical chain. Receipt status is authoritative for included success vs
    revert.
    """
    if evidence.tx_nonce < 0:
        raise ChainObservationError("negative transaction nonce")
    if evidence.receipt_status not in (None, 0, 1):
        raise ChainObservationError("invalid receipt status")

    if evidence.receipt_present:
        if not evidence.tx_present:
            raise ChainObservationError("receipt cannot be present while transaction evidence is absent")
        if evidence.block_hash is None or evidence.block_number is None:
            raise ChainObservationError("included receipt requires block identity")
        if evidence.receipt_status == 0:
            return ObservationDecision(ChainObservationState.REVERTED, evidence.tx_hash, None, "receipt status is reverted")
        if evidence.canonical_block_hash is None:
            return ObservationDecision(ChainObservationState.UNKNOWN, evidence.tx_hash, None, "canonical block identity unavailable")
        if evidence.block_hash != evidence.canonical_block_hash:
            return ObservationDecision(ChainObservationState.REORGED, evidence.tx_hash, None, "receipt block is no longer canonical")
        if evidence.replacement_tx_hash:
            raise ChainObservationError("replacement hash cannot accompany an included receipt")
        return ObservationDecision(ChainObservationState.INCLUDED, evidence.tx_hash, None, "canonical successful receipt")

    if evidence.replacement_tx_hash:
        if not evidence.tx_present:
            raise ChainObservationError("replacement evidence requires replacement transaction presence")
        return ObservationDecision(ChainObservationState.REPLACED, evidence.tx_hash, evidence.replacement_tx_hash, "explicit replacement transaction evidence")

    if evidence.tx_present:
        return ObservationDecision(ChainObservationState.PENDING, evidence.tx_hash, None, "transaction present without receipt")

    if evidence.pending_nonce is None:
        return ObservationDecision(ChainObservationState.NOT_FOUND, evidence.tx_hash, None, "transaction not observed and pending nonce unavailable")

    if evidence.pending_nonce > evidence.tx_nonce:
        return ObservationDecision(ChainObservationState.DROPPED, evidence.tx_hash, None, "pending nonce advanced beyond transaction nonce")

    return ObservationDecision(ChainObservationState.NOT_FOUND, evidence.tx_hash, None, "transaction absent but nonce does not prove drop")
