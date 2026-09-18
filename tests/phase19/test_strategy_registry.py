import unittest

from phantomx.strategy_registry import DEFAULT_STRATEGIES, StrategyRegistry, StrategySpec, StrategyStatus


class StrategyRegistryTests(unittest.TestCase):
    def test_current_canonical_strategy_is_unique(self):
        production = DEFAULT_STRATEGIES.production()
        self.assertEqual(len(production), 1)
        self.assertEqual(production[0].strategy_id, "S0-DIRECT-QS-V3")

    def test_discovery_surface_is_expanded_but_fail_closed(self):
        discovery = DEFAULT_STRATEGIES.discovery_only()
        self.assertGreaterEqual(len(discovery), 8)
        self.assertTrue(all(s.chain_id == 137 for s in discovery))
        self.assertFalse(any(s.status == StrategyStatus.CANONICAL for s in discovery))

    def test_duplicate_registration_is_rejected(self):
        registry=StrategyRegistry()
        spec=StrategySpec("X","x",StrategyStatus.DISCOVERY_ONLY,137,("Aave V3",),("Venue",),"direct")
        registry.add(spec)
        with self.assertRaises(ValueError):
            registry.add(spec)


if __name__=="__main__":
    unittest.main(verbosity=2)
