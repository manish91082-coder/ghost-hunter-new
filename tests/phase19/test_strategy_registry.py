import unittest

from phantomx.strategy_registry import (
    DEFAULT_STRATEGIES,
    execution_eligible,
    execution_supported_strategies,
    get_strategy,
    production_authorized_strategies,
)


class StrategyRegistryTests(unittest.TestCase):
    def test_registry_matches_existing_and_expansion_ids(self):
        ids = {item.strategy_id for item in DEFAULT_STRATEGIES}
        expected = {"S0","S1","S2","S3","S5","S5A","S6","S9","S10"} | {f"X{i}" for i in range(1,14)}
        self.assertEqual(ids, expected)

    def test_execution_support_is_not_production_authorization(self):
        self.assertEqual(
            {x.strategy_id for x in execution_supported_strategies()},
            {"S0","S1","S2","S3","S5","S9","S10"},
        )
        self.assertFalse(execution_eligible("S0"))
        self.assertEqual(production_authorized_strategies(), ())

    def test_lookup(self):
        self.assertEqual(get_strategy("S10").family, "QSV3_RAMSES")
        self.assertEqual(get_strategy("X1").min_legs, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
