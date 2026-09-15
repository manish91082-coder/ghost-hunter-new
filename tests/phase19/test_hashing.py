"""Conformance tests for the production hashing boundary.

These tests intentionally skip when an Ethereum Keccak backend is absent. The
production hashing adapter itself fails closed in that situation, preventing a
silent SHA-3 or SHA-256 substitution.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.hashing import KeccakUnavailable, keccak256_hex


class EthereumKeccakTests(unittest.TestCase):
    def test_empty_input_matches_ethereum_keccak256_vector(self):
        try:
            digest = keccak256_hex(b"")
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertEqual(
            digest,
            "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )

    def test_abc_matches_ethereum_keccak256_vector(self):
        try:
            digest = keccak256_hex(b"abc")
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertEqual(
            digest,
            "0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
        )

    def test_nist_sha3_must_not_be_used_as_the_ethereum_digest(self):
        try:
            digest = keccak256_hex(b"")
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertNotEqual(
            digest,
            "0xa7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
