import unittest
from decimal import Decimal
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling, compute_uniswap_v3_swap_fee_raw, compute_gas_cost_usd

class DynamicMarketPolicyTests(unittest.TestCase):
    def test_ceiling_uses_live_liquidity_and_route_constraints(self):
        x = DynamicLoanInputs(1_000_000, 700_000, 800_000, 900_000, 500)
        self.assertEqual(compute_dynamic_loan_ceiling(x), 650_000)

    def test_one_percent_fee_is_swap_cost_not_gas(self):
        self.assertEqual(compute_uniswap_v3_swap_fee_raw(10_000_000, 10_000), 100_000)

    def test_gas_uses_units_and_price_not_loan_percentage(self):
        self.assertEqual(compute_gas_cost_usd(gas_used=200_000, effective_gas_price_wei=1_000_000_000, native_usd_price=Decimal('0.50')), Decimal('0.0001'))

    def test_zero_live_liquidity_fails_closed(self):
        with self.assertRaises(ValueError):
            compute_dynamic_loan_ceiling(DynamicLoanInputs(0, 1, 1))

if __name__ == "__main__":
    unittest.main()