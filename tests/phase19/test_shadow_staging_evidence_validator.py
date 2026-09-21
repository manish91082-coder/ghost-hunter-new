import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_shadow_staging_evidence import main


CURRENT_VERIFIED_ARTIFACT = "eea845af1388ea619c54ffc4faf8a34d215e2aa1"


class ShadowStagingEvidenceValidatorTests(unittest.TestCase):
    def _evidence(self, root: Path, **overrides):
        data = {
            "schema_version": 1,
            "artifact_commit": CURRENT_VERIFIED_ARTIFACT,
            "execution_checkout_commit": CURRENT_VERIFIED_ARTIFACT,
            "executor_identity": "0x1111111111111111111111111111111111111111",
            "expected_signer": "0x2222222222222222222222222222222222222222",
            "route_proof_identity": "route-proof-1",
            "economic_proof_identity": "economic-proof-1",
            "authority_evidence_identity": "authority-evidence-1",
            "staging_environment_identity": "staging-env-1",
            "submission_policy_identity": "submission-policy-1",
            "operator_identity": "operator",
            "witness_identity": "witness",
            "observed_at_utc": "2026-09-16T08:30:00Z",
            "execution_result": {
                "mode": "SHADOW_STAGING",
                "live_capital": False,
                "broadcast": False,
                "outcome": "PASS",
            },
            "evidence_hash": "",
        }
        data.update(overrides)
        payload = {key: data[key] for key in sorted(set(data) - {"evidence_hash"})}
        data["evidence_hash"] = "0x" + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        path = root / "staging.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_accepts_consistent_shadow_staging_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(main([str(self._evidence(Path(temp)))]), 0)

    def test_rejects_execution_checkout_artifact_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._evidence(Path(temp), execution_checkout_commit="0" * 40)
            self.assertEqual(main([str(path)]), 2)

    def test_rejects_live_capital(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._evidence(Path(temp))
            data = json.loads(path.read_text())
            data["execution_result"]["live_capital"] = True
            path.write_text(json.dumps(data))
            self.assertEqual(main([str(path)]), 2)

    def test_rejects_broadcast(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._evidence(Path(temp))
            data = json.loads(path.read_text())
            data["execution_result"]["broadcast"] = True
            path.write_text(json.dumps(data))
            self.assertEqual(main([str(path)]), 2)

    def test_rejects_artifact_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._evidence(Path(temp))
            data = json.loads(path.read_text())
            data["artifact_commit"] = "0" * 40
            path.write_text(json.dumps(data))
            self.assertEqual(main([str(path)]), 2)

    def test_rejects_unknown_field(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._evidence(Path(temp))
            data = json.loads(path.read_text())
            data["unexpected"] = "x"
            path.write_text(json.dumps(data))
            self.assertEqual(main([str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
