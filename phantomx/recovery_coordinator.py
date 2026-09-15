"""Crash/restart recovery coordinator for Phase 19.

The coordinator is deliberately policy-only: it consumes durable records and
chain evidence, then returns an explicit recovery action. It never signs,
submits, releases a nonce, or broadcasts a replacement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .chain_observer import ChainObservationState, ObservationDecision
from .execution import ExecutionState


class RecoveryAction(str, Enum):
    HOLD = "HOLD"
    RECONCILE_INCLUDED = "RECONCILE_INCLUDED"
    MARK_REVERTED = "MARK_REVERTED"
    ELIGIBLE_FOR_REPLACEMENT_REVIEW = "ELIGIBLE_FOR_REPLACEMENT_REVIEW"
    REVIEW_REPLACEMENT = "REVIEW_REPLACEMENT"
    REOBSERVE = "REOBSERVE"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class RecoveryDecision:
    record_hash: str
    action: RecoveryAction
    reason: str


def recover(record_hash: str, execution_state: ExecutionState, observation: ObservationDecision) -> RecoveryDecision:
    """Determine the only safe next recovery action from durable + chain state."""
    state = execution_state
    chain = observation.state

    if state in {ExecutionState.PROFIT_CONFIRMED, ExecutionState.PROFIT_FAILED}:
        return RecoveryDecision(record_hash, RecoveryAction.BLOCK, "terminal transaction record requires no restart action")

    if chain is ChainObservationState.INCLUDED:
        if state not in {ExecutionState.PENDING, ExecutionState.INCLUDED, ExecutionState.RECONCILED}:
            return RecoveryDecision(record_hash, RecoveryAction.BLOCK, "included transaction conflicts with durable lifecycle state")
        return RecoveryDecision(record_hash, RecoveryAction.RECONCILE_INCLUDED, "canonical successful receipt requires settlement reconciliation")

    if chain is ChainObservationState.REVERTED:
        if state not in {ExecutionState.PENDING, ExecutionState.INCLUDED}:
            return RecoveryDecision(record_hash, RecoveryAction.BLOCK, "reverted chain evidence conflicts with durable lifecycle state")
        return RecoveryDecision(record_hash, RecoveryAction.MARK_REVERTED, "receipt proves execution reverted; no replacement is implied")

    if chain is ChainObservationState.REPLACED:
        if observation.replacement_tx_hash is None:
            return RecoveryDecision(record_hash, RecoveryAction.BLOCK, "replacement state lacks replacement transaction hash")
        return RecoveryDecision(record_hash, RecoveryAction.REVIEW_REPLACEMENT, "explicit replacement evidence requires replacement-record reconciliation")

    if chain is ChainObservationState.DROPPED:
        if state not in {ExecutionState.SIGNED, ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PENDING}:
            return RecoveryDecision(record_hash, RecoveryAction.BLOCK, "drop evidence conflicts with durable lifecycle state")
        return RecoveryDecision(record_hash, RecoveryAction.ELIGIBLE_FOR_REPLACEMENT_REVIEW, "nonce advancement proves drop; replacement still requires new authorization")

    if chain is ChainObservationState.REORGED:
        return RecoveryDecision(record_hash, RecoveryAction.REOBSERVE, "reorg evidence requires fresh canonical-chain observation")

    if chain in {ChainObservationState.PENDING, ChainObservationState.NOT_FOUND, ChainObservationState.UNKNOWN}:
        return RecoveryDecision(record_hash, RecoveryAction.HOLD, "chain evidence is insufficient for release or replacement")

    return RecoveryDecision(record_hash, RecoveryAction.BLOCK, "unrecognized recovery state")
