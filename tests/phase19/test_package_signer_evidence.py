import json
import tempfile
import unittest
from pathlib import Path

from scripts.package_signer_evidence import main


VALID = {
    "schema_version": 1,
    "expected_address": "0x" + "11" * 20,
    "recovered_address": "0x" + "11" * 20,
    "challenge_hash": "0x" + "22" * 32,
    "signature": "0x" + "33" * 65,
    "evidence_hash": "0x" + "44" * 32,
}


class SignerEvidencePackagerTests(unittest.TestCase):
    def _run(self, verifier, extra=None):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "verifier.json"
            out = root / "signer_evidence.json"
            src.write_text(json.dumps(verifier), encoding="utf-8")
            args = [
                str(src), str(out),
                "--challenge", "0x" + "55" * 32,
                "--verifier-commit", "e117b6550686cf5e0ff787d9bd7d85e83996db07",
                "--certification-ref", "CI-482",
                "--operator-identity", "operator-a",
                "--witness-identity", "witness-b",
                "--observed-at-utc", "2026-09-16T12:00:00Z",
            ]
            if extra:
                verifier = dict(verifier, **extra)
                src.write_text(json.dumps(verifier), encoding="utf-8")
            rc = main(args)
            packaged = out.read_text(encoding="utf-8") if out.is_file() else None
            return rc, packaged

    def test_packages_verified_output(self):
        rc, packaged = self._run(VALID)
        self.assertEqual(rc, 0)
        self.assertIsNotNone(packaged)
        record = json.loads(packaged)
        self.assertEqual(record["challenge"], "0x" + "55" * 32)
        self.assertEqual(record["certification_ref"], "CI-482")

    def test_blocks_expected_recovery_mismatch(self):
        rc, _ = self._run(VALID, {"recovered_address": "0x" + "66" * 20})
        self.assertEqual(rc, 2)

    def test_blocks_bad_signature_length(self):
        rc, _ = self._run(VALID, {"signature": "0x33"})
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
