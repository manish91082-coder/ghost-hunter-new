"""Crash/restart recovery audit tests."""
import tempfile
import unittest
from pathlib import Path

from phantomx.durable_nonce import NonceStatus
from phantomx.execution import ExecutionIntent, ExecutionState, TransactionEnvelope
from phantomx.execution_recovery import RecoveryAuditState, audit_store
from phantomx.nonce_manager import NonceManager
from phantomx.nonce_binding import bind_nonce
from phantomx.execution import Authorization
from phantomx.sqlite_execution_store import SQLiteExecutionStore
from phantomx.transaction_record import build_signed_record


class ExecutionRecoveryAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteExecutionStore(Path(self.tmp.name) / "execution.sqlite3")
        self.sender = "0x0000000000000000000000000000000000000002"
        self.executor = "0x0000000000000000000000000000000000000001"
        envelope = TransactionEnvelope(137, self.sender, self.executor, 7, b"calldata", 300000, 100, 30)
        base = ExecutionIntent(137, self.executor, self.sender, "0x0000000000000000000000000000000000000003", 1000, "route", "0x0", "economic", "simulation", 7, 1000)
        self.intent = base.with_field(calldata_hash=envelope.calldata_hash)
        auth = Authorization(self.intent.intent_hash(), self.intent.calldata_hash, self.intent.economic_proof_hash, self.intent.simulation_proof_hash, 137, self.executor, self.sender, 7, 1000, 300000, 100, 30)
        reservation = NonceManager(7).reserve(self.sender, "r7")
        bound = bind_nonce(reservation, self.intent, auth)
        record = build_signed_record(self.intent, auth, envelope, bound, "0x" + "22" * 32)
        self.store.reserve_nonce(self.sender, "r7", self.intent.intent_hash(), chain_pending_nonce=7)
        self.store.create_signed_transaction(record, intent=self.intent, bound_nonce=bound)
        self.record = record

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_restart_audit(self):
        result = audit_store(SQLiteExecutionStore(self.store.path))
        self.assertEqual(result.state, RecoveryAuditState.CLEAN)
        self.assertEqual(result.checked_transactions, 1)
        self.assertEqual(result.checked_nonces, 1)

    def test_corrupt_nonce_intent_is_inconsistent(self):
        with self.store._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE nonce_records SET intent_hash=? WHERE sender=? AND nonce=?", ("corrupt", self.sender, 7))
            db.execute("COMMIT")
        result = audit_store(SQLiteExecutionStore(self.store.path))
        self.assertEqual(result.state, RecoveryAuditState.INCONSISTENT)
        self.assertTrue(any("intent mismatch" in item for item in result.anomalies))

    def test_missing_nonce_is_inconsistent(self):
        with self.store._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM nonce_records WHERE sender=? AND nonce=?", (self.sender, 7))
            db.execute("COMMIT")
        result = audit_store(SQLiteExecutionStore(self.store.path))
        self.assertEqual(result.state, RecoveryAuditState.INCONSISTENT)
        self.assertTrue(any("missing nonce record" in item for item in result.anomalies))

    def test_active_nonce_without_tx_hash_is_inconsistent(self):
        with self.store._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE nonce_records SET tx_hash=NULL WHERE sender=? AND nonce=?", (self.sender, 7))
            db.execute("COMMIT")
        result = audit_store(SQLiteExecutionStore(self.store.path))
        self.assertEqual(result.state, RecoveryAuditState.INCONSISTENT)
        self.assertTrue(any("active state without tx hash" in item for item in result.anomalies))


if __name__ == "__main__":
    unittest.main(verbosity=2)
