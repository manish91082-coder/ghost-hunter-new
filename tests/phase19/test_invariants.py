"""Phase-19 adversarial tests for non-negotiable execution invariants."""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.controls import Lifecycle, NonceBook, ReplayRegistry
from phantomx.economics import CostBreakdown, RealizedSettlement, strict_profit_ok
from phantomx.execution import Authorization, ExecutionIntent, ExecutionState, TransactionEnvelope
from phantomx.settlement import ReceiptRecord, reconcile


class StrictProfitTests(unittest.TestCase):
    def test_below_floor_rejected(self):
        self.assertFalse(strict_profit_ok(Decimal("0.199999")))

    def test_exact_floor_rejected(self):
        self.assertFalse(strict_profit_ok(Decimal("0.200000")))

    def test_above_floor_accepted(self):
        self.assertTrue(strict_profit_ok(Decimal("0.200001")))

    def test_all_costs_are_subtracted(self):
        costs = CostBreakdown(Decimal("0.10"), Decimal("0.20"), Decimal("0.10"), Decimal("0.15"), Decimal("0.05"), Decimal("0.01"))
        settlement = RealizedSettlement(Decimal("101.00"), Decimal("100.00"), costs)
        self.assertEqual(settlement.realized_net_profit, Decimal("0.39"))
        self.assertTrue(settlement.profit_confirmed)

    def test_successful_trade_can_still_fail_profit_gate(self):
        settlement = RealizedSettlement(Decimal("100.50"), Decimal("100.00"), CostBreakdown(gas=Decimal("0.20"), relay=Decimal("0.11")))
        self.assertFalse(settlement.profit_confirmed)


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            137, "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
            "0x0000000000000000000000000000000000000003", 1_000_000,
            "0xroute", "0xcalldata", "0xeconomic", "0xsimulation", 42, 2_000,
        )
        self.authorization = Authorization(
            self.intent.intent_hash(), self.intent.calldata_hash,
            self.intent.economic_proof_hash, self.intent.simulation_proof_hash,
            self.intent.chain_id, self.intent.executor, self.intent.sender,
            self.intent.nonce, self.intent.deadline, 300_000, 100, 30,
        )

    def test_authorization_matches_unchanged_intent(self):
        self.assertTrue(self.authorization.matches(self.intent, now=1_000))

    def test_route_change_invalidates_authorization(self):
        self.assertFalse(self.authorization.matches(self.intent.with_field(route_hash="0xchanged"), 1_000))

    def test_loan_change_invalidates_authorization(self):
        self.assertFalse(self.authorization.matches(self.intent.with_field(loan_amount=2_000_000), 1_000))

    def test_economic_proof_change_invalidates_authorization(self):
        self.assertFalse(self.authorization.matches(self.intent.with_field(economic_proof_hash="0xchanged"), 1_000))

    def test_simulation_proof_change_invalidates_authorization(self):
        self.assertFalse(self.authorization.matches(self.intent.with_field(simulation_proof_hash="0xchanged"), 1_000))

    def test_nonce_change_invalidates_authorization(self):
        self.assertFalse(self.authorization.matches(self.intent.with_field(nonce=43), 1_000))

    def test_expired_authorization_rejected(self):
        self.assertFalse(self.authorization.matches(self.intent, now=2_001))

    def test_calldata_mutation_changes_envelope_hash(self):
        first = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"A", 300_000, 100, 30)
        second = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"B", 300_000, 100, 30)
        self.assertNotEqual(first.calldata_hash, second.calldata_hash)


class LifecycleTests(unittest.TestCase):
    def test_happy_path_reaches_profit_confirmation(self):
        lifecycle = Lifecycle()
        lifecycle.walk([
            ExecutionState.SIMULATED, ExecutionState.AUTHORIZED, ExecutionState.NONCE_RESERVED,
            ExecutionState.BUILT, ExecutionState.VERIFIED, ExecutionState.SIGNED,
            ExecutionState.PRIVATE_SUBMITTED, ExecutionState.PENDING, ExecutionState.INCLUDED,
            ExecutionState.RECONCILED, ExecutionState.PROFIT_CONFIRMED,
        ])
        self.assertEqual(lifecycle.state, ExecutionState.PROFIT_CONFIRMED)

    def test_terminal_state_cannot_restart(self):
        lifecycle = Lifecycle(ExecutionState.PROFIT_CONFIRMED)
        with self.assertRaises(ValueError):
            lifecycle.advance(ExecutionState.CREATED)

    def test_invalid_skip_is_rejected(self):
        with self.assertRaises(ValueError):
            Lifecycle().advance(ExecutionState.AUTHORIZED)


class ReplayAndNonceTests(unittest.TestCase):
    def test_intent_can_only_be_consumed_once(self):
        registry = ReplayRegistry()
        registry.consume("0xintent")
        with self.assertRaises(ValueError):
            registry.consume("0xintent")

    def test_distinct_intents_are_independent(self):
        registry = ReplayRegistry()
        registry.consume("0xa")
        registry.consume("0xb")
        self.assertTrue(registry.is_consumed("0xa"))
        self.assertTrue(registry.is_consumed("0xb"))

    def test_nonce_reservations_are_unique_and_monotonic(self):
        book = NonceBook(41)
        self.assertEqual([book.reserve(), book.reserve(), book.reserve()], [41, 42, 43])
        self.assertEqual(book.next_nonce, 44)


class ReceiptAccountingTests(unittest.TestCase):
    def test_successful_receipt_does_not_imply_profit(self):
        receipt = ReceiptRecord("0xtx", 1, 100_000, 30_000_000_000, 123)
        result = reconcile(receipt=receipt, final_settlement=Decimal("100.50"), flash_repayment=Decimal("100.00"), costs=CostBreakdown(gas=Decimal("0.20"), relay=Decimal("0.11")))
        self.assertTrue(result.successful)
        self.assertFalse(result.profit_confirmed)

    def test_reverted_receipt_cannot_confirm_profit(self):
        receipt = ReceiptRecord("0xtx", 0, 100_000, 30_000_000_000, 123)
        result = reconcile(receipt=receipt, final_settlement=Decimal("101.00"), flash_repayment=Decimal("100.00"), costs=CostBreakdown(gas=Decimal("0.01")))
        self.assertFalse(result.successful)
        self.assertFalse(result.profit_confirmed)

    def test_receipt_gas_cost_is_gas_used_times_effective_price(self):
        receipt = ReceiptRecord("0xtx", 1, 123_456, 7_000_000_000, 123)
        self.assertEqual(receipt.gas_cost_wei, 864_192_000_000_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
