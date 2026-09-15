"""Deterministic replacement-fee policy for Phase 19.

Replacement is a new authorization decision, never an implicit permission to
raise fees. The policy is deliberately independent of RPC/signing/broadcast.
"""

from __future__ import annotations

from dataclasses import dataclass
import json

from .hashing import keccak256_hex


class ReplacementPolicyError(ValueError):
    """Raised when a replacement fee request violates policy."""


@dataclass(frozen=True)
class ReplacementFeePolicy:
    """Bounded EIP-1559 replacement policy.

    ``max_absolute_fee_per_gas`` is a hard ceiling. ``max_fee_multiplier_bps``
    bounds escalation relative to the replaced transaction. The priority fee
    has its own absolute ceiling and cannot exceed max fee.
    """

    max_fee_multiplier_bps: int = 12500
    max_absolute_fee_per_gas: int = 0
    max_priority_fee_per_gas: int = 0
    min_bump_bps: int = 11000

    def __post_init__(self) -> None:
        if self.max_fee_multiplier_bps < 10000:
            raise ValueError("max_fee_multiplier_bps must be >= 10000")
        if self.min_bump_bps < 10000 or self.min_bump_bps > self.max_fee_multiplier_bps:
            raise ValueError("min_bump_bps must be within the allowed multiplier")
        if self.max_absolute_fee_per_gas <= 0 or self.max_priority_fee_per_gas < 0:
            raise ValueError("absolute fee bounds must be configured")

    def canonical(self) -> dict[str, int]:
        return {
            "max_fee_multiplier_bps": self.max_fee_multiplier_bps,
            "max_absolute_fee_per_gas": self.max_absolute_fee_per_gas,
            "max_priority_fee_per_gas": self.max_priority_fee_per_gas,
            "min_bump_bps": self.min_bump_bps,
        }

    def policy_hash(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return keccak256_hex(payload)

    def authorize(self, old_max_fee: int, old_priority_fee: int, new_max_fee: int, new_priority_fee: int) -> None:
        if old_max_fee <= 0 or old_priority_fee < 0 or old_priority_fee > old_max_fee:
            raise ReplacementPolicyError("invalid original EIP-1559 fee envelope")
        if new_max_fee <= 0 or new_priority_fee < 0 or new_priority_fee > new_max_fee:
            raise ReplacementPolicyError("invalid replacement EIP-1559 fee envelope")
        if new_max_fee > self.max_absolute_fee_per_gas:
            raise ReplacementPolicyError("replacement max fee exceeds absolute policy ceiling")
        if new_priority_fee > self.max_priority_fee_per_gas:
            raise ReplacementPolicyError("replacement priority fee exceeds absolute policy ceiling")

        required_max = (old_max_fee * self.min_bump_bps + 9999) // 10000
        allowed_max = (old_max_fee * self.max_fee_multiplier_bps) // 10000
        if new_max_fee < required_max:
            raise ReplacementPolicyError("replacement max fee does not meet minimum bump")
        if new_max_fee > allowed_max:
            raise ReplacementPolicyError("replacement max fee exceeds relative escalation bound")

        required_priority = (old_priority_fee * self.min_bump_bps + 9999) // 10000
        if new_priority_fee < required_priority:
            raise ReplacementPolicyError("replacement priority fee does not meet minimum bump")


@dataclass(frozen=True)
class ReplacementAuthorization:
    """Immutable authorization fingerprint for one replacement decision."""

    original_tx_hash: str
    replacement_tx_hash: str
    intent_hash: str
    authorization_hash: str
    nonce: int
    old_max_fee_per_gas: int
    old_max_priority_fee_per_gas: int
    new_max_fee_per_gas: int
    new_max_priority_fee_per_gas: int
    policy_hash: str

    def validate(self, *, policy: ReplacementFeePolicy) -> None:
        if self.original_tx_hash.lower() == self.replacement_tx_hash.lower():
            raise ReplacementPolicyError("replacement transaction must have a new hash")
        if self.nonce < 0:
            raise ReplacementPolicyError("replacement nonce must be non-negative")
        if not self.intent_hash or not self.authorization_hash or not self.policy_hash:
            raise ReplacementPolicyError("replacement authorization is incompletely bound")
        if self.policy_hash.lower() != policy.policy_hash().lower():
            raise ReplacementPolicyError("replacement authorization policy hash does not match policy")
        policy.authorize(
            self.old_max_fee_per_gas,
            self.old_max_priority_fee_per_gas,
            self.new_max_fee_per_gas,
            self.new_max_priority_fee_per_gas,
        )
