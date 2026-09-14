"""Adversarial and restart tests for durable TransactionRecord storage."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from phantomx.execution import Authorization, ExecutionIntent, ExecutionState, TransactionEnvelope
from phantomx.nonce_binding import bind_nonce
from phantomx.nonce_manager import NonceManager
from phantomx.sqlite_transaction_store import SQLiteTransactionStore
from phantomx.transaction_record import build_signed_record


class SQLiteTransactionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "transactions.sqlite3"
        sender = "0x0000000000000000000000000000000000000002"
        executor = "0x0000000000000000000000000000000000000001"
        envelope = TransactionEnvelope(137, sender, executor, 42, b"authorized-calldata", 300_000, 100, 30)
        provisional = ExecutionIntent(137, executor, sender, "0x0000000000000000000000000000000000000003", 1_000_000, "0xroute", "0x0", "0xeconomic", "0xsimulation", 42, 2_000)
        intent = provisional.with_field(calldata_hash=envelope.calldata_hash)
        authorization = Authorization(intent.intent_hash(), intent.calldata_hash, intent.economic_proof_hash, intent.simulation_proof_hash, 137, executor, sender, 42, 2_000, 300_000, 100, 30)
        reservation = NonceManager(42).reserve(sender, "reservation-42")
        bound = bind_nonce(reservation, intent, authorization)
        self.intent, self.authorization, self.envelope, self.bound = intent, authorization, envelope, bound
        self.tx_hash = "0x" + "11" * 32
        self.store = SQLiteTransactionStore(self.path)
        self.record = build_signed_record(intent, authorization, envelope, bound, self.tx_hash)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_restart_persists_exact_record(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        record_hash = self.record.record_hash()
        restarted = SQLiteTransactionStore(self.path)
        loaded = restarted.get(record_hash)
        self.assertEqual(loaded, self.record)
        self.assertEqual(loaded.record_hash(), record_hash)
        self.assertEqual(restarted.get_by_tx_hash(self.tx_hash), self.record)

    def test_duplicate_transaction_hash_is_rejected_without_extra_record(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        with self.assertRaises(ValueError):
            self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        self.assertEqual(len(self.store.records()), 1)

    def test_intent_mutation_cannot_be_persisted(self):
        mutated = replace(self.record, intent_hash="0x" + "aa" * 32)
        with self.assertRaises(ValueError):
            self.store.create(mutated, intent=self.intent, bound_nonce=self.bound)
        self.assertEqual(self.store.records(), [])

    def test_nonce_mutation_cannot_be_persisted(self):
        mutated = replace(self.record, nonce=43)
        with self.assertRaises(ValueError):
            self.store.create(mutated, intent=self.intent, bound_nonce=self.bound)
        self.assertEqual(self.store.records(), [])

    def test_atomic_lifecycle_survives_restart(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        record_hash = self.record.record_hash()
        for state in (ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PENDING, ExecutionState.INCLUDED, ExecutionState.RECONCILED, ExecutionState.PROFIT_CONFIRMED):
            self.store.transition(record_hash, state)
            restarted = SQLiteTransactionStore(self.path)
            self.assertEqual(restarted.get(record_hash).state, state)

    def test_invalid_transition_does_not_mutate_state(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        record_hash = self.record.record_hash()
        with self.assertRaises(ValueError):
            self.store.transition(record_hash, ExecutionState.INCLUDED)
        self.assertEqual(self.store.get(record_hash).state, ExecutionState.SIGNED)

    def test_terminal_state_cannot_restart(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        record_hash = self.record.record_hash()
        self.store.transition(record_hash, ExecutionState.PROFIT_FAILED)
        with self.assertRaises(ValueError):
            self.store.transition(record_hash, ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(self.store.get(record_hash).state, ExecutionState.PROFIT_FAILED)

    def test_replacement_requires_active_source_and_exact_linkage(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        self.store.transition(self.record.record_hash(), ExecutionState.PRIVATE_SUBMITTED)
        replacement_hash = "0x" + "22" * 32
        replacement = replace(self.record, tx_hash=replacement_hash, replacement_of=self.tx_hash)
        stored = self.store.create_replacement(replacement, intent=self.intent, bound_nonce=self.bound, replaces_tx_hash=self.tx_hash)
        self.assertEqual(stored.replacement_of, self.tx_hash)
        self.assertEqual(self.store.get_by_tx_hash(replacement_hash).nonce, self.record.nonce)

    def test_replacement_wrong_source_is_rejected(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        replacement = replace(self.record, tx_hash="0x" + "22" * 32, replacement_of="0x" + "33" * 32)
        with self.assertRaises((ValueError, KeyError)):
            self.store.create_replacement(replacement, intent=self.intent, bound_nonce=self.bound, replaces_tx_hash="0x" + "33" * 32)
        self.assertEqual(len(self.store.records()), 1)

    def test_crash_like_restart_preserves_incomplete_signed_record(self):
        self.store.create(self.record, intent=self.intent, bound_nonce=self.bound)
        restarted = SQLiteTransactionStore(self.path)
        recovered = restarted.get(self.record.record_hash())
        self.assertEqual(recovered.state, ExecutionState.SIGNED)
        self.assertEqual(recovered.tx_hash, self.tx_hash)
        self.assertEqual(recovered.nonce, self.bound.nonce)


if __name__ == "__main__":
    unittest.main(verbosity=2)
