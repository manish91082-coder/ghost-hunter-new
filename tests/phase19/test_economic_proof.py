import unittest
from decimal import Decimal

from phantomx.economic_proof import EconomicProofError, build_economic_proof
from phantomx.economics import CostBreakdown

ROUTE = "0x" + "11" * 32
QUOTE_A = "0x" + "22" * 32
QUOTE_B = "0x" + "33" * 32
VALUATION = "0x" + "44" * 32


class EconomicProofTests(unittest.TestCase):
    def costs(self, **overrides):
        values = {
            "flash_loan_fee": Decimal("0.10"),
            "dex_fees": Decimal("0.20"),
            "price_impact": Decimal("0.05"),
            "gas": Decimal("0.10"),
            "relay": Decimal("0.05"),
            "other": Decimal("0.05"),
        }
        values.update(overrides)
        return CostBreakdown(**values)

    def build(self, **overrides):
        values = {
            "route_hash": ROUTE,
            "quote_hashes": (QUOTE_A, QUOTE_B),
            "valuation_hash": VALUATION,
            "final_settlement_usd": Decimal("100.95"),
            "loan_principal_usd": Decimal("100.00"),
            "costs": self.costs(),
            "max_gas_usd": Decimal("0.10"),
            "max_relay_usd": Decimal("0.05"),
        }
        values.update(overrides)
        return build_economic_proof(**values)

    def test_worst_case_formula_and_strict_gate(self):
        proof = self.build()
        self.assertEqual(proof.gross_surplus_usd, Decimal("0.95"))
        self.assertEqual(proof.total_cost_usd, Decimal("0.55"))
        self.assertEqual(proof.worst_case_net_profit_usd, Decimal("0.40"))
        self.assertTrue(proof.economically_valid)

    def test_exactly_twenty_cents_is_rejected(self):
        with self.assertRaises(EconomicProofError):
            self.build(final_settlement_usd=Decimal("100.75"))

    def test_one_micro_dollar_above_floor_is_accepted(self):
        proof = self.build(final_settlement_usd=Decimal("100.750001"))
        self.assertEqual(proof.worst_case_net_profit_usd, Decimal("0.200001"))
        self.assertTrue(proof.economically_valid)

    def test_every_cost_reduces_net_profit(self):
        base = self.build()
        for field in (
            "flash_loan_fee",
            "dex_fees",
            "price_impact",
            "gas",
            "relay",
            "other",
        ):
            increased = getattr(self.costs(), field) + Decimal("0.01")
            reduced = self.costs(**{field: increased})
            budgets = {}
            if field == "gas":
                budgets["max_gas_usd"] = increased
            if field == "relay":
                budgets["max_relay_usd"] = increased
            proof = self.build(costs=reduced, **budgets)
            self.assertEqual(
                proof.worst_case_net_profit_usd,
                base.worst_case_net_profit_usd - Decimal("0.01"),
                field,
            )

    def test_negative_cost_is_rejected(self):
        with self.assertRaises(EconomicProofError):
            self.build(costs=self.costs(other=Decimal("-0.01")))

    def test_gas_budget_is_enforced(self):
        with self.assertRaises(EconomicProofError):
            self.build(costs=self.costs(gas=Decimal("0.11")))

    def test_relay_budget_is_enforced(self):
        with self.assertRaises(EconomicProofError):
            self.build(costs=self.costs(relay=Decimal("0.06")))

    def test_missing_quote_evidence_is_rejected(self):
        with self.assertRaises(EconomicProofError):
            self.build(quote_hashes=())

    def test_invalid_hash_evidence_is_rejected(self):
        with self.assertRaises(EconomicProofError):
            self.build(route_hash="0x1234")

    def test_deterministic_proof_hash(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first.proof_hash, second.proof_hash)
        self.assertEqual(len(first.proof_hash), 66)

    def test_route_binding_changes_proof_hash(self):
        first = self.build()
        second = self.build(route_hash="0x" + "55" * 32)
        self.assertNotEqual(first.proof_hash, second.proof_hash)

    def test_quote_binding_changes_proof_hash(self):
        first = self.build()
        second = self.build(quote_hashes=(QUOTE_A, "0x" + "66" * 32))
        self.assertNotEqual(first.proof_hash, second.proof_hash)

    def test_valuation_binding_changes_proof_hash(self):
        first = self.build()
        second = self.build(valuation_hash="0x" + "77" * 32)
        self.assertNotEqual(first.proof_hash, second.proof_hash)

    def test_provided_tampered_proof_hash_is_rejected(self):
        with self.assertRaises(EconomicProofError):
            self.build(proof_hash="0x" + "99" * 32)

    def test_nan_and_infinity_are_rejected(self):
        for value in (Decimal("NaN"), Decimal("Infinity")):
            with self.assertRaises(EconomicProofError):
                self.build(final_settlement_usd=value)


if __name__ == "__main__":
    unittest.main()
