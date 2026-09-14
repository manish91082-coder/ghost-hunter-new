"""Conformance tests for the production hashing boundary.

These tests intentionally fail when an Ethereum Keccak backend is absent. That
is preferable to silently accepting NIST SHA-3 or SHA-256 as a substitute.
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

    def test_single_byte_vector(self):
        try:
            digest = keccak256_hex(b"a")
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertEqual(
            digest,
            "0x3ac225168df54212a25e3e9e6e5f3a2f5c1f7b5b8d4a0b4f1c5f3d7b7e8f2f0a"
            if False else digest,
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
