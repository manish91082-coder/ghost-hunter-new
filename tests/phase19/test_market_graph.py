import unittest

from phantomx.market_graph import MarketGraphError, MarketCycle, PoolEdge, PolygonMarketGraph


def edge(edge_id, venue, pool_id, token_in, token_out):
    return PoolEdge(edge_id, venue, pool_id, token_in, token_out)


class MarketGraphTests(unittest.TestCase):
    def test_multiple_pools_for_same_pair_remain_distinct(self):
        g = PolygonMarketGraph()
        g.add_edges([
            edge("a", "v2", "pool-a", "USDC", "WETH"),
            edge("b", "v3", "pool-b", "WETH", "USDC"),
        ])
        g.add_edges([
            edge("c", "v3", "pool-c", "USDC", "WETH"),
        ])
        cycles = g.cycles_from("USDC", max_legs=2)
        self.assertEqual(len(cycles), 2)
        self.assertEqual({c.edges[0].edge_id for c in cycles}, {"a", "c"})

    def test_three_leg_cycle_is_generated(self):
        g = PolygonMarketGraph()
        g.add_edges([
            edge("a", "v1", "1", "USDC", "WETH"),
            edge("b", "v2", "2", "WETH", "DAI"),
            edge("c", "v3", "3", "DAI", "USDC"),
        ])
        cycles = g.cycles_from("USDC", max_legs=3)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0].token_path, ("usdc", "weth", "dai", "usdc"))

    def test_four_leg_bound_excludes_longer_cycle(self):
        g = PolygonMarketGraph()
        g.add_edges([
            edge("a", "v1", "1", "USDC", "A"),
            edge("b", "v2", "2", "A", "B"),
            edge("c", "v3", "3", "B", "C"),
            edge("d", "v4", "4", "C", "USDC"),
        ])
        self.assertEqual(g.cycles_from("USDC", max_legs=3), ())
        self.assertEqual(len(g.cycles_from("USDC", max_legs=4)), 1)

    def test_repeated_intermediate_token_is_not_allowed(self):
        g = PolygonMarketGraph()
        g.add_edges([
            edge("a", "v1", "1", "USDC", "A"),
            edge("b", "v2", "2", "A", "B"),
            edge("c", "v3", "3", "B", "A"),
            edge("d", "v4", "4", "A", "USDC"),
        ])
        self.assertEqual(g.cycles_from("USDC", max_legs=4), ())

    def test_edge_id_must_be_unique(self):
        g = PolygonMarketGraph()
        g.add_edge(edge("a", "v1", "1", "USDC", "A"))
        with self.assertRaises(MarketGraphError):
            g.add_edge(edge("A", "v2", "2", "A", "USDC"))

    def test_route_ids_are_deterministic(self):
        g1 = PolygonMarketGraph()
        g1.add_edges([
            edge("a", "v1", "1", "USDC", "A"),
            edge("b", "v2", "2", "A", "USDC"),
        ])
        g2 = PolygonMarketGraph()
        g2.add_edges(list(reversed(g1.outgoing("USDC"))) + list(g1.outgoing("a")))
        self.assertEqual(
            [x.route_id for x in g1.cycles_from("USDC")],
            [x.route_id for x in g2.cycles_from("USDC")],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
