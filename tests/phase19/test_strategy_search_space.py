import unittest

from phantomx.market_graph import MarketCycle, PoolEdge, PolygonMarketGraph
from phantomx.strategy_search_space import StrategyFamily, classify_cycle, generate_candidates


class StrategySearchSpaceTests(unittest.TestCase):
    def test_direct_cross_venue_is_classified(self):
        g = PolygonMarketGraph()
        g.add_edges([
            PoolEdge("a", "qsv2", "1", "USDC", "WETH"),
            PoolEdge("b", "uv3", "2", "WETH", "USDC"),
        ])
        cycle = g.cycles_from("USDC", max_legs=2)[0]
        self.assertIn(StrategyFamily.DIRECT_CROSS_VENUE, classify_cycle(cycle))

    def test_same_venue_distinct_pool_is_classified(self):
        g = PolygonMarketGraph()
        g.add_edges([
            PoolEdge("a", "uv3", "pool1", "USDC", "WETH", (("fee","500"),)),
            PoolEdge("b", "uv3", "pool2", "WETH", "USDC", (("fee","3000"),)),
        ])
        cycle = g.cycles_from("USDC", max_legs=2)[0]
        self.assertIn(StrategyFamily.SAME_VENUE_POOL_DISLOCATION, classify_cycle(cycle))

    def test_three_venue_cycle_is_triangular(self):
        g = PolygonMarketGraph()
        g.add_edges([
            PoolEdge("a", "qsv3", "1", "USDC", "WETH"),
            PoolEdge("b", "uv3", "2", "WETH", "DAI"),
            PoolEdge("c", "ramses", "3", "DAI", "USDC"),
        ])
        cycle = g.cycles_from("USDC", max_legs=3)[0]
        self.assertIn(StrategyFamily.TRIANGULAR, classify_cycle(cycle))

    def test_four_leg_candidate_is_generated(self):
        g = PolygonMarketGraph()
        g.add_edges([
            PoolEdge("a", "qsv2", "1", "USDC", "WETH"),
            PoolEdge("b", "uv3", "2", "WETH", "DAI"),
            PoolEdge("c", "curve", "3", "DAI", "USDT"),
            PoolEdge("d", "ramses", "4", "USDT", "USDC"),
        ])
        cycles = g.cycles_from("USDC", max_legs=4)
        out = generate_candidates(cycles, StrategyFamily.FOUR_LEG)
        self.assertEqual(len(out), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
