import json
import tempfile
import unittest
from pathlib import Path

from phantomx.executor_authority import ExecutorAuthorityEvidence
from scripts.validate_production_authority_evidence import main


EXECUTOR = "0x1111111111111111111111111111111111111111"
SIGNER = "0x2222222222222222222222222222222222222222"
CODE_HASH = "0x" + "aa" * 32


def make_record():
    evidence = ExecutorAuthorityEvidence(
        schema_version=1,
        chain_id=137,
        executor=EXECUTOR,
        owner=SIGNER,
        observed_block=500,
        runtime_code_hash=CODE_HASH,
        attesting_provider_names=("primary", "secondary"),
    )
    return {
        "schema_version": 1,
        "chain_id": 137,
        "executor": EXECUTOR,
        "expected_signer": SIGNER,
        "common_block": 500,
        "observed_owner": SIGNER,
        "runtime_code_hash": CODE_HASH,
        "quorum": 2,
        "attesting_provider_names": ["primary", "secondary"],
        "provider_observations": [
            {"provider_name": "primary", "chain_id": 137, "observed_block": 500, "owner": SIGNER, "runtime_code_hash": CODE_HASH},
            {"provider_name": "secondary", "chain_id": 137, "observed_block": 500, "owner": SIGNER, "runtime_code_hash": CODE_HASH},
        ],
        "evidence_hash": evidence.evidence_hash,
        "observed_at_utc": "2026-09-16T06:00:00Z",
        "operator_identity": "operator-a",
        "witness_identity": "witness-b",
    }


class ProductionAuthorityEvidenceValidatorTests(unittest.TestCase):
    def _run(self, record):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            return main([str(path)])

    def test_accepts_consistent_quorum_evidence(self):
        self.assertEqual(self._run(make_record()), 0)

    def test_rejects_owner_mismatch(self):
        record = make_record()
        record["provider_observations"][1]["owner"] = EXECUTOR
        self.assertEqual(self._run(record), 2)

    def test_rejects_common_block_mismatch(self):
        record = make_record()
        record["provider_observations"][0]["observed_block"] = 501
        self.assertEqual(self._run(record), 2)

    def test_rejects_duplicate_provider_identity(self):
        record = make_record()
        record["attesting_provider_names"] = ["primary", "primary"]
        self.assertEqual(self._run(record), 2)

    def test_rejects_evidence_hash_tampering(self):
        record = make_record()
        record["evidence_hash"] = "0x" + "bb" * 32
        self.assertEqual(self._run(record), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
