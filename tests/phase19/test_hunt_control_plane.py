import unittest

from phantomx.coverage_ledger import CoverageLedger, CoverageRecord, CoverageStatus, CoverageTask
from phantomx.market_graph import PoolEdge
from phantomx.polygon_market_snapshot import build_snapshot
from phantomx.hunt_control_plane import build_plan
from phantomx.strategy_search_space import StrategyFamily


class HuntControlPlaneTests(unittest.TestCase):
    def _result(self, venue, edge_id, pool_id, token_in, token_out):
        from phantomx.polygon_universe_inventory import InventoryTask, InventoryTaskResult
        return InventoryTaskResult(
            task=InventoryTask(venue, 100, 100, 10),
            logs=(),
            edges=(PoolEdge(edge_id, venue, pool_id, token_in, token_out),),
            status="QUOTED",
            error=None,
            evidence_hash=edge_id,
        )

    def test_new_route_is_scheduled_as_hot(self):
        snapshot = build_snapshot([
            self._result("qsv2", "a", "1", "USDC", "WETH"),
            self._result("uv3", "b", "2", "WETH", "USDC"),
        ], base_token="USDC")
        plan = build_plan(
            snapshot,
            base_token="USDC",
            current_block=101,
            family=StrategyFamily.DIRECT_CROSS_VENUE,
            coverage=CoverageLedger(),
        )
        self.assertEqual(len(plan.candidates), 2)
        self.assertEqual(plan.scheduled[0].task.task_id.startswith("hunt:"), True)

    def test_terminal_coverage_is_not_rescheduled(self):
        snapshot = build_snapshot([
            self._result("qsv2", "a", "1", "USDC", "WETH"),
            self._result("uv3", "b", "2", "WETH", "USDC"),
        ], base_token="USDC")
        temp = build_plan(snapshot, base_token="USDC", current_block=101, family=StrategyFamily.DIRECT_CROSS_VENUE, coverage=CoverageLedger())
        ledger = CoverageLedger()
        for scheduled in temp.scheduled:
            task = scheduled.task
            ledger.upsert(CoverageRecord(CoverageTask(task.task_id, "DIRECT_CROSS_VENUE", task.route_id, 101), CoverageStatus.ECONOMIC_REJECTED, "x"))
        plan = build_plan(snapshot, base_token="USDC", current_block=200, family=StrategyFamily.DIRECT_CROSS_VENUE, coverage=ledger)
        self.assertEqual(plan.scheduled, ())

if __name__ == "__main__":
    unittest.main(verbosity=2)