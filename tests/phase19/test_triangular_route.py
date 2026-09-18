import unittest

from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.triangular_route import (
    TriangularRouteSimulationError,
    compute_multi_leg_route_hash,
    simulate_multi_leg,
)

A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
C = "0x" + "cc" * 20


def snapshot(token_in, token_out, amount_in, amount_out, block=500):
    from phantomx.quote_engine import ExactQuote
    return QuoteSnapshot.from_exact_quote(
        ExactQuote("test", token_in, token_out, amount_in, amount_out, block, 0),
        chain_id=137,
        observed_at_unix=1700000000,
        pool_or_router="0x" + "11" * 20,
    )


class TriangularRouteTests(unittest.TestCase):
    def test_three_legs_are_contiguous_and_round_trip(self):
        one = snapshot(A, B, 1000, 1100)
        two = snapshot(B, C, 1100, 1200)
        three = snapshot(C, A, 1200, 1050)
        route = simulate_multi_leg((one, two, three))
        self.assertEqual(route.initial_amount, 1000)
        self.assertEqual(route.final_amount, 1050)
        self.assertEqual(route.legs[1].amount_in, 1100)
        self.assertEqual(route.legs[2].amount_in, 1200)

    def test_hash_is_order_sensitive(self):
        one = snapshot(A, B, 1000, 1100)
        two = snapshot(B, C, 1100, 1200)
        three = snapshot(C, A, 1200, 1050)
        self.assertNotEqual(
            compute_multi_leg_route_hash((one, two, three)),
            compute_multi_leg_route_hash((three, two, one)),
        )

    def test_continuity_break_rejected(self):
        one = snapshot(A, B, 1000, 1100)
        two = snapshot(B, C, 1101, 1200)
        three = snapshot(C, A, 1200, 1050)
        with self.assertRaises(TriangularRouteSimulationError):
            simulate_multi_leg((one, two, three))

    def test_block_mismatch_rejected(self):
        one = snapshot(A, B, 1000, 1100)
        two = snapshot(B, C, 1100, 1200, block=501)
        three = snapshot(C, A, 1200, 1050)
        with self.assertRaises(TriangularRouteSimulationError):
            simulate_multi_leg((one, two, three))

    def test_non_round_trip_rejected(self):
        one = snapshot(A, B, 1000, 1100)
        two = snapshot(B, C, 1100, 1200)
        three = snapshot(C, B, 1200, 1050)
        with self.assertRaises(TriangularRouteSimulationError):
            simulate_multi_leg((one, two, three))


if __name__ == "__main__":
    unittest.main(verbosity=2)
