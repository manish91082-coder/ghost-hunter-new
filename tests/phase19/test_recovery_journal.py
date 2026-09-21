"""Tests for durable idempotent recovery decisions."""

from pathlib import Path
import tempfile
import unittest

from phantomx.chain_observer import ChainEvidence, observe
from phantomx.recovery_coordinator import RecoveryAction, recover
from phantomx.recovery_journal import SQLiteRecoveryJournal
from phantomx.execution import ExecutionState


class RecoveryJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "recovery.sqlite3"
        self.tx_hash = "0x" + "11" * 32
        observation = observe(ChainEvidence(self.tx_hash, 42, 43, False, False, None, None, None, None))
        self.observation = observation
        self.decision = recover("0x" + "aa" * 32, ExecutionState.PENDING, observation)
        self.journal = SQLiteRecoveryJournal(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_survives_restart(self):
        entry = self.journal.append(self.decision, self.observation)
        restarted = SQLiteRecoveryJournal(self.path)
        pending = restarted.pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].sequence, entry.sequence)
        self.assertEqual(pending[0].action, RecoveryAction.ELIGIBLE_FOR_REPLACEMENT_REVIEW)

    def test_append_is_idempotent(self):
        first = self.journal.append(self.decision, self.observation)
        second = self.journal.append(self.decision, self.observation)
        self.assertEqual(first.sequence, second.sequence)
        self.assertEqual(len(self.journal.pending()), 1)

    def test_mark_applied_is_persistent(self):
        entry = self.journal.append(self.decision, self.observation)
        applied = self.journal.mark_applied(entry.sequence)
        self.assertTrue(applied.applied)
        restarted = SQLiteRecoveryJournal(self.path)
        self.assertEqual(restarted.pending(), [])

    def test_unknown_sequence_fails(self):
        with self.assertRaises(KeyError):
            self.journal.mark_applied(999)

    def test_journal_preserves_replacement_hash_evidence(self):
        replacement = "0x" + "22" * 32
        observation = observe(ChainEvidence(self.tx_hash, 42, 42, True, False, None, None, None, None, replacement))
        decision = recover("0x" + "aa" * 32, ExecutionState.PENDING, observation)
        entry = self.journal.append(decision, observation)
        self.assertEqual(entry.replacement_tx_hash, replacement)


if __name__ == "__main__":
    unittest.main(verbosity=2)
