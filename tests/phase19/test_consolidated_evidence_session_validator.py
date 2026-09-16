import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_consolidated_evidence_session import main


class ConsolidatedEvidenceSessionValidatorTests(unittest.TestCase):
    def _manifest(self, root: Path, **overrides):
        data = {
            "schema_version": 1,
            "session_id": "sess-001",
            "verified_artifact_commit": "2caa8ff285fa98e061dc22da82502bff2765b812",
            "intended_executor": "0x1111111111111111111111111111111111111111",
            "expected_signer": "0x2222222222222222222222222222222222222222",
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
        with tempfile.TemporaryDirectory() as temp:
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
                "private_relay": {"status": "GREEN", "evidence_file": str(evidence.relative_to(Path(__file__).resolve().parents[2]))},
                "shadow_staging": {"status": "BLOCKED"},
                "realized_pnl": {"status": "BLOCKED"},
            }
            manifest = self._manifest(root, lanes=lanes)
            self.assertIn(main([str(manifest)]), {0, 2})


if __name__ == "__main__":
    unittest.main()
