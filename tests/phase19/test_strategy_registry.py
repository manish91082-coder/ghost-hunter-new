import unittest

from phantomx.strategy_registry import DEFAULT_STRATEGIES, discovery_strategies, execution_eligible, execution_strategies, get_strategy


class StrategyRegistryTests(unittest.TestCase):
    def test_registry_has_complete_declared_strategy_surface(self):
        self.assertEqual(len(DEFAULT_STRATEGIES), 20)
        self.assertEqual({x.strategy_id for x in DEFAULT_STRATEGIES}, {f"S{i}" for i in range(20)})

    def test_only_explicitly_certified_lanes_are_execution_eligible(self):
        eligible = {x.strategy_id for x in execution_strategies()}
        self.assertEqual(eligible, {"S0", "S1", "S3"})
        self.assertTrue(execution_eligible("S0"))
        self.assertFalse(execution_eligible("S6"))

    def test_lookup_is_deterministic(self):
        self.assertEqual(get_strategy("S10").max_legs, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
