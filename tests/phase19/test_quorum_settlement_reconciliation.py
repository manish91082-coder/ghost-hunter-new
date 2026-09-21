import unittest

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_chain_observation
from phantomx.execution_reconciliation import (
    ExecutionReconciliationError,
    reconcile_quorum_included_execution,
)
from phantomx.production_chain_observation import QuorumChainObservation
from phantomx.production_chain_observation_store import persist_quorum_chain_observation
from phantomx.execution_submission import submit_prepared_execution
from phantomx.settlement import ReceiptRecord

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


BLOCK_HASH = "0x" + "12" * 32


class QuorumSettlementReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutionSubmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store
        self.prepared = self.fixture._prepare()
        submit_prepared_execution(
            store=self.store,
            prepared=self.prepared,
            relay=FakeRelay(),
            now=self.fixture.now,
            submission_authority=self.prepared.authority,
        )
        self.intent = self.prepared.assembly.intent
        self.tx_hash = self.prepared.signed_transaction.transaction_hash
        self.observation = ObservationDecision(
            ChainObservationState.INCLUDED,
            self.tx_hash,
            None,
            "canonical successful receipt",
        )
        persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=self.observation,
            tx_nonce=self.intent.nonce,
            pending_nonce=self.intent.nonce + 1,
            block_hash=BLOCK_HASH,
            block_number=6000,
            canonical_block_hash=BLOCK_HASH,
        )

    def _quorum(self, block=100, providers=("provider-a", "provider-b")):
        return QuorumChainObservation(
            schema_version=1,
            chain_id=137,
            tx_hash=self.tx_hash,
            decision=self.observation,
            common_observed_block=block,
            attesting_provider_names=providers,
        )

    def _receipt(self):
        return ReceiptRecord(
            tx_hash=self.tx_hash,
            status=1,
            gas_used=21_000,
            effective_gas_price=100,
            block_number=6000,
        )

    def _settle(self, quorum, **overrides):
        kwargs = dict(
            store=self.store,
            intent=self.intent,
            quorum_observation=quorum,
            observation=self.observation,
            current_observed_block=105,
            maximum_age_blocks=5,
            minimum_attesting_providers=2,
            receipt=self._receipt(),
            block_hash=BLOCK_HASH,
            canonical_block_hash=BLOCK_HASH,
            final_settlement="101.00",
            flash_repayment="100.00",
            costs=CostBreakdown(gas="0.01", relay="0.01"),
        )
        kwargs.update(overrides)
        return reconcile_quorum_included_execution(**kwargs)

    def test_fresh_two_provider_quorum_can_reach_settlement(self):
        quorum = self._quorum()
        persist_quorum_chain_observation(
            store=self.store,
            intent_hash=self.intent.intent_hash(),
            observation=quorum,
        )
        result = self._settle(quorum)
        self.assertEqual(result.transaction_state, ExecutionState.PROFIT_CONFIRMED)

    def test_single_provider_quorum_is_blocked_before_settlement_mutation(self):
        quorum = self._quorum(providers=("provider-a",))
        persist_quorum_chain_observation(
            store=self.store,
            intent_hash=self.intent.intent_hash(),
            observation=quorum,
        )
        with self.assertRaisesRegex(ExecutionReconciliationError, "fresh quorum evidence"):
            self._settle(quorum)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.INCLUDED,
        )
        with self.store._connect() as db:
            settlement_count = db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='settlement_records'").fetchone()[0]
            if settlement_count:
                rows = db.execute("SELECT COUNT(*) FROM settlement_records").fetchone()[0]
            else:
                rows = 0
        self.assertEqual(rows, 0)

    def test_stale_quorum_is_blocked_before_settlement_mutation(self):
        quorum = self._quorum(block=99)
        persist_quorum_chain_observation(
            store=self.store,
            intent_hash=self.intent.intent_hash(),
            observation=quorum,
        )
        with self.assertRaisesRegex(ExecutionReconciliationError, "fresh quorum evidence"):
            self._settle(quorum)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.INCLUDED,
        )

    def test_observation_binding_mismatch_is_blocked_before_admission(self):
        quorum = self._quorum()
        persist_quorum_chain_observation(
            store=self.store,
            intent_hash=self.intent.intent_hash(),
            observation=quorum,
        )
        mismatched = ObservationDecision(
            ChainObservationState.INCLUDED,
            "0x" + "33" * 32,
            None,
            "mismatched transaction evidence",
        )
        with self.assertRaisesRegex(ExecutionReconciliationError, "transaction hash mismatch"):
            reconcile_quorum_included_execution(
                store=self.store,
                intent=self.intent,
                quorum_observation=quorum,
                observation=mismatched,
                current_observed_block=105,
                maximum_age_blocks=5,
                minimum_attesting_providers=2,
                receipt=self._receipt(),
                block_hash=BLOCK_HASH,
                canonical_block_hash=BLOCK_HASH,
                final_settlement="101.00",
                flash_repayment="100.00",
                costs=CostBreakdown(gas="0.01"),
            )
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.INCLUDED,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
