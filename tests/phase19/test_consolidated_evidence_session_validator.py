import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.validate_consolidated_evidence_session import main


class ConsolidatedEvidenceSessionValidatorTests(unittest.TestCase):
    def _manifest(self, root: Path, **overrides):
        data = {
            "schema_version": 1,
            "session_id": "sess-001",
            "verified_artifact_commit": "e117b6550686cf5e0ff787d9bd7d85e83996db07",
            "intended_executor": "0x1111111111111111111111111111111111111111",
            "expected_signer": "0x2222222222222222222222222222222222222222",
            "intended_private_relay": "approved-relay",
            "operator_identity": "operator",
            "witness_identity": "witness",
            "observed_at_utc": "2026-09-16T07:30:00Z",
            "lanes": {
                "signer": {"status": "BLOCKED"},
                "polygon_authority": {"status": "BLOCKED"},
                "private_relay": {"status": "BLOCKED"},
                "shadow_staging": {"status": "BLOCKED"},
                "realized_pnl": {"status": "BLOCKED"},
            },
        }
        data.update(overrides)
        path = root / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_missing_lane_evidence_is_blocked_not_inferred_green(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._manifest(root)
            self.assertEqual(main([str(manifest)]), 0)

    def test_frozen_artifact_mismatch_is_rejected_before_lane_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._manifest(root, verified_artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812")
            self.assertEqual(main([str(manifest)]), 2)

    def test_unknown_lane_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lanes = {
                "signer": {"status": "BLOCKED"},
                "polygon_authority": {"status": "BLOCKED"},
                "private_relay": {"status": "BLOCKED"},
                "shadow_staging": {"status": "BLOCKED"},
                "realized_pnl": {"status": "BLOCKED"},
                "unexpected": {"status": "BLOCKED"},
            }
            manifest = self._manifest(root, lanes=lanes)
            self.assertEqual(main([str(manifest)]), 2)

    def test_invalid_lane_status_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lanes = {
                "signer": {"status": "UNKNOWN"},
                "polygon_authority": {"status": "BLOCKED"},
                "private_relay": {"status": "BLOCKED"},
                "shadow_staging": {"status": "BLOCKED"},
                "realized_pnl": {"status": "BLOCKED"},
            }
            manifest = self._manifest(root, lanes=lanes)
            self.assertEqual(main([str(manifest)]), 2)

    def test_manifest_with_existing_validator_file_reports_review_required(self):
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(dir=repo_root) as temp:
            root = Path(temp)
            evidence = root / "relay.json"
            evidence.write_text(
                json.dumps({
                    "schema_version": 1,
                    "relay_name": "relay",
                    "endpoint_scheme": "https",
                    "private_assertion": True,
                    "authentication_configured": True,
                    "observed_response_class": "AUTHENTICATED",
                    "observed_at_utc": "2026-09-16T07:30:00Z",
                    "operator_identity": "operator",
                    "witness_identity": "witness",
                    "evidence_hash": "0x" + "0" * 64,
                }),
                encoding="utf-8",
            )
            lanes = {
                "signer": {"status": "BLOCKED"},
                "polygon_authority": {"status": "BLOCKED"},
                "private_relay": {"status": "GREEN", "evidence_file": str(evidence.relative_to(repo_root))},
                "shadow_staging": {"status": "BLOCKED"},
                "realized_pnl": {"status": "BLOCKED"},
            }
            manifest = self._manifest(root, lanes=lanes)
            self.assertIn(main([str(manifest)]), {0, 2})

    def _write_evidence(self, root: Path, lane: str, data: dict) -> str:
        path = root / f"{lane}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path.name

    def test_valid_identity_bindings_allow_external_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            signer = {
                "schema_version": 1,
                "expected_address": "0x2222222222222222222222222222222222222222",
                "recovered_address": "0x2222222222222222222222222222222222222222",
                "challenge": "00" * 32,
                "challenge_hash": "0x" + "0" * 64,
                "signature": "00" * 65,
                "evidence_hash": "0x" + "0" * 64,
                "verifier_commit": "v",
                "certification_ref": "c",
                "operator_identity": "operator",
                "witness_identity": "witness",
                "observed_at_utc": "2026-09-16T07:30:00Z",
            }
            authority = {
                "schema_version": 1,
                "chain_id": 137,
                "executor": "0x1111111111111111111111111111111111111111",
                "expected_signer": "0x2222222222222222222222222222222222222222",
                "observed_owner": "0x2222222222222222222222222222222222222222",
                "common_block": 1,
                "runtime_code_hash": "0x" + "1" * 64,
                "quorum": 1,
                "attesting_provider_names": ["p1"],
                "provider_observations": [{
                    "provider_name": "p1",
                    "chain_id": 137,
                    "observed_block": 1,
                    "owner": "0x2222222222222222222222222222222222222222",
                    "runtime_code_hash": "0x" + "1" * 64,
                }],
                "evidence_hash": "0x" + "2" * 64,
                "observed_at_utc": "2026-09-16T07:30:00Z",
                "operator_identity": "operator",
                "witness_identity": "witness",
            }
            shadow = {
                "schema_version": 1,
                "artifact_commit": "e117b6550686cf5e0ff787d9bd7d85e83996db07",
                "executor_identity": "0x1111111111111111111111111111111111111111",
                "expected_signer": "0x2222222222222222222222222222222222222222",
                "route_proof_identity": "route",
                "economic_proof_identity": "economic",
                "authority_evidence_identity": "authority",
                "staging_environment_identity": "staging",
                "submission_policy_identity": "policy",
                "operator_identity": "operator",
                "witness_identity": "witness",
                "observed_at_utc": "2026-09-16T07:30:00Z",
                "execution_result": {"mode": "SHADOW_STAGING", "live_capital": False, "broadcast": False, "outcome": "PASS"},
                "evidence_hash": "0x" + "3" * 64,
            }
            signer_path = self._write_evidence(root, "signer", signer)
            authority_path = self._write_evidence(root, "authority", authority)
            shadow_path = self._write_evidence(root, "shadow", shadow)
            lanes = {
                "signer": {"status": "GREEN", "evidence_file": signer_path},
                "polygon_authority": {"status": "GREEN", "evidence_file": authority_path},
                "private_relay": {"status": "BLOCKED"},
                "shadow_staging": {"status": "GREEN", "evidence_file": shadow_path},
                "realized_pnl": {"status": "BLOCKED"},
            }
            manifest = self._manifest(root, lanes=lanes)
            with patch("scripts.validate_consolidated_evidence_session.subprocess.run", return_value=SimpleNamespace(returncode=0)):
                self.assertEqual(main([str(manifest)]), 0)

    def test_signer_binding_mismatch_is_failed_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = {
                "expected_address": "0x3333333333333333333333333333333333333333",
                "recovered_address": "0x3333333333333333333333333333333333333333",
                "operator_identity": "operator",
                "witness_identity": "witness",
            }
            path = self._write_evidence(root, "signer", evidence)
            data = json.loads(self._manifest(root).read_text())
            data["lanes"]["signer"] = {"status": "GREEN", "evidence_file": path}
            (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            with patch("scripts.validate_consolidated_evidence_session.subprocess.run", return_value=SimpleNamespace(returncode=0)):
                self.assertEqual(main([str(root / "manifest.json")]), 2)

    def test_authority_executor_binding_mismatch_is_failed_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = {
                "executor": "0x3333333333333333333333333333333333333333",
                "expected_signer": "0x2222222222222222222222222222222222222222",
                "observed_owner": "0x2222222222222222222222222222222222222222",
                "operator_identity": "operator",
                "witness_identity": "witness",
            }
            path = self._write_evidence(root, "authority", evidence)
            data = json.loads(self._manifest(root).read_text())
            data["lanes"]["polygon_authority"] = {"status": "GREEN", "evidence_file": path}
            (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            with patch("scripts.validate_consolidated_evidence_session.subprocess.run", return_value=SimpleNamespace(returncode=0)):
                self.assertEqual(main([str(root / "manifest.json")]), 2)

    def test_shadow_artifact_binding_mismatch_is_failed_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = {
                "artifact_commit": "3caa8ff285fa98e061dc22da82502bff2765b812",
                "executor_identity": "0x1111111111111111111111111111111111111111",
                "expected_signer": "0x2222222222222222222222222222222222222222",
                "operator_identity": "operator",
                "witness_identity": "witness",
            }
            path = self._write_evidence(root, "shadow", evidence)
            data = json.loads(self._manifest(root).read_text())
            data["lanes"]["shadow_staging"] = {"status": "GREEN", "evidence_file": path}
            (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            with patch("scripts.validate_consolidated_evidence_session.subprocess.run", return_value=SimpleNamespace(returncode=0)):
                self.assertEqual(main([str(root / "manifest.json")]), 2)

    def test_absolute_evidence_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = json.loads(self._manifest(root).read_text())
            data["lanes"]["private_relay"] = {"status": "GREEN", "evidence_file": str(root / "relay.json")}
            (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            (root / "relay.json").write_text("{}", encoding="utf-8")
            self.assertEqual(main([str(root / "manifest.json")]), 2)


if __name__ == "__main__":
    unittest.main()
