"""Adversarial tests for nonce reservation ↔ authorization binding."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.execution import Authorization, ExecutionIntent
from phantomx.nonce_binding import bind_nonce
from phantomx.nonce_manager import NonceManager


class NonceBindingTests(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            137,
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
            "0x0000000000000000000000000000000000000003",
            1_000_000,
            "0xroute",
            "0xcalldata",
            "0xeconomic",
            "0xsimulation",
            42,
            2_000,
        )
        self.authorization = Authorization(
            self.intent.intent_hash(), self.intent.calldata_hash,
            self.intent.economic_proof_hash, self.intent.simulation_proof_hash,
            self.intent.chain_id, self.intent.executor, self.intent.sender,
            self.intent.nonce, self.intent.deadline, 500_000, 100, 30,
        )
        self.reservation = NonceManager(42).reserve(self.intent.sender, "reservation-42")

    def test_exact_reservation_binds(self):
        bound = bind_nonce(self.reservation, self.intent, self.authorization)
        self.assertEqual(bound.reservation_id, "reservation-42")
        self.assertEqual(bound.nonce, 42)
        self.assertEqual(bound.intent_hash, self.intent.intent_hash())

    def test_different_nonce_rejected(self):
        mutated = self.intent.with_field(nonce=43)
        with self.assertRaises(ValueError):
            bind_nonce(self.reservation, mutated, self.authorization)

    def test_different_sender_rejected(self):
        mutated = self.intent.with_field(sender="0x0000000000000000000000000000000000000009")
        with self.assertRaises(ValueError):
            bind_nonce(self.reservation, mutated, self.authorization)

    def test_authorization_nonce_mutation_rejected(self):
        mutated = replace(self.authorization, nonce=43)
        with self.assertRaises(ValueError):
            bind_nonce(self.reservation, self.intent, mutated)

    def test_authorization_sender_mutation_rejected(self):
        mutated = replace(self.authorization, sender="0x0000000000000000000000000000000000000009")
        with self.assertRaises(ValueError):
            bind_nonce(self.reservation, self.intent, mutated)

    def test_authorization_intent_hash_mutation_rejected(self):
        mutated = replace(self.authorization, intent_hash="0xchanged")
        with self.assertRaises(ValueError):
            bind_nonce(self.reservation, self.intent, mutated)

    def test_wrong_reservation_id_does_not_change_binding_identity(self):
        other = replace(self.reservation, reservation_id="different-id")
        bound = bind_nonce(other, self.intent, self.authorization)
        self.assertEqual(bound.reservation_id, "different-id")
        self.assertEqual(bound.nonce, 42)


if __name__ == "__main__":
    unittest.main(verbosity=2)
