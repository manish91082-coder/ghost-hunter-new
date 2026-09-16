import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_realized_pnl_evidence import main


class RealizedPnlEvidenceValidatorTests(unittest.TestCase):
    def _record(self, **overrides):
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
            "operator_identity": "operator-1",
            "witness_identity": "witness-1",
            "observed_at_utc": "2026-09-16T10:00:00Z",
        }
        record.update(overrides)
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        record["evidence_hash"] = "0x" + hashlib.sha256(canonical.encode()).hexdigest()
        return record

    def _run(self, record):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "realized_pnl.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            return main([str(path)])

    def test_accepts_strictly_positive_realized_profit(self):
        self.assertEqual(self._run(self._record()), 0)

    def test_rejects_profit_equal_to_threshold(self):
        self.assertEqual(
            self._run(self._record(realized_net_profit_usd="0.20")),
            2,
        )

    def test_rejects_arithmetic_mismatch(self):
        self.assertEqual(
            self._run(self._record(realized_net_profit_usd="0.76")),
            2,
        )

    def test_rejects_negative_cost(self):
        self.assertEqual(self._run(self._record(gas_cost_usd="-0.10")), 2)

    def test_rejects_unknown_fields(self):
        self.assertEqual(self._run(self._record(extra="not-allowed")), 2)

    def test_rejects_artifact_format(self):
        self.assertEqual(self._run(self._record(artifact_commit="bad")), 2)

    def test_rejects_hash_tampering(self):
        record = self._record()
        record["evidence_hash"] = "0x" + "00" * 32
        self.assertEqual(self._run(record), 2)

    def test_rejects_missing_witness(self):
        self.assertEqual(self._run(self._record(witness_identity="")), 2)


if __name__ == "__main__":
    unittest.main()
