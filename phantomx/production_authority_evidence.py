"""Replay-resistant verification helpers for production authority evidence."""
from __future__ import annotations

from dataclasses import dataclass

from .executor_authority import (
    ExecutorAuthorityEvidence,
    verify_executor_authority,
    verify_executor_authority_freshness,
)


class ProductionAuthorityEvidenceError(ValueError):
    """Raised when production authority evidence cannot be safely reused."""


@dataclass(frozen=True)
class AuthorityEvidenceReusePolicy:
    """Explicit policy for how long an authority observation may be reused."""

    maximum_age_blocks: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.maximum_age_blocks, int)
            or isinstance(self.maximum_age_blocks, bool)
            or self.maximum_age_blocks <= 0
        ):
            raise ProductionAuthorityEvidenceError("maximum authority evidence age must be a positive integer")


def verify_reusable_production_authority_evidence(
    evidence: ExecutorAuthorityEvidence,
    *,
    expected_executor: str,
    expected_signer: str,
    current_observed_block: int,
    policy: AuthorityEvidenceReusePolicy,
    minimum_observed_block: int = 0,
) -> None:
    """Require exact authority binding, freshness, and an optional lower block bound."""
    try:
        verify_executor_authority(
            evidence,
            chain_id=137,
            executor=expected_executor,
            sender=expected_signer,
            minimum_observed_block=minimum_observed_block,
        )
        verify_executor_authority_freshness(
            evidence,
            current_observed_block=current_observed_block,
            maximum_age_blocks=policy.maximum_age_blocks,
        )
    except Exception as exc:
        raise ProductionAuthorityEvidenceError("production authority evidence reuse blocked") from exc
