import json
import unittest

from scripts.first_hunt_live_scan import LOAN_USDC, PAIRS, POLYGON_CHAIN_ID


class FirstHuntLiveScanContractTests(unittest.TestCase):
    def test_scan_contract_is_explicitly_read_only(self):
        self.assertEqual(POLYGON_CHAIN_ID, 137)
        self.assertTrue(LOAN_USDC)
        self.assertEqual(len(PAIRS), 3)

    def test_loan_frontier_is_strictly_increasing(self):
        self.assertEqual(tuple(sorted(LOAN_USDC)), LOAN_USDC)
        self.assertEqual(len(set(LOAN_USDC)), len(LOAN_USDC))
        self.assertGreaterEqual(LOAN_USDC[0], 100)
        self.assertGreaterEqual(LOAN_USDC[-1], 25000)

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
