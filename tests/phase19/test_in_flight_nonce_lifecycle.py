"""Regression tests for the SIGNED-nonce to chain-proven lifecycle handoff."""

import unittest

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_nonce import NonceStatus
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_chain_observation
from phantomx.execution_submission import ExecutionSubmissionError, submit_prepared_execution

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


class InFlightNonceLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutionSubmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store
        self.prepared = self.fixture._prepare()
        self.intent = self.prepared.assembly.intent
        self.tx_hash = self.prepared.signed_transaction.transaction_hash
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
        self.assertIsNone(self.store.get_nonce(self.intent.sender, self.nonce).tx_hash)

    def test_pending_promotes_signed_nonce_only_after_exact_chain_evidence(self):
        self._enter_in_flight()
        result = persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.PENDING,
                self.tx_hash,
                None,
                "exact transaction remains pending after ambiguous relay result",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce,
        )
        self.assertEqual(result.transaction_state, ExecutionState.PENDING)
        self.assertEqual(result.nonce_state, NonceStatus.SUBMITTED)
        self.assertEqual(self.store.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.SUBMITTED)

    def test_included_promotes_signed_nonce_to_included(self):
        self._enter_in_flight()
        result = persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.INCLUDED,
                self.tx_hash,
                None,
                "exact canonical receipt observed after ambiguous relay result",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash="0x" + "11" * 32,
            block_number=9000,
            canonical_block_hash="0x" + "11" * 32,
        )
        self.assertEqual(result.transaction_state, ExecutionState.INCLUDED)
        self.assertEqual(result.nonce_state, NonceStatus.INCLUDED)
        self.assertEqual(self.store.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.INCLUDED)

    def test_reverted_promotes_signed_nonce_to_included_terminal_failure(self):
        self._enter_in_flight()
        result = persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.REVERTED,
                self.tx_hash,
                None,
                "exact canonical reverted receipt observed after ambiguous relay result",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash="0x" + "22" * 32,
            block_number=9001,
            canonical_block_hash="0x" + "22" * 32,
        )
        self.assertEqual(result.transaction_state, ExecutionState.PROFIT_FAILED)
        self.assertEqual(result.nonce_state, NonceStatus.INCLUDED)
        self.assertEqual(self.store.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.PROFIT_FAILED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
