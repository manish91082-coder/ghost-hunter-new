"""Adversarial tests for restart recovery decisions."""

import unittest

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.execution import ExecutionState
from phantomx.recovery_coordinator import RecoveryAction, recover


class RecoveryCoordinatorTests(unittest.TestCase):
    def decision(self, state, replacement=None):
        return ObservationDecision(state, "0x" + "11" * 32, replacement, "evidence")

    def test_pending_holds(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.PENDING))
        self.assertEqual(d.action, RecoveryAction.HOLD)

    def test_not_found_holds(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.NOT_FOUND))
        self.assertEqual(d.action, RecoveryAction.HOLD)

    def test_unknown_holds(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.UNKNOWN))
        self.assertEqual(d.action, RecoveryAction.HOLD)

    def test_included_requires_settlement(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.INCLUDED))
        self.assertEqual(d.action, RecoveryAction.RECONCILE_INCLUDED)

    def test_reverted_does_not_imply_replacement(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.REVERTED))
        self.assertEqual(d.action, RecoveryAction.MARK_REVERTED)

    def test_drop_allows_only_replacement_review(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.DROPPED))
        self.assertEqual(d.action, RecoveryAction.ELIGIBLE_FOR_REPLACEMENT_REVIEW)

    def test_drop_never_directly_submits_replacement(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.DROPPED))
        self.assertNotEqual(d.action, RecoveryAction.REVIEW_REPLACEMENT)

    def test_reorg_requires_reobservation(self):
        d = recover("record", ExecutionState.INCLUDED, self.decision(ChainObservationState.REORGED))
        self.assertEqual(d.action, RecoveryAction.REOBSERVE)

    def test_explicit_replacement_requires_reconciliation(self):
        replacement = "0x" + "22" * 32
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.REPLACED, replacement))
        self.assertEqual(d.action, RecoveryAction.REVIEW_REPLACEMENT)

    def test_replacement_without_hash_blocks(self):
        d = recover("record", ExecutionState.PENDING, self.decision(ChainObservationState.REPLACED))
        self.assertEqual(d.action, RecoveryAction.BLOCK)

    def test_terminal_state_blocks_restart_actions(self):
        d = recover("record", ExecutionState.PROFIT_CONFIRMED, self.decision(ChainObservationState.DROPPED))
        self.assertEqual(d.action, RecoveryAction.BLOCK)

    def test_chain_lifecycle_conflict_blocks(self):
        d = recover("record", ExecutionState.SIGNED, self.decision(ChainObservationState.INCLUDED))
        self.assertEqual(d.action, RecoveryAction.BLOCK)

    def test_reverted_lifecycle_conflict_blocks(self):
        d = recover("record", ExecutionState.SIGNED, self.decision(ChainObservationState.REVERTED))
        self.assertEqual(d.action, RecoveryAction.BLOCK)


if __name__ == "__main__":
    unittest.main(verbosity=2)
