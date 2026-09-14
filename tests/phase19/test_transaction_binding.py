"""Adversarial tests for authorization-to-transaction binding."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope
from phantomx.transaction_binding import TransactionBindingVerifier


class TransactionBindingTests(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            137,
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
            "0x0000000000000000000000000000000000000003",
            1_000_000,
            "0xroute",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0xeconomic",
            "0xsimulation",
            42,
            2_000,
        )
        self.calldata = b"authorized-calldata"
        self.intent = self.intent.with_field(
            calldata_hash=TransactionEnvelope(
                137, self.intent.sender, self.intent.executor, 42,
                self.calldata, 300_000, 100, 30,
            ).calldata_hash
        )
        self.authorization = Authorization(
            self.intent.intent_hash(), self.intent.calldata_hash,
            self.intent.economic_proof_hash, self.intent.simulation_proof_hash,
            self.intent.chain_id, self.intent.executor, self.intent.sender,
            self.intent.nonce, self.intent.deadline,
        )
        self.envelope = TransactionEnvelope(
            137, self.intent.sender, self.intent.executor, 42,
            self.calldata, 300_000, 100, 30,
        )
        self.verifier = TransactionBindingVerifier()

    def test_exact_envelope_is_accepted(self):
        result = self.verifier.verify(self.authorization, self.intent, self.envelope, 1_000)
        self.assertEqual(result.intent_hash, self.intent.intent_hash())
        self.assertEqual(result.calldata_hash, self.envelope.calldata_hash)
        self.assertEqual(result.nonce, 42)

    def test_calldata_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"mutated", 300_000, 100, 30)
        with self.assertRaises(ValueError):
            self.verifier.verify(self.authorization, self.intent, mutated, 1_000)

    def test_sender_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, "0x0000000000000000000000000000000000000009", self.intent.executor, 42, self.calldata, 300_000, 100, 30)
        with self.assertRaises(ValueError):
            self.verifier.verify(self.authorization, self.intent, mutated, 1_000)

    def test_executor_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, self.intent.sender, "0x0000000000000000000000000000000000000009", 42, self.calldata, 300_000, 100, 30)
        with self.assertRaises(ValueError):
            self.verifier.verify(self.authorization, self.intent, mutated, 1_000)

    def test_nonce_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 43, self.calldata, 300_000, 100, 30)
        with self.assertRaises(ValueError):
            self.verifier.verify(self.authorization, self.intent, mutated, 1_000)

    def test_chain_mutation_is_rejected(self):
        mutated = TransactionEnvelope(1, self.intent.sender, self.intent.executor, 42, self.calldata, 300_000, 100, 30)
        with self.assertRaises(ValueError):
            self.verifier.verify(self.authorization, self.intent, mutated, 1_000)

    def test_expired_authorization_is_rejected_before_envelope_acceptance(self):
        with self.assertRaises(ValueError):
            self.verifier.verify(self.authorization, self.intent, self.envelope, 2_001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
