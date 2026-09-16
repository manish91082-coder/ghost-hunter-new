import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.validate_consolidated_evidence_session import main


class CrossLaneProvenanceBindingTests(unittest.TestCase):
    def _manifest(self, root: Path, lanes):
        data = {
            "schema_version": 1,
            "session_id": "sess-cross-lane",
            "verified_artifact_commit": "2caa8ff285fa98e061dc22da82502bff2765b812",
            "intended_executor": "0x1111111111111111111111111111111111111111",
            "expected_signer": "0x2222222222222222222222222222222222222222",
            "intended_private_relay": "approved-relay",
            "operator_identity": "operator",
            "witness_identity": "witness",
            "observed_at_utc": "2026-09-16T07:30:00Z",
            "lanes": lanes,
        }
        path = root / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    @staticmethod
    def _evidence(root: Path, name: str, **values) -> str:
        path = root / f"{name}.json"
        path.write_text(json.dumps(values), encoding="utf-8")
        return path.name

    def test_shadow_must_reference_accepted_authority_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            authority_path = self._evidence(
                root,
                "authority",
                schema_version=1,
                evidence_hash="0x" + "2" * 64,
                executor="0x1111111111111111111111111111111111111111",
                expected_signer="0x2222222222222222222222222222222222222222",
                observed_owner="0x2222222222222222222222222222222222222222",
                operator_identity="operator",
                witness_identity="witness",
            )
            shadow_path = self._evidence(
                root,
                "shadow",
                schema_version=1,
                artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812",
                executor_identity="0x1111111111111111111111111111111111111111",
                expected_signer="0x2222222222222222222222222222222222222222",
                authority_evidence_identity="0x" + "9" * 64,
                operator_identity="operator",
                witness_identity="witness",
                evidence_hash="0x" + "3" * 64,
            )
            manifest = self._manifest(
                root,
                {
                    "signer": {"status": "BLOCKED"},
                    "polygon_authority": {"status": "GREEN", "evidence_file": authority_path},
                    "private_relay": {"status": "BLOCKED"},
                    "shadow_staging": {"status": "GREEN", "evidence_file": shadow_path},
                    "realized_pnl": {"status": "BLOCKED"},
                },
            )
            with patch(
                "scripts.validate_consolidated_evidence_session.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ):
                self.assertEqual(main([str(manifest)]), 2)

    def test_shadow_matching_authority_hash_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            authority_path = self._evidence(
                root,
                "authority",
                evidence_hash="0x" + "2" * 64,
                executor="0x1111111111111111111111111111111111111111",
                expected_signer="0x2222222222222222222222222222222222222222",
                observed_owner="0x2222222222222222222222222222222222222222",
                operator_identity="operator",
                witness_identity="witness",
            )
            shadow_path = self._evidence(
                root,
                "shadow",
                artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812",
                executor_identity="0x1111111111111111111111111111111111111111",
                expected_signer="0x2222222222222222222222222222222222222222",
                authority_evidence_identity="0x" + "2" * 64,
                operator_identity="operator",
                witness_identity="witness",
                evidence_hash="0x" + "3" * 64,
            )
            manifest = self._manifest(
                root,
                {
                    "signer": {"status": "BLOCKED"},
                    "polygon_authority": {"status": "GREEN", "evidence_file": authority_path},
                    "private_relay": {"status": "BLOCKED"},
                    "shadow_staging": {"status": "GREEN", "evidence_file": shadow_path},
                    "realized_pnl": {"status": "BLOCKED"},
                },
            )
            with patch(
                "scripts.validate_consolidated_evidence_session.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ):
                self.assertEqual(main([str(manifest)]), 0)

    def test_realized_pnl_must_reference_accepted_shadow_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shadow_path = self._evidence(
                root,
                "shadow",
                artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812",
                executor_identity="0x1111111111111111111111111111111111111111",
                expected_signer="0x2222222222222222222222222222222222222222",
                operator_identity="operator",
                witness_identity="witness",
                evidence_hash="0x" + "3" * 64,
            )
            pnl_path = self._evidence(
                root,
                "pnl",
                artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812",
                execution_evidence_identity="0x" + "9" * 64,
                operator_identity="operator",
                witness_identity="witness",
            )
            manifest = self._manifest(
                root,
                {
                    "signer": {"status": "BLOCKED"},
                    "polygon_authority": {"status": "BLOCKED"},
                    "private_relay": {"status": "BLOCKED"},
                    "shadow_staging": {"status": "GREEN", "evidence_file": shadow_path},
                    "realized_pnl": {"status": "GREEN", "evidence_file": pnl_path},
                },
            )
            with patch(
                "scripts.validate_consolidated_evidence_session.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ):
                self.assertEqual(main([str(manifest)]), 2)

    def test_realized_pnl_matching_shadow_hash_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shadow_path = self._evidence(
                root,
                "shadow",
                artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812",
                executor_identity="0x1111111111111111111111111111111111111111",
                expected_signer="0x2222222222222222222222222222222222222222",
                operator_identity="operator",
                witness_identity="witness",
                evidence_hash="0x" + "3" * 64,
            )
            pnl_path = self._evidence(
                root,
                "pnl",
                artifact_commit="2caa8ff285fa98e061dc22da82502bff2765b812",
                execution_evidence_identity="0x" + "3" * 64,
                operator_identity="operator",
                witness_identity="witness",
            )
            manifest = self._manifest(
                root,
                {
                    "signer": {"status": "BLOCKED"},
                    "polygon_authority": {"status": "BLOCKED"},
                    "private_relay": {"status": "BLOCKED"},
                    "shadow_staging": {"status": "GREEN", "evidence_file": shadow_path},
                    "realized_pnl": {"status": "GREEN", "evidence_file": pnl_path},
                },
            )
            with patch(
                "scripts.validate_consolidated_evidence_session.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ):
                self.assertEqual(main([str(manifest)]), 0)


if __name__ == "__main__":
    unittest.main()
