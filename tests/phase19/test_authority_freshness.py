import unittest

from phantomx.executor_authority import (
    ExecutorAuthorityError,
    ExecutorAuthorityEvidence,
    verify_executor_authority_freshness,
)
from phantomx.hashing import keccak256_hex

EXECUTOR = "0x" + "aa" * 20
OWNER = "0x" + "bb" * 20
CODE_HASH = keccak256_hex(b"phase19-authority-runtime")


class AuthorityFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.evidence = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=OWNER,
            observed_block=1000,
            runtime_code_hash=CODE_HASH,
            attesting_provider_names=("rpc-a", "rpc-b"),
        )

    def test_fresh_evidence_is_accepted_at_policy_boundary(self):
        verify_executor_authority_freshness(
            self.evidence,
            current_observed_block=1100,
            maximum_age_blocks=100,
        )

    def test_stale_evidence_is_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "stale"):
            verify_executor_authority_freshness(
                self.evidence,
                current_observed_block=1101,
                maximum_age_blocks=100,
            )

    def test_future_evidence_is_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "future"):
            verify_executor_authority_freshness(
                self.evidence,
                current_observed_block=999,
                maximum_age_blocks=100,
            )

    def test_zero_and_negative_policy_values_are_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "maximum observation age"):
            verify_executor_authority_freshness(
                self.evidence,
                current_observed_block=1000,
                maximum_age_blocks=0,
            )
        with self.assertRaisesRegex(ExecutorAuthorityError, "maximum observation age"):
            verify_executor_authority_freshness(
                self.evidence,
                current_observed_block=1000,
                maximum_age_blocks=-1,
            )

    def test_current_block_must_be_non_negative_integer(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "current observed block"):
            verify_executor_authority_freshness(
                self.evidence,
                current_observed_block=-1,
                maximum_age_blocks=100,
            )
        with self.assertRaisesRegex(ExecutorAuthorityError, "current observed block"):
            verify_executor_authority_freshness(
                self.evidence,
                current_observed_block=True,
                maximum_age_blocks=100,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
