"""Phase-19 adversarial tests for the non-negotiable execution invariants.

These tests are deliberately dependency-free. They validate policy and data
contracts only. They do NOT claim Polygon execution, fork execution, or
production signing has been proven.
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.economics import CostBreakdown, RealizedSettlement, strict_profit_ok
from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope


class StrictProfitTests(unittest.TestCase):
    def test_below_floor_rejected(self):
        self.assertFalse(strict_profit_ok(Decimal("0.199999")))

    def test_exact_floor_rejected(self):
        self.assertFalse(strict_profit_ok(Decimal("0.200000")))

    def test_above_floor_accepted(self):
        self.assertTrue(strict_profit_ok(Decimal("0.200001")))

    def test_all_costs_are_subtracted(self):
        costs = CostBreakdown(
            flash_loan_fee=Decimal("0.10"),
            dex_fees=Decimal("0.20"),
            price_impact=Decimal("0.10"),
            gas=Decimal("0.15"),
            relay=Decimal("0.05"),
            other=Decimal("0.01"),
        )
        settlement = RealizedSettlement(
            final_settlement=Decimal("101.00"),
            flash_repayment=Decimal("100.00"),
            costs=costs,
        )
        self.assertEqual(settlement.realized_net_profit, Decimal("0.39"))
        self.assertTrue(settlement.profit_confirmed)

    def test_successful_trade_can_still_fail_profit_gate(self):
        settlement = RealizedSettlement(
            final_settlement=Decimal("100.50"),
            flash_repayment=Decimal("100.00"),
            costs=CostBreakdown(gas=Decimal("0.20"), relay=Decimal("0.11")),
        )
        self.assertFalse(settlement.profit_confirmed)


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            chain_id=137,
            executor="0x0000000000000000000000000000000000000001",
            sender="0x0000000000000000000000000000000000000002",
            loan_asset="0x0000000000000000000000000000000000000003",
            loan_amount=1_000_000,
            route_hash="0xroute",
            calldata_hash="0xcalldata",
            nonce=42,
            deadline=2_000,
        )
        self.authorization = Authorization(
            intent_hash=self.intent.intent_hash(),
            calldata_hash=self.intent.calldata_hash,
            chain_id=self.intent.chain_id,
            executor=self.intent.executor,
            sender=self.intent.sender,
            nonce=self.intent.nonce,
            deadline=self.intent.deadline,
        )

    def test_authorization_matches_unchanged_intent(self):
        self.assertTrue(self.authorization.matches(self.intent, now=1_000))

    def test_route_change_invalidates_authorization(self):
        mutated = self.intent.with_field(route_hash="0xchanged")
        self.assertFalse(self.authorization.matches(mutated, now=1_000))

    def test_loan_change_invalidates_authorization(self):
        mutated = self.intent.with_field(loan_amount=2_000_000)
        self.assertFalse(self.authorization.matches(mutated, now=1_000))

    def test_nonce_change_invalidates_authorization(self):
        mutated = self.intent.with_field(nonce=43)
        self.assertFalse(self.authorization.matches(mutated, now=1_000))

    def test_expired_authorization_rejected(self):
        self.assertFalse(self.authorization.matches(self.intent, now=2_001))

    def test_calldata_mutation_changes_envelope_hash(self):
        first = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"A", 300_000, 100, 30)
        second = TransactionEnvelope(137, self.intent.sender, self.intent.executor, 42, b"B", 300_000, 100, 30)
        self.assertNotEqual(first.calldata_hash, second.calldata_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)
