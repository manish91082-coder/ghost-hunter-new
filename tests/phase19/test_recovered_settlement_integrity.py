"""Adversarial settlement and duplicate-authority tests after crash recovery."""

import unittest

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_nonce import NonceStatus
from phantomx.durable_recovery import DurableRecoveryError, persist_recovery_observation
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_chain_observation
from phantomx.execution_reconciliation import ExecutionReconciliationError, reconcile_included_execution
from phantomx.execution_submission import ExecutionSubmissionError, submit_prepared_execution
from phantomx.economics import CostBreakdown
from phantomx.settlement import ReceiptRecord

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay

BLOCK_HASH = "0x" + "44" * 32
OTHER_BLOCK_HASH = "0x" + "55" * 32


class RecoveredSettlementIntegrityTests(unittest.TestCase):
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

    def _observe_included(self):
        return persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.INCLUDED,
                self.tx_hash,
                None,
                "canonical receipt observed",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash=BLOCK_HASH,
            block_number=10000,
            canonical_block_hash=BLOCK_HASH,
        )

    def _observe_pending(self):
        return persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.PENDING,
                self.tx_hash,
                None,
                "transaction still pending after recovery",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce,
        )

    def _receipt(self, status=1, block_number=10000):
        return ReceiptRecord(
            tx_hash=self.tx_hash,
            status=status,
            gas_used=21_000,
            effective_gas_price=100,
            block_number=block_number,
        )

    def _settle(self, persisted_observation, block_hash=BLOCK_HASH, canonical_block_hash=BLOCK_HASH, **overrides):
        kwargs = dict(
            store=self.store,
            intent=self.intent,
            observation=persisted_observation.observation,
            receipt=self._receipt(),
            block_hash=block_hash,
            canonical_block_hash=canonical_block_hash,
            final_settlement="101.00",
            flash_repayment="100.00",
            costs=CostBreakdown(
                flash_loan_fee="0.05",
                dex_fees="0.02",
                gas="0.01",
                relay="0.01",
                other="0.01",
            ),
        )
        kwargs.update(overrides)
        return reconcile_included_execution(**kwargs)

    def test_pending_recovery_cannot_bypass_settlement(self):
        self._enter_in_flight()
        pending = self._observe_pending()
        with self.assertRaisesRegex(ExecutionReconciliationError, "settlement requires canonical INCLUDED observation"):
            self._settle(pending)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.PENDING,
        )

    def test_included_recovery_requires_canonical_receipt_before_profit_state(self):
        self._enter_in_flight()
        included = self._observe_included()
        with self.assertRaises(ExecutionReconciliationError):
            self._settle(included, canonical_block_hash=OTHER_BLOCK_HASH)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.INCLUDED,
        )

    def test_included_recovery_can_reach_profit_only_through_reconciliation(self):
        self._enter_in_flight()
        included = self._observe_included()
        result = self._settle(included)
        self.assertEqual(result.transaction_state, ExecutionState.PROFIT_CONFIRMED)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.PROFIT_CONFIRMED,
        )
        self.assertTrue(result.settlement_record.profit_confirmed)

    def test_reorged_recovery_cannot_bypass_reobservation_or_settlement(self):
        self._enter_in_flight()
        self._observe_included()
        reorged = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.REORGED,
                self.tx_hash,
                None,
                "previous inclusion no longer canonical",
            ),
            tx_nonce=self.nonce,
            block_hash=BLOCK_HASH,
            block_number=10000,
            canonical_block_hash=OTHER_BLOCK_HASH,
        )
        self.assertEqual(reorged.transaction_state, ExecutionState.REORGED)
        with self.assertRaises(ExecutionReconciliationError):
            self._settle(
                self._make_stale_included_observation(),
                block_hash=BLOCK_HASH,
                canonical_block_hash=BLOCK_HASH,
            )
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.REORGED,
        )

    def _make_stale_included_observation(self):
        return type("PersistedObservation", (), {
            "observation": ObservationDecision(
                ChainObservationState.INCLUDED,
                self.tx_hash,
                None,
                "stale inclusion evidence",
            )
        })()

    def test_recovery_cannot_create_second_submission_from_pending_state(self):
        self._enter_in_flight()
        self._observe_pending()
        relay = FakeRelay()
        with self.assertRaises(ExecutionSubmissionError):
            submit_prepared_execution(
                store=self.store,
                prepared=self.prepared,
                relay=relay,
                now=self.fixture.now,
                submission_authority=self.prepared.authority,
            )
        self.assertEqual(relay.calls, 0)

    def test_recovery_cannot_create_second_submission_from_reorged_state(self):
        self._enter_in_flight()
        self._observe_included()
        persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.REORGED,
                self.tx_hash,
                None,
                "canonical block changed",
            ),
            tx_nonce=self.nonce,
            block_hash=BLOCK_HASH,
            block_number=10000,
            canonical_block_hash=OTHER_BLOCK_HASH,
        )
        relay = FakeRelay()
        with self.assertRaises(ExecutionSubmissionError):
            submit_prepared_execution(
                store=self.store,
                prepared=self.prepared,
                relay=relay,
                now=self.fixture.now,
                submission_authority=self.prepared.authority,
            )
        self.assertEqual(relay.calls, 0)

    def test_dropped_recovery_never_grants_replacement_submission_authority(self):
        self._enter_in_flight()
        dropped = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                ChainObservationState.DROPPED,
                self.tx_hash,
                None,
                "pending nonce advanced",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
        )
        self.assertEqual(dropped.transaction_state, ExecutionState.DROPPED)
        self.assertEqual(dropped.nonce_state, NonceStatus.DROPPED)
        relay = FakeRelay()
        with self.assertRaises(ExecutionSubmissionError):
            submit_prepared_execution(
                store=self.store,
                prepared=self.prepared,
                relay=relay,
                now=self.fixture.now,
                submission_authority=self.prepared.authority,
            )
        self.assertEqual(relay.calls, 0)

    def test_realized_profit_floor_remains_authoritative_after_recovery(self):
        self._enter_in_flight()
        included = self._observe_included()
        result = self._settle(
            included,
            final_settlement="100.30",
            costs=CostBreakdown(gas="0.10"),
        )
        self.assertEqual(result.transaction_state, ExecutionState.PROFIT_FAILED)
        self.assertFalse(result.settlement_record.profit_confirmed)

    def test_contradictory_reorg_evidence_is_rejected_without_lifecycle_change(self):
        self._enter_in_flight()
        self._observe_included()
        with self.assertRaises(DurableRecoveryError):
            persist_recovery_observation(
                store=self.store,
                intent=self.intent,
                observation=ObservationDecision(
                    ChainObservationState.REORGED,
                    self.tx_hash,
                    None,
                    "invalid unchanged canonical identity",
                ),
                tx_nonce=self.nonce,
                block_hash=BLOCK_HASH,
                block_number=10000,
                canonical_block_hash=BLOCK_HASH,
            )
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.INCLUDED,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
