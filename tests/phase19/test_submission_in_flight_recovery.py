"""Adversarial tests for resolving uncertain private relay outcomes."""

import unittest

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_recovery import persist_recovery_observation
from phantomx.durable_nonce import NonceStatus
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_chain_observation
from phantomx.execution_recovery import RecoveryAuditState, audit_store
from phantomx.recovery_coordinator import RecoveryAction, recover
from phantomx.execution_submission import ExecutionSubmissionError, submit_prepared_execution

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


class SubmissionInFlightRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutionSubmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store
        self.prepared = self.fixture._prepare()
        self.tx_hash = self.prepared.signed_transaction.transaction_hash
        self.intent = self.prepared.assembly.intent
        self.nonce = self.intent.nonce

    def _enter_in_flight(self):
        with self.assertRaisesRegex(ExecutionSubmissionError, "outcome is uncertain"):
            submit_prepared_execution(
                store=self.store,
                prepared=self.prepared,
                relay=FakeRelay(fail=True),
                now=self.fixture.now,
                submission_authority=self.prepared.authority,
            )
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.SUBMISSION_IN_FLIGHT,
        )
        self.assertEqual(self.store.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.SIGNED)

    def test_pending_observation_resolves_in_flight_after_restart(self):
        self._enter_in_flight()
        reopened = type(self.store)(self.store.path)
        result = persist_chain_observation(
            store=reopened,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.PENDING,
                self.tx_hash,
                None,
                "transaction remains pending after uncertain relay outcome",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce,
        )
        self.assertEqual(result.transaction_state, ExecutionState.PENDING)
        self.assertEqual(result.nonce_state, NonceStatus.SUBMITTED)
        self.assertEqual(reopened.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.PENDING)
        self.assertEqual(reopened.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.SUBMITTED)

    def test_included_observation_resolves_in_flight_after_restart(self):
        self._enter_in_flight()
        reopened = type(self.store)(self.store.path)
        result = persist_chain_observation(
            store=reopened,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.INCLUDED,
                self.tx_hash,
                None,
                "canonical receipt observed after uncertain relay outcome",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash="0x" + "11" * 32,
            block_number=8000,
            canonical_block_hash="0x" + "11" * 32,
        )
        self.assertEqual(result.transaction_state, ExecutionState.INCLUDED)
        self.assertEqual(result.nonce_state, NonceStatus.INCLUDED)
        self.assertEqual(reopened.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.INCLUDED)

    def test_drop_evidence_can_close_in_flight_for_replacement_review(self):
        self._enter_in_flight()
        result = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.DROPPED,
                self.tx_hash,
                None,
                "sender pending nonce advanced beyond uncertain transaction",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
        )
        self.assertEqual(result.transaction_state, ExecutionState.DROPPED)
        self.assertEqual(result.nonce_state, NonceStatus.DROPPED)
        self.assertEqual(result.action, RecoveryAction.ELIGIBLE_FOR_REPLACEMENT_REVIEW)

    def test_reorg_evidence_can_move_in_flight_to_reobserve(self):
        self._enter_in_flight()
        result = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.REORGED,
                self.tx_hash,
                None,
                "canonical block identity changed during uncertain submission recovery",
            ),
            tx_nonce=self.nonce,
            block_hash="0x" + "11" * 32,
            block_number=8000,
            canonical_block_hash="0x" + "22" * 32,
        )
        self.assertEqual(result.transaction_state, ExecutionState.REORGED)
        self.assertEqual(result.nonce_state, NonceStatus.REORGED)
        self.assertEqual(result.action, RecoveryAction.REOBSERVE)

    def test_startup_audit_accepts_durable_in_flight_state(self):
        self._enter_in_flight()
        reopened = type(self.store)(self.store.path)
        audit = audit_store(reopened)
        self.assertEqual(audit.state, RecoveryAuditState.CLEAN)
        self.assertEqual(audit.anomalies, ())

    def test_recovery_policy_never_reopens_in_flight_to_signed(self):
        for chain_state in (
            ChainObservationState.PENDING,
            ChainObservationState.INCLUDED,
            ChainObservationState.REVERTED,
            ChainObservationState.DROPPED,
            ChainObservationState.REPLACED,
            ChainObservationState.REORGED,
        ):
            replacement = "0x" + "22" * 32 if chain_state is ChainObservationState.REPLACED else None
            observation = ObservationDecision(chain_state, self.tx_hash, replacement, "evidence")
            decision = recover("record", ExecutionState.SUBMISSION_IN_FLIGHT, observation)
            self.assertNotEqual(decision.action, RecoveryAction.BLOCK, chain_state.value)
            self.assertNotIn("SIGNED", decision.reason)

    def test_in_flight_state_survives_restart_without_creating_submitted_hash(self):
        self._enter_in_flight()
        reopened = type(self.store)(self.store.path)
        self.assertEqual(
            reopened.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.SUBMISSION_IN_FLIGHT,
        )
        self.assertEqual(reopened.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.SIGNED)
        self.assertIsNone(reopened.get_nonce(self.intent.sender, self.nonce).tx_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)

# Certification note: uncertain private relay outcomes remain fenced until explicit chain evidence resolves them.
