import unittest

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_observation import ExecutionObservationError, persist_chain_observation
from phantomx.execution_reconciliation import ExecutionReconciliationError, reconcile_included_execution
from phantomx.execution_submission import submit_prepared_execution
from phantomx.settlement import ReceiptRecord

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


class ExecutionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutionSubmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store
        self.prepared = self.fixture._prepare()
        submit_prepared_execution(store=self.store, prepared=self.prepared, relay=FakeRelay(), now=self.fixture.now)
        self.tx_hash = self.prepared.signed_transaction.transaction_hash
        self.included_observation = ObservationDecision(
            state=ChainObservationState.INCLUDED,
            tx_hash=self.tx_hash,
            replacement_tx_hash=None,
            evidence_reason="canonical successful receipt",
        )
        persist_chain_observation(
            store=self.store,
            intent=self.prepared.assembly.intent,
            observation=self.included_observation,
            tx_nonce=self.prepared.assembly.intent.nonce,
            pending_nonce=self.prepared.assembly.intent.nonce + 1,
            block_hash="0x" + "12" * 32,
            block_number=6000,
            canonical_block_hash="0x" + "12" * 32,
        )

    def _receipt(self):
        return ReceiptRecord(
            tx_hash=self.tx_hash,
            status=1,
            gas_used=21_000,
            effective_gas_price=100,
            block_number=6000,
        )

    def test_realized_profit_above_strict_floor_confirms(self):
        receipt = self._receipt()
        self.assertEqual(receipt.gas_cost_wei, 2_100_000)
        result = reconcile_included_execution(
            store=self.store,
            intent=self.prepared.assembly.intent,
            observation=self.included_observation,
            receipt=receipt,
            final_settlement="101.00",
            flash_repayment="100.00",
            costs=CostBreakdown(flash_loan_fee="0.05", dex_fees="0.02", gas="0.01", relay="0.01", other="0.01"),
        )
        self.assertEqual(result.transaction_state, ExecutionState.PROFIT_CONFIRMED)
        self.assertTrue(result.settlement_record.profit_confirmed)
        self.assertEqual(result.settlement_record.realized_net_profit_usd, result.reconciliation.settlement.realized_net_profit)
        self.assertEqual(self.store.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.PROFIT_CONFIRMED)
        self.assertEqual(self.store.get_nonce(self.prepared.assembly.intent.sender, self.prepared.assembly.intent.nonce).status.value, "INCLUDED")

    def test_exact_twenty_cents_fails_strict_floor(self):
        result = reconcile_included_execution(
            store=self.store,
            intent=self.prepared.assembly.intent,
            observation=self.included_observation,
            receipt=self._receipt(),
            final_settlement="100.30",
            flash_repayment="100.00",
            costs=CostBreakdown(gas="0.10"),
        )
        self.assertEqual(result.transaction_state, ExecutionState.PROFIT_FAILED)
        self.assertFalse(result.settlement_record.profit_confirmed)
        self.assertEqual(result.settlement_record.realized_net_profit_usd, result.reconciliation.settlement.realized_net_profit)

    def test_settlement_is_idempotent_but_conflicting_evidence_is_rejected(self):
        kwargs = dict(
            store=self.store,
            intent=self.prepared.assembly.intent,
            observation=self.included_observation,
            receipt=self._receipt(),
            final_settlement="101.00",
            flash_repayment="100.00",
            costs=CostBreakdown(flash_loan_fee="0.05", dex_fees="0.02", gas="0.01", relay="0.01", other="0.01"),
        )
        first = reconcile_included_execution(**kwargs)
        self.assertEqual(first.settlement_record.record_hash, reconcile_included_execution(**kwargs).settlement_record.record_hash)
        conflicting = dict(kwargs)
        conflicting["final_settlement"] = "101.01"
        with self.assertRaises(ExecutionReconciliationError):
            reconcile_included_execution(**conflicting)

    def test_noncanonical_observation_is_rejected_before_accounting(self):
        bad_observation = ObservationDecision(
            state=ChainObservationState.INCLUDED,
            tx_hash=self.tx_hash,
            replacement_tx_hash=None,
            evidence_reason="bad canonical identity",
        )
        with self.assertRaises(ExecutionObservationError):
            persist_chain_observation(
                store=self.store,
                intent=self.prepared.assembly.intent,
                observation=bad_observation,
                tx_nonce=self.prepared.assembly.intent.nonce,
                block_hash="0x" + "12" * 32,
                block_number=6000,
                canonical_block_hash="0x" + "34" * 32,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
