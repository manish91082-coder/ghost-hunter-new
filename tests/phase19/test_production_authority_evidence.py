import unittest

from phantomx.executor_authority import ExecutorAuthorityEvidence
from phantomx.hashing import keccak256_hex
from phantomx.production_authority_evidence import (
    AuthorityEvidenceReusePolicy,
    ProductionAuthorityEvidenceError,
    verify_reusable_production_authority_evidence,
)

EXECUTOR = "0x" + "aa" * 20
SIGNER = "0x" + "bb" * 20
CODE_HASH = keccak256_hex(b"phase19-runtime")


class ProductionAuthorityEvidenceReuseTests(unittest.TestCase):
    def setUp(self):
        self.evidence = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SIGNER,
            observed_block=1000,
            runtime_code_hash=CODE_HASH,
            attesting_provider_names=("rpc-a", "rpc-b"),
        )

    def test_reuse_requires_exact_binding_and_freshness(self):
        verify_reusable_production_authority_evidence(
            self.evidence,
            expected_executor=EXECUTOR,
            expected_signer=SIGNER,
            current_observed_block=1100,
            policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=100),
        )

    def test_stale_reuse_is_blocked(self):
        with self.assertRaises(ProductionAuthorityEvidenceError):
            verify_reusable_production_authority_evidence(
                self.evidence,
                expected_executor=EXECUTOR,
                expected_signer=SIGNER,
                current_observed_block=1101,
                policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=100),
            )

    def test_executor_or_signer_mismatch_is_blocked(self):
        with self.assertRaises(ProductionAuthorityEvidenceError):
            verify_reusable_production_authority_evidence(
                self.evidence,
                expected_executor=SIGNER,
                expected_signer=SIGNER,
                current_observed_block=1000,
                policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=100),
            )
        with self.assertRaises(ProductionAuthorityEvidenceError):
            verify_reusable_production_authority_evidence(
                self.evidence,
                expected_executor=EXECUTOR,
                expected_signer=EXECUTOR,
                current_observed_block=1000,
                policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=100),
            )

    def test_invalid_policy_is_rejected(self):
        with self.assertRaisesRegex(ProductionAuthorityEvidenceError, "positive integer"):
            AuthorityEvidenceReusePolicy(maximum_age_blocks=0)
        with self.assertRaisesRegex(ProductionAuthorityEvidenceError, "positive integer"):
            AuthorityEvidenceReusePolicy(maximum_age_blocks=True)

    def test_future_evidence_is_blocked(self):
        with self.assertRaises(ProductionAuthorityEvidenceError):
            verify_reusable_production_authority_evidence(
                self.evidence,
                expected_executor=EXECUTOR,
                expected_signer=SIGNER,
                current_observed_block=999,
                policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=100),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
