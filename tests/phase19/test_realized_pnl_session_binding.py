import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.validate_consolidated_evidence_session import main


class RealizedPnlSessionBindingTests(unittest.TestCase):
    def _manifest(self, root: Path):
        data = {
            "schema_version": 1,
            "session_id": "sess-pnl",
            "verified_artifact_commit": "fc0df125ee6d0ea694b976ff7d86622b9e45eb15",
            "intended_executor": "0x1111111111111111111111111111111111111111",
            "expected_signer": "0x2222222222222222222222222222222222222222",
            "intended_private_relay": "approved-relay",
            "operator_identity": "operator",
            "witness_identity": "witness",
            "observed_at_utc": "2026-09-16T10:00:00Z",
            "lanes": {
                "signer": {"status": "BLOCKED"},
                "polygon_authority": {"status": "BLOCKED"},
                "private_relay": {"status": "BLOCKED"},
                "shadow_staging": {"status": "BLOCKED"},
                "realized_pnl": {"status": "GREEN", "evidence_file": "realized_pnl.json"},
            },
        }
        path = root / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def _evidence(self, root: Path, **overrides):
        record = {
            "schema_version": 1,
            "artifact_commit": "fc0df125ee6d0ea694b976ff7d86622b9e45eb15",
            "execution_evidence_identity": "exec-proof-1",
            "settlement_evidence_identity": "settlement-proof-1",
            "gross_profit_usd": "1.50",
            "gas_cost_usd": "0.10",
            "loan_cost_usd": "0.20",
            "dex_cost_usd": "0.15",
            "relay_cost_usd": "0.05",
            "other_cost_usd": "0.25",
            "realized_net_profit_usd": "0.75",
            "operator_identity": "operator",
            "witness_identity": "witness",
            "observed_at_utc": "2026-09-16T10:00:00Z",
            "evidence_hash": "0x" + "0" * 64,
        }
        record.update(overrides)
        import hashlib
        payload = {k: record[k] for k in sorted(set(record) - {"evidence_hash"})}
        record["evidence_hash"] = "0x" + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        path = root / "realized_pnl.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def _run(self, evidence_overrides=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._evidence(root, **(evidence_overrides or {}))
            manifest = self._manifest(root)
            with patch(
                "scripts.validate_consolidated_evidence_session.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ):
                return main([str(manifest)])

    def test_realized_pnl_evidence_is_bound_to_manifest_identities(self):
        self.assertEqual(self._run(), 0)

    def test_realized_pnl_artifact_binding_mismatch_is_failed_closed(self):
        self.assertEqual(
            self._run({"artifact_commit": "eea845af1388ea619c54ffc4faf8a34d215e2aa1"}),
            2,
        )

    def test_realized_pnl_operator_binding_mismatch_is_failed_closed(self):
        self.assertEqual(self._run({"operator_identity": "different-operator"}), 2)

    def test_realized_pnl_witness_binding_mismatch_is_failed_closed(self):
        self.assertEqual(self._run({"witness_identity": "different-witness"}), 2)


if __name__ == "__main__":
    unittest.main()
