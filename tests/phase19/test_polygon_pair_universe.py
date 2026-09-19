import unittest

from phantomx.polygon_pair_universe import base_pairs, build_pair_universe
from phantomx.polygon_universe_inventory import InventoryTask, InventoryTaskResult
from phantomx.market_graph import PoolEdge


class PairUniverseTests(unittest.TestCase):
    def result(self, venue, edge):
        return InventoryTaskResult(
            InventoryTask(venue, 100, 100),
            logs=(),
            edges=(edge,),
            status="QUOTED",
            error=None,
            evidence_hash=edge.edge_id,
        )

    def test_universe_merges_same_pair_across_venues(self):
        results = [
            self.result("qsv2", PoolEdge("a", "qsv2", "p1", "USDC", "WETH")),
            self.result("uv3", PoolEdge("b", "uv3", "p2", "WETH", "USDC")),
        ]
        universe = build_pair_universe(results)
        self.assertEqual(len(universe), 1)
        self.assertEqual(universe[0].venues, ("qsv2", "uv3"))
        self.assertEqual(universe[0].pool_count, 2)

    def test_base_pair_requires_all_requested_venues(self):
        results = [
            self.result("qsv2", PoolEdge("a", "qsv2", "p1", "USDC", "WETH")),
            self.result("uv3", PoolEdge("b", "uv3", "p2", "WETH", "USDC")),
            self.result("curve", PoolEdge("c", "curve", "p3", "DAI", "USDC")),
        ]
        universe = build_pair_universe(results)
        pairs = base_pairs(universe, base_token="USDC", required_venues=("qsv2", "uv3"))
        self.assertEqual(len(pairs), 1)

    def test_parameterized_pools_count_separately(self):
        results = [
            self.result("uv3", PoolEdge("a", "uv3", "p", "USDC", "WETH", (("fee","500"),))),
            self.result("uv3", PoolEdge("b", "uv3", "p", "WETH", "USDC", (("fee","3000"),))),
        ]
        universe = build_pair_universe(results)
        self.assertEqual(universe[0].pool_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
