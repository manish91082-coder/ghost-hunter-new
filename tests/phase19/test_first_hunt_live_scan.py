import json
import unittest

from scripts.first_hunt_live_scan import PAIRS, POLYGON_CHAIN_ID, SEED_LOAN_USDC, UNISWAP_V3_FEE_TIERS, classify_tile_coverage, dynamic_loan_frontier_usdc


class FirstHuntLiveScanContractTests(unittest.TestCase):
    def test_scan_contract_is_explicitly_read_only(self):
        self.assertEqual(POLYGON_CHAIN_ID, 137)
        self.assertTrue(SEED_LOAN_USDC)
        self.assertEqual(len(PAIRS), 9)
        pair_names = tuple(pair.name for pair in PAIRS)
        self.assertIn("USDC/USDT.e", pair_names)
        self.assertIn("USDC/MIMATIC", pair_names)
        self.assertEqual(len(set(pair_names)), len(pair_names))

    def test_loan_frontier_is_strictly_increasing(self):
        self.assertEqual(tuple(sorted(SEED_LOAN_USDC)), SEED_LOAN_USDC)
        self.assertEqual(len(set(SEED_LOAN_USDC)), len(SEED_LOAN_USDC))
        self.assertGreaterEqual(SEED_LOAN_USDC[0], 100)
        self.assertGreaterEqual(SEED_LOAN_USDC[-1], 25000)

    def test_dynamic_frontier_never_exceeds_live_ceiling(self):
        frontier = dynamic_loan_frontier_usdc(10050)
        self.assertTrue(frontier)
        self.assertLessEqual(frontier[-1], 10050)
        self.assertIn(10000, frontier)
        self.assertEqual(tuple(sorted(set(frontier))), frontier)

    def test_dynamic_frontier_includes_live_ceiling_above_seed_domain(self):
        frontier = dynamic_loan_frontier_usdc(400000)
        self.assertEqual(frontier[-1], 400000)
        self.assertGreater(len(frontier), len(SEED_LOAN_USDC))

    def test_uniswap_fee_tier_frontier_is_complete_and_unique(self):
        self.assertEqual(UNISWAP_V3_FEE_TIERS, (100, 500, 3000, 10000))
        self.assertEqual(len(set(UNISWAP_V3_FEE_TIERS)), len(UNISWAP_V3_FEE_TIERS))

    def test_tile_coverage_requires_every_declared_tile(self):
        complete = [{"status": "SUCCESS"} for _ in range(len(PAIRS) * len(UNISWAP_V3_FEE_TIERS))]
        self.assertEqual(classify_tile_coverage(complete), "COMPLETE")

    def test_tile_coverage_marks_missing_tile_as_incomplete(self):
        partial = [{"status": "SUCCESS"} for _ in range(2)] + [{"status": "UNAVAILABLE_OR_FAILED"}]
        self.assertEqual(classify_tile_coverage(partial), "PARTIAL_INCOMPLETE")
        self.assertNotEqual(classify_tile_coverage(partial), "COMPLETE")

    def test_artifact_profit_policy_is_non_claiming(self):
        payload = {
            "economic_certification": "NOT_PERFORMED",
            "profit_claim": "NONE",
            "signing": False,
            "submission": False,
            "broadcast": False,
            "live_capital": False,
        }
        self.assertFalse(payload["signing"])
        self.assertFalse(payload["submission"])
        self.assertFalse(payload["broadcast"])
        self.assertFalse(payload["live_capital"])
        self.assertEqual(payload["economic_certification"], "NOT_PERFORMED")
        self.assertEqual(payload["profit_claim"], "NONE")


if __name__ == "__main__":
    unittest.main()
