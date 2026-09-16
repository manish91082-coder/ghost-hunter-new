import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_private_relay_evidence import main


class PrivateRelayEvidenceValidatorTests(unittest.TestCase):
    def _record(self, **overrides):
        record = {
            "schema_version": 1,
            "relay_name": "approved-relay",
            "endpoint_scheme": "https",
            "private_assertion": True,
            "authentication_configured": True,
            "observed_response_class": "CONTROLLED_AUTH_RESPONSE",
            "observed_at_utc": "2026-09-16T00:00:00Z",
            "operator_identity": "operator-1",
            "witness_identity": "witness-1",
        }
        record.update(overrides)
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        record["evidence_hash"] = "0x" + hashlib.sha256(canonical.encode()).hexdigest()
        return record

    def _run(self, record):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            return main([str(path)])

    def test_accepts_consistent_non_secret_evidence(self):
        self.assertEqual(self._run(self._record()), 0)

    def test_rejects_non_https(self):
        self.assertEqual(self._run(self._record(endpoint_scheme="http")), 2)

    def test_rejects_private_false(self):
        self.assertEqual(self._run(self._record(private_assertion=False)), 2)

    def test_rejects_missing_authentication(self):
        self.assertEqual(self._run(self._record(authentication_configured=False)), 2)

    def test_rejects_unknown_fields(self):
        self.assertEqual(self._run(self._record(extra="not-allowed")), 2)

    def test_rejects_secret_marker_content(self):
        self.assertEqual(self._run(self._record(observed_response_class="contains api_key material")), 2)

    def test_rejects_hash_tampering(self):
        record = self._record()
        record["evidence_hash"] = "0x" + "00" * 32
        self.assertEqual(self._run(record), 2)

    def test_rejects_missing_witness_identity(self):
        self.assertEqual(self._run(self._record(witness_identity="")), 2)


if __name__ == "__main__":
    unittest.main()
