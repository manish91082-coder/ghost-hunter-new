import unittest
from decimal import Decimal

from phantomx.gas_cost import GasCostEvidenceError, build_gas_cost_evidence
from phantomx.gas_observation import GasObservation

class GasCostEvidenceTests(unittest.TestCase):
    def obs(self):
        return GasObservation(
            schema_version=1, chain_id=137, block_number=100,
            gas_estimate=100000, gas_limit=120000,
            base_fee_per_gas=1_000_000_000,
            priority_fee_per_gas=100_000_000,
            max_fee_per_gas=2_100_000_000,
        )

    def test_usd_cost_uses_transaction_level_native_gas_bound(self):
        evidence = build_gas_cost_evidence(self.obs(), native_usd_price=Decimal("0.50"), valuation_evidence_hash="0x"+"11"*32)
        expected = Decimal(120000 * 2_100_000_000) * Decimal("0.50") / Decimal(10**18)
        self.assertEqual(evidence.max_gas_cost_usd, expected)

    def test_loan_size_is_not_an_input(self):
        evidence = build_gas_cost_evidence(self.obs(), native_usd_price="0.5", valuation_evidence_hash="0x"+"11"*32)
        self.assertGreater(evidence.max_gas_cost_usd, Decimal("0"))

    def test_bad_valuation_hash_is_rejected(self):
        with self.assertRaises(GasCostEvidenceError):
            build_gas_cost_evidence(self.obs(), native_usd_price="0.5", valuation_evidence_hash="0x1234")

    def test_non_positive_price_is_rejected(self):
        with self.assertRaises(GasCostEvidenceError):
            build_gas_cost_evidence(self.obs(), native_usd_price="0", valuation_evidence_hash="0x"+"11"*32)

if __name__ == "__main__":
    unittest.main(verbosity=2)
