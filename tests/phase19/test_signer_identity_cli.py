import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from phantomx.signer import EthereumEip1559Signer
from scripts.verify_signer_identity import main

PRIVATE_KEY = "0x" + "01" * 32


class SignerIdentityCLITests(unittest.TestCase):
    def setUp(self):
        self.signer = EthereumEip1559Signer(PRIVATE_KEY)
        self.challenge = b"C" * 32
        self.signature = self.signer.sign_challenge(self.challenge)

    def test_generate_challenge_emits_exactly_one_fresh_32_byte_hex_value(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--generate-challenge"]), 0)
        value = output.getvalue().strip()
        self.assertTrue(value.startswith("0x"))
        self.assertEqual(len(value), 66)
        self.assertNotEqual(value, "0x" + "00" * 32)

    def test_generate_challenge_rejects_verification_arguments(self):
        with self.assertRaises(SystemExit):
            main(["--generate-challenge", "--challenge", self.challenge.hex()])

    def test_verification_prints_canonical_non_secret_evidence(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                main([
                    "--expected-address", self.signer.address,
                    "--challenge", self.challenge.hex(),
                    "--signature", self.signature.hex(),
                ]),
                0,
            )
        record = json.loads(output.getvalue())
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["expected_address"], self.signer.address)
        self.assertEqual(record["recovered_address"], self.signer.address)
        self.assertEqual(record["challenge_hash"], "0x" + __import__("phantomx.hashing", fromlist=["keccak256_hex"]).keccak256_hex(self.challenge)[2:])
        self.assertEqual(len(record["signature"]), 132)
        self.assertTrue(record["evidence_hash"].startswith("0x"))

    def test_wrong_signature_fails_closed_without_json_evidence(self):
        err = io.StringIO()
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main([
                "--expected-address", self.signer.address,
                "--challenge", self.challenge.hex(),
                "--signature", EthereumEip1559Signer("0x" + "02" * 32).sign_challenge(self.challenge).hex(),
            ])
        self.assertEqual(rc, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("BLOCKED:", err.getvalue())

    def test_missing_verification_input_is_rejected(self):
        with self.assertRaises(SystemExit):
            main(["--expected-address", self.signer.address])


if __name__ == "__main__":
    unittest.main(verbosity=2)
