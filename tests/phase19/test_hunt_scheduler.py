import unittest

from phantomx.hunt_scheduler import (
    HuntBand,
    HuntTask,
    classify,
    priority,
    schedule,
    stable_task_id,
)


class HuntSchedulerTests(unittest.TestCase):
    def test_recent_positive_is_hot_and_due_every_block(self):
        task = HuntTask("t1", "r1", 100, recently_positive=True)
        self.assertEqual(classify(task), HuntBand.HOT)
        items = schedule([task], 101)
        self.assertEqual(items[0].band, HuntBand.HOT)
        self.assertEqual(items[0].next_due_block, 101)

    def test_new_pool_is_hot(self):
        task = HuntTask("t1", "r1", 100, newly_discovered=True)
        self.assertEqual(classify(task), HuntBand.HOT)

    def test_liquid_route_is_warm(self):
        task = HuntTask("t1", "r1", 100, liquidity_score_bps=3000)
        self.assertEqual(classify(task), HuntBand.WARM)
        self.assertEqual(schedule([task], 105)[0].next_due_block, 105)

    def test_quiet_route_remains_cold(self):
        task = HuntTask("t1", "r1", 100, liquidity_score_bps=500)
        self.assertEqual(classify(task), HuntBand.COLD)
        self.assertEqual(schedule([task], 105)[0].next_due_block, 200)

    def test_ineligible_route_is_never_scheduled(self):
        task = HuntTask("t1", "r1", 100, eligible=False, recently_positive=True)
        self.assertEqual(schedule([task], 200), ())

    def test_starvation_guard_keeps_due_cold_route_alive(self):
        tasks = [
            HuntTask(f"hot{i}", f"rh{i}", 0, recently_positive=True)
            for i in range(5)
        ]
        tasks.append(HuntTask("cold", "rc", 0, liquidity_score_bps=100))
        selected = schedule(tasks, 100, max_tasks=5)
        self.assertIn("cold", [item.task.task_id for item in selected])

    def test_stable_task_id_is_deterministic(self):
        self.assertEqual(stable_task_id("route:abc", "state:1"), stable_task_id("route:abc", "state:1"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
