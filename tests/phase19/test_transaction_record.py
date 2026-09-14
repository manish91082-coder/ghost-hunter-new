"""Adversarial tests for immutable TransactionRecord binding."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.execution import Authorization, ExecutionIntent, ExecutionState, TransactionEnvelope
from phantomx.nonce_binding import bind_nonce
from phantomx.nonce_manager import NonceManager
from phantomx.transaction_record import build_signed_record


class TransactionRecordTests(unittest.TestCase):
    def setUp(self):
        sender = "0x0000000000000000000000000000000000000002"
        executor = "0x0000000000000000000000000000000000000001"
        calldata = b"authorized-calldata"
        provisional = ExecutionIntent(137, executor, sender, "0x0000000000000000000000000000000000000003", 1_000_000, "0xroute", "0x0", "0xeconomic", "0xsimulation", 42, 2_000)
        envelope = TransactionEnvelope(137, sender, executor, 42, calldata, 300_000, 100, 30)
        intent = provisional.with_field(calldata_hash=envelope.calldata_hash)
        authorization = Authorization(intent.intent_hash(), intent.calldata_hash, intent.economic_proof_hash, intent.simulation_proof_hash, 137, executor, sender, 42, 2_000, 300_000, 100, 30)
        reservation = NonceManager(42).reserve(sender, "reservation-42")
        bound = bind_nonce(reservation, intent, authorization)
        self.intent = intent
        self.authorization = authorization
        self.envelope = envelope
        self.bound = bound
        self.tx_hash = "0x" + "11" * 32

    def test_exact_signed_record_is_accepted(self):
        record = build_signed_record(self.intent, self.authorization, self.envelope, self.bound, self.tx_hash)
        self.assertEqual(record.state, ExecutionState.SIGNED)
        self.assertEqual(record.intent_hash, self.intent.intent_hash())
        self.assertEqual(record.calldata_hash, self.envelope.calldata_hash)
        self.assertEqual(record.nonce, 42)
        self.assertEqual(record.tx_hash, self.tx_hash)
        record.validate_binding(self.intent, self.authorization, self.envelope, self.bound)

    def test_calldata_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, self.envelope.sender, self.envelope.executor, 42, b"mutated", 300_000, 100, 30)
        with self.assertRaises(ValueError):
            build_signed_record(self.intent, self.authorization, mutated, self.bound, self.tx_hash)

    def test_nonce_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, self.envelope.sender, self.envelope.executor, 43, self.envelope.calldata, 300_000, 100, 30)
        with self.assertRaises(ValueError):
            build_signed_record(self.intent, self.authorization, mutated, self.bound, self.tx_hash)

    def test_gas_mutation_is_rejected(self):
        mutated = TransactionEnvelope(137, self.envelope.sender, self.envelope.executor, 42, self.envelope.calldata, 300_001, 100, 30)
        with self.assertRaises(ValueError):
            build_signed_record(self.intent, self.authorization, mutated, self.bound, self.tx_hash)

    def test_authorization_mutation_is_rejected(self):
        mutated = Authorization(self.authorization.intent_hash, self.authorization.calldata_hash, self.authorization.economic_proof_hash, self.authorization.simulation_proof_hash, 137, self.authorization.executor, self.authorization.sender, 42, 2_000, 300_000, 101, 30)
        with self.assertRaises(ValueError):
            build_signed_record(self.intent, mutated, self.envelope, self.bound, self.tx_hash)

    def test_intent_mutation_is_rejected(self):
        mutated = self.intent.with_field(loan_amount=1_000_001)
        with self.assertRaises(ValueError):
            build_signed_record(mutated, self.authorization, self.envelope, self.bound, self.tx_hash)

    def test_nonce_reservation_mutation_is_rejected(self):
        mutated = self.bound.__class__(self.bound.reservation_id, self.bound.sender, 43, self.bound.intent_hash)
        with self.assertRaises(ValueError):
            build_signed_record(self.intent, self.authorization, self.envelope, mutated, self.tx_hash)

    def test_invalid_transaction_hash_is_rejected(self):
        with self.assertRaises(ValueError):
            build_signed_record(self.intent, self.authorization, self.envelope, self.bound, "0x1234")

    def test_identity_hash_is_stable_but_state_hash_changes(self):
        record = build_signed_record(self.intent, self.authorization, self.envelope, self.bound, self.tx_hash)
        submitted = record.with_state(ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(record.record_hash(), submitted.record_hash())
        self.assertNotEqual(record.state_hash(), submitted.state_hash())

    def test_record_is_frozen(self):
        record = build_signed_record(self.intent, self.authorization, self.envelope, self.bound, self.tx_hash)
        with self.assertRaises(Exception):
            record.tx_hash = "0x" + "22" * 32


if __name__ == "__main__":
    unittest.main(verbosity=2)
