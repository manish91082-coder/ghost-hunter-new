"""Adversarial tests for the unified Phase-19 SQLite execution boundary."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from phantomx.chain_observer import ChainObservationState
from phantomx.execution import Authorization, ExecutionIntent, ExecutionState, TransactionEnvelope
from phantomx.nonce_manager import NonceManager
from phantomx.nonce_binding import bind_nonce
from phantomx.recovery_coordinator import RecoveryAction, RecoveryDecision
from phantomx.sqlite_execution_store import SQLiteExecutionStore
from phantomx.transaction_record import build_signed_record


class SQLiteExecutionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "execution.sqlite3"
        self.sender = "0x0000000000000000000000000000000000000002"
        self.executor = "0x0000000000000000000000000000000000000001"
        envelope = TransactionEnvelope(137, self.sender, self.executor, 42, b"authorized-calldata", 300_000, 100, 30)
        provisional = ExecutionIntent(137, self.executor, self.sender, "0x0000000000000000000000000000000000000003", 1_000_000, "0xroute", "0x0", "0xeconomic", "0xsimulation", 42, 2_000)
        self.intent = provisional.with_field(calldata_hash=envelope.calldata_hash)
        self.authorization = Authorization(self.intent.intent_hash(), self.intent.calldata_hash, self.intent.economic_proof_hash, self.intent.simulation_proof_hash, 137, self.executor, self.sender, 42, 2_000, 300_000, 100, 30)
        reservation = NonceManager(42).reserve(self.sender, "reservation-42")
        self.bound = bind_nonce(reservation, self.intent, self.authorization)
        self.tx_hash = "0x" + "11" * 32
        self.record = build_signed_record(self.intent, self.authorization, envelope, self.bound, self.tx_hash)
        self.store = SQLiteExecutionStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def _seed_signed(self):
        self.store.reserve_nonce(self.sender, self.bound.reservation_id, self.intent.intent_hash(), chain_pending_nonce=42)
        self.store.create_signed_transaction(self.record, intent=self.intent, bound_nonce=self.bound)

    def test_reserve_and_sign_are_one_durable_domain(self):
        self._seed_signed()
        restarted = SQLiteExecutionStore(self.path)
        self.assertEqual(restarted.get_nonce(self.sender, 42).status.value, "SIGNED")
        self.assertEqual(restarted.get_transaction(self.record.record_hash()).state, ExecutionState.SIGNED)

    def test_failed_signed_creation_rolls_back_nonce_state(self):
        self.store.reserve_nonce(self.sender, self.bound.reservation_id, self.intent.intent_hash(), chain_pending_nonce=42)
        bad = replace(self.record, tx_hash="not-a-valid-hash")
        with self.assertRaises(Exception):
            self.store.create_signed_transaction(bad, intent=self.intent, bound_nonce=self.bound)
        restarted = SQLiteExecutionStore(self.path)
        self.assertEqual(restarted.get_nonce(self.sender, 42).status.value, "RESERVED")
        self.assertEqual(restarted.next_nonce(self.sender), 43)
        self.assertEqual(len(restarted.pending_journal()), 0)

    def test_recovery_updates_transaction_nonce_and_journal_together(self):
        self._seed_signed()
        db = self.store._connect()
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE nonce_records SET status=? WHERE sender=? AND nonce=?", ("SUBMITTED", self.sender, 42))
        db.execute("UPDATE transaction_records SET state=? WHERE record_hash=?", (ExecutionState.PENDING.value, self.record.record_hash()))
        db.execute("COMMIT")
        db.close()
        decision = RecoveryDecision(self.record.record_hash(), RecoveryAction.RECONCILE_INCLUDED, "canonical successful receipt")
        result = self.store.apply_recovery(decision=decision, chain_state=ChainObservationState.INCLUDED.value, tx_hash=self.tx_hash, replacement_tx_hash=None, transaction_state=ExecutionState.INCLUDED, nonce_state=__import__('phantomx.durable_nonce', fromlist=['NonceStatus']).NonceStatus.INCLUDED, intent=self.intent)
        self.assertEqual(result.transaction.state, ExecutionState.INCLUDED)
        self.assertEqual(result.nonce.status.value, "INCLUDED")
        self.assertEqual(self.store.pending_journal(), [])
        restarted = SQLiteExecutionStore(self.path)
        self.assertEqual(restarted.get_transaction(self.record.record_hash()).state, ExecutionState.INCLUDED)
        self.assertEqual(restarted.get_nonce(self.sender, 42).status.value, "INCLUDED")

    def test_recovery_idempotency_does_not_double_apply(self):
        self._seed_signed()
        db = self.store._connect()
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE nonce_records SET status=? WHERE sender=? AND nonce=?", ("SUBMITTED", self.sender, 42))
        db.execute("UPDATE transaction_records SET state=? WHERE record_hash=?", (ExecutionState.PENDING.value, self.record.record_hash()))
        db.execute("COMMIT")
        db.close()
        decision = RecoveryDecision(self.record.record_hash(), RecoveryAction.RECONCILE_INCLUDED, "canonical successful receipt")
        kwargs = dict(decision=decision, chain_state=ChainObservationState.INCLUDED.value, tx_hash=self.tx_hash, replacement_tx_hash=None, transaction_state=ExecutionState.INCLUDED, nonce_state=__import__('phantomx.durable_nonce', fromlist=['NonceStatus']).NonceStatus.INCLUDED, intent=self.intent)
        first = self.store.apply_recovery(**kwargs)
        second = self.store.apply_recovery(**kwargs)
        self.assertEqual(first.journal_sequence, second.journal_sequence)
        self.assertEqual(len(self.store.pending_journal()), 0)

    def test_recovery_rejects_intent_mutation_without_state_change(self):
        self._seed_signed()
        decision = RecoveryDecision(self.record.record_hash(), RecoveryAction.RECONCILE_INCLUDED, "canonical successful receipt")
        with self.assertRaises(ValueError):
            self.store.apply_recovery(decision=decision, chain_state=ChainObservationState.INCLUDED.value, tx_hash=self.tx_hash, replacement_tx_hash=None, transaction_state=ExecutionState.INCLUDED, nonce_state=__import__('phantomx.durable_nonce', fromlist=['NonceStatus']).NonceStatus.INCLUDED, intent=replace(self.intent, loan_amount=999999))
        self.assertEqual(self.store.get_transaction(self.record.record_hash()).state, ExecutionState.SIGNED)
        self.assertEqual(self.store.get_nonce(self.sender, 42).status.value, "SIGNED")
        self.assertEqual(self.store.pending_journal(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
