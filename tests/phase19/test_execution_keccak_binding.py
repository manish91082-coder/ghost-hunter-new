"""Focused conformance tests for canonical Ethereum execution hashes."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.execution import ExecutionIntent, TransactionEnvelope
from phantomx.hashing import KeccakUnavailable, keccak256_hex


class ExecutionKeccakBindingTests(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            chain_id=137,
            executor="0x0000000000000000000000000000000000000001",
            sender="0x0000000000000000000000000000000000000002",
            loan_asset="0x0000000000000000000000000000000000000003",
            loan_amount=1_000_000,
            route_hash="0xroute",
            calldata_hash="0xcalldata",
            nonce=42,
            deadline=2_000,
        )

    def test_empty_keccak_vector(self):
        try:
            digest = keccak256_hex(b"")
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertEqual(
            digest,
            "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )

    def test_intent_hash_uses_ethereum_keccak(self):
        try:
            digest = self.intent.intent_hash()
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertTrue(digest.startswith("0x"))
        self.assertEqual(len(digest), 66)
        self.assertNotEqual(
            digest,
            self.intent.test_only_sha256_fingerprint(),
        )

    def test_calldata_binding_changes_when_calldata_changes(self):
        try:
            first = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"A", 300_000, 100, 30)
            second = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"B", 300_000, 100, 30)
            self.assertNotEqual(first.calldata_hash, second.calldata_hash)
            self.assertEqual(len(first.calldata_hash), 66)
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))

    def test_mutating_route_changes_canonical_intent_digest(self):
        try:
            original = self.intent.intent_hash()
            mutated = self.intent.with_field(route_hash="0xchanged").intent_hash()
        except KeccakUnavailable as exc:
            self.skipTest(str(exc))
        self.assertNotEqual(original, mutated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
