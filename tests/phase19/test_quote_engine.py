import unittest
from decimal import Decimal

from phantomx.economics import CostBreakdown
from phantomx.quote_engine import QuoteEngineError, net_profit_usd, profitable_after_costs, quote_sequential


class QuoteEngineTests(unittest.TestCase):
    def test_sequential_output_becomes_next_input(self):
        seen = []
        def first(amount):
            seen.append(amount)
            return amount * 2
        def second(amount):
            seen.append(amount)
            return amount - 3
        route = quote_sequential([
            ("qs", "A", "B", first),
            ("uni", "B", "A", second),
        ], 10, 123)
        self.assertEqual(seen, [10, 20])
        self.assertEqual(route.final_amount, 17)
        self.assertEqual(route.quotes[1].amount_in, 20)

    def test_empty_route_rejected(self):
        with self.assertRaises(QuoteEngineError):
            quote_sequential([], 10, 1)

    def test_zero_output_terminates_route(self):
        with self.assertRaises(QuoteEngineError):
            quote_sequential([("qs", "A", "B", lambda _: 0)], 10, 1)

    def test_integer_quote_has_no_float_rounding(self):
        route = quote_sequential([("qs", "A", "B", lambda _: 123456789)], 999999999, 55)
        self.assertEqual(route.final_amount, 123456789)
        self.assertIsInstance(route.final_amount, int)

    def test_all_costs_are_in_net_profit(self):
        costs = CostBreakdown(Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5"), Decimal("6"))
        self.assertEqual(net_profit_usd(Decimal("30"), Decimal("1"), costs), Decimal("8"))

    def test_exactly_twenty_cents_is_rejected(self):
        costs = CostBreakdown()
        self.assertFalse(profitable_after_costs(Decimal("1.20"), Decimal("1.00"), costs))

    def test_above_twenty_cents_is_accepted(self):
        costs = CostBreakdown()
        self.assertTrue(profitable_after_costs(Decimal("1.201"), Decimal("1.00"), costs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
