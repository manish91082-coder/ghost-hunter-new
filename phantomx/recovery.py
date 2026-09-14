"""Deterministic in-flight transaction recovery policy.

The planner converts chain observations into explicit durable-nonce state
transitions. It never guesses that a missing transaction was dropped, and it
never authorizes a replacement without proof that the replacement targets the
currently active transaction for the same nonce.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .durable_nonce import NonceStatus


class RecoveryError(ValueError):
    """Raised when chain evidence is insufficient or contradictory."""


class ChainTxState(str, Enum):
    PENDING = "PENDING"
    INCLUDED_SUCCESS = "INCLUDED_SUCCESS"
    INCLUDED_REVERT = "INCLUDED_REVERT"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ChainTransactionObservation:
    tx_hash: str
    nonce: int
    state: ChainTxState
    block_hash: str | None = None
    receipt_block_hash: str | None = None
    gas_used: int | None = None
    effective_gas_price: int | None = None

    def __post_init__(self) -> None:
        if not self.tx_hash.startswith("0x"):
            raise RecoveryError("transaction hash must be 0x-prefixed")
        if self.nonce < 0:
            raise RecoveryError("transaction nonce cannot be negative")
        if self.state in {ChainTxState.INCLUDED_SUCCESS, ChainTxState.INCLUDED_REVERT}:
            if not self.block_hash or not self.receipt_block_hash:
                raise RecoveryError("included transaction requires block evidence")
            if self.gas_used is None or self.gas_used < 0:
                raise RecoveryError("included transaction requires non-negative gas_used")
            if self.effective_gas_price is None or self.effective_gas_price < 0:
                raise RecoveryError("included transaction requires effective gas price")


@dataclass(frozen=True)
class RecoveryDecision:
    action: str
    reason: str
    next_status: NonceStatus | None = None


def decide(
    *,
    current_status: NonceStatus,
    active_tx_hash: str | None,
    observation: ChainTransactionObservation,
    chain_pending_nonce: int,
) -> RecoveryDecision:
    """Choose a state transition using only explicit chain evidence.

    NOT_FOUND is intentionally non-terminal. A transaction can be temporarily
    absent from a provider's mempool. A nonce being consumed by a different
    transaction is required before classifying the active transaction as
    dropped/replaced.
    """
    if chain_pending_nonce < observation.nonce:
        raise RecoveryError("chain pending nonce cannot trail observed transaction nonce")

    if active_tx_hash is not None and observation.tx_hash.lower() != active_tx_hash.lower():
        raise RecoveryError("observation hash does not match active transaction")

    if observation.state == ChainTxState.UNKNOWN:
        return RecoveryDecision("HOLD", "chain evidence is unknown; do not mutate durable state")

    if observation.state == ChainTxState.PENDING:
        return RecoveryDecision("HOLD", "transaction is still pending")

    if observation.state == ChainTxState.INCLUDED_SUCCESS:
        if current_status not in {NonceStatus.SUBMITTED, NonceStatus.REPLACED, NonceStatus.REORGED}:
            raise RecoveryError(f"cannot mark {current_status.value} as included")
        return RecoveryDecision("MARK_INCLUDED", "receipt proves successful inclusion", NonceStatus.INCLUDED)

    if observation.state == ChainTxState.INCLUDED_REVERT:
        if current_status not in {NonceStatus.SUBMITTED, NonceStatus.REPLACED, NonceStatus.REORGED}:
            raise RecoveryError(f"cannot mark {current_status.value} as dropped")
        return RecoveryDecision("MARK_REVERTED", "receipt proves inclusion with execution revert", NonceStatus.INCLUDED)

    if observation.state == ChainTxState.NOT_FOUND:
        return RecoveryDecision("HOLD", "transaction is not observed; absence alone is not drop proof")

    raise RecoveryError("unhandled chain transaction state")


def prove_dropped(*, active_tx_hash: str, nonce: int, chain_pending_nonce: int, replacement_tx_hash: str | None) -> RecoveryDecision:
    """Require nonce-consumption evidence before a missing transaction is dropped.

    If a replacement hash is supplied, it must be tracked separately by the
    caller and later reconciled against its own receipt. This function only
    establishes that the active nonce has moved past the missing transaction.
    """
    if chain_pending_nonce <= nonce:
        raise RecoveryError("nonce consumption has not been proven")
    if not active_tx_hash.startswith("0x"):
        raise RecoveryError("active transaction hash is invalid")
    if replacement_tx_hash is not None and replacement_tx_hash.lower() == active_tx_hash.lower():
        raise RecoveryError("replacement hash must differ from active transaction")
    reason = "chain pending nonce advanced beyond missing transaction nonce"
    if replacement_tx_hash:
        reason += "; replacement evidence supplied for follow-up reconciliation"
    return RecoveryDecision("MARK_DROPPED", reason, NonceStatus.DROPPED)
