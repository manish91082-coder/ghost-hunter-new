import unittest

from phantomx.market_graph import PoolEdge
from phantomx.polygon_market_snapshot import build_snapshot, cycle_tasks
from phantomx.polygon_universe_inventory import InventoryTask, InventoryTaskResult


class MarketSnapshotTests(unittest.TestCase):
    def _result(self, edge):
        return InventoryTaskResult(
            task=InventoryTask("uniswap_v3", 100, 100, 10),
            logs=(),
            edges=(edge,),
            status="QUOTED",
            error=None,
            evidence_hash="h",
        )

    def test_pool_becomes_two_way_and_generates_two_leg_cycle(self):
        snapshot = build_snapshot(
            [self._result(PoolEdge("p", "v3", "pool", "USDC", "WETH"))],
            base_token="USDC",
        )
        self.assertEqual(snapshot.edge_count, 2)
        self.assertEqual(snapshot.token_count, 2)
        self.assertEqual(len(snapshot.cycles_2_leg), 1)

    def test_two_pool_path_generates_three_leg_cycle(self):
        results = [
            self._result(PoolEdge("p1", "v3", "1", "USDC", "WETH")),
            self._result(PoolEdge("p2", "v3", "2", "WETH", "DAI")),
            self._result(PoolEdge("p3", "v3", "3", "DAI", "USDC")),
        ]
        snapshot = build_snapshot(results, base_token="USDC")
        self.assertEqual(len(snapshot.cycles_3_leg), 1)

    def test_cycle_tasks_have_stable_ids(self):
        snapshot = build_snapshot(
            [self._result(PoolEdge("p", "v3", "pool", "USDC", "WETH"))],
            base_token="USDC",
        )
        tasks = cycle_tasks(snapshot, base_token="USDC", last_scanned_block=100)
        self.assertEqual(len(tasks), 1)
        self.assertTrue(tasks[0].task_id.startswith("hunt:"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
