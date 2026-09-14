import unittest

from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import RouteSimulationError, compute_route_hash, simulate_two_leg

A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
QS = "0x" + "11" * 20
UNI = "0x" + "22" * 20


def snapshot(venue, router, token_in, token_out, amount_in, amount_out, timestamp=1000):
    from phantomx.quote_engine import ExactQuote
    return QuoteSnapshot.from_exact_quote(
        ExactQuote(venue, token_in, token_out, amount_in, amount_out, 500, 0),
        chain_id=137,
        observed_at_unix=timestamp,
        pool_or_router=router,
    )


class RouteSimulatorTests(unittest.TestCase):
    def make_legs(self):
        one = snapshot("quickswap_v2", QS, A, B, 1_000_000, 1_050_000)
        two = snapshot("uniswap_v3:pool", UNI, B, A, 1_050_000, 1_010_000)
        return one, two

    def test_exact_output_feeds_second_leg(self):
        one, two = self.make_legs()
        route = simulate_two_leg(one, two)
        self.assertEqual(route.initial_amount, 1_000_000)
        self.assertEqual(route.final_amount, 1_010_000)
        self.assertEqual(route.legs[1].amount_in, route.legs[0].amount_out)

    def test_route_hash_is_order_sensitive(self):
        one, two = self.make_legs()
        self.assertNotEqual(compute_route_hash((one, two)), compute_route_hash((two, one)))

    def test_same_evidence_has_same_route_hash(self):
        one, two = self.make_legs()
        self.assertEqual(compute_route_hash((one, two)), compute_route_hash((one, two)))

    def test_chain_mismatch_rejected(self):
        one, two = self.make_legs()
        bad = snapshot("uniswap_v3:pool", UNI, B, A, 1_050_000, 1_010_000)
        object.__setattr__(bad, "chain_id", 1)
        with self.assertRaises(RouteSimulationError):
            simulate_two_leg(one, bad)

    def test_block_mismatch_rejected(self):
        one, _ = self.make_legs()
        two = snapshot("uniswap_v3:pool", UNI, B, A, 1_050_000, 1_010_000)
        object.__setattr__(two, "block_number", 501)
        with self.assertRaises(RouteSimulationError):
            simulate_two_leg(one, two)

    def test_token_continuity_rejected(self):
        one, _ = self.make_legs()
        two = snapshot("uniswap_v3:pool", UNI, A, B, 1_050_000, 1_010_000)
        with self.assertRaises(RouteSimulationError):
            simulate_two_leg(one, two)

    def test_amount_continuity_rejected(self):
        one, _ = self.make_legs()
        two = snapshot("uniswap_v3:pool", UNI, B, A, 1_049_999, 1_010_000)
        with self.assertRaises(RouteSimulationError):
            simulate_two_leg(one, two)

    def test_non_round_trip_rejected(self):
        one = snapshot("quickswap_v2", QS, A, B, 1_000_000, 1_050_000)
        two = snapshot("uniswap_v3:pool", UNI, B, "0x" + "cc" * 20, 1_050_000, 1_010_000)
        with self.assertRaises(RouteSimulationError):
            simulate_two_leg(one, two)


if __name__ == "__main__":
    unittest.main(verbosity=2)
