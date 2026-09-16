import json
import tempfile
import unittest
from pathlib import Path

from phantomx.hashing import keccak256_hex
from scripts.package_signer_evidence import main


CHALLENGE = "0x" + "55" * 32
EXPECTED_ADDRESS = "0x" + "11" * 20
CHALLENGE_HASH = keccak256_hex(bytes.fromhex(CHALLENGE[2:]))
EVIDENCE_HASH = keccak256_hex((CHALLENGE_HASH + EXPECTED_ADDRESS).encode("ascii"))

VALID = {
    "schema_version": 1,
    "expected_address": EXPECTED_ADDRESS,
    "recovered_address": EXPECTED_ADDRESS,
    "challenge_hash": CHALLENGE_HASH,
    "signature": "0x" + "33" * 65,
    "evidence_hash": EVIDENCE_HASH,
}


class SignerEvidencePackagerTests(unittest.TestCase):
    def _run(self, verifier, extra=None, challenge=CHALLENGE):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "verifier.json"
            out = root / "signer_evidence.json"
            if extra:
                verifier = dict(verifier, **extra)
            src.write_text(json.dumps(verifier), encoding="utf-8")
            args = [
                str(src), str(out),
                "--challenge", challenge,
                "--verifier-commit", "e117b6550686cf5e0ff787d9bd7d85e83996db07",
                "--certification-ref", "CI-482",
                "--operator-identity", "operator-a",
                "--witness-identity", "witness-b",
                "--observed-at-utc", "2026-09-16T12:00:00Z",
            ]
            rc = main(args)
            packaged = out.read_text(encoding="utf-8") if out.is_file() else None
            return rc, packaged

    def test_packages_verified_output(self):
        rc, packaged = self._run(VALID)
        self.assertEqual(rc, 0)
        self.assertIsNotNone(packaged)
        record = json.loads(packaged)
        self.assertEqual(record["challenge"], CHALLENGE)
        self.assertEqual(record["challenge_hash"], CHALLENGE_HASH)
        self.assertEqual(record["evidence_hash"], EVIDENCE_HASH)
        self.assertEqual(record["certification_ref"], "CI-482")

    def test_blocks_expected_recovery_mismatch(self):
        rc, _ = self._run(VALID, {"recovered_address": "0x" + "66" * 20})
        self.assertEqual(rc, 2)

    def test_blocks_bad_signature_length(self):
        rc, _ = self._run(VALID, {"signature": "0x33"})
        self.assertEqual(rc, 2)

    def test_blocks_challenge_hash_mismatch(self):
        rc, _ = self._run(VALID, {"challenge_hash": "0x" + "22" * 32})
        self.assertEqual(rc, 2)

    def test_blocks_evidence_hash_mismatch(self):
        rc, _ = self._run(VALID, {"evidence_hash": "0x" + "44" * 32})
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
