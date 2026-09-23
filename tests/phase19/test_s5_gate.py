import unittest

from scripts.validate_s5_gate import validate_s5_artifact


def complete_artifact():
    return {
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "chain_id_expected": 137,
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
        "provenance": {"git_commit_sha": "abc123"},
        "successful_endpoints": [
            {
                "status": "SUCCESS",
                "coverage": {"status": "COMPLETE"},
                "pair_universe": {"status": "COMPLETE_RECENT_WINDOW"},
            }
        ],
        "pair_universe": {"status": "COMPLETE_RECENT_WINDOW"},
        "failed_endpoints": [],
    }


class S5GateTests(unittest.TestCase):
    def test_complete_s5_artifact_passes(self):
        ok, errors = validate_s5_artifact(complete_artifact())
        self.assertTrue(ok)
        self.assertEqual(errors, ())

    def test_incomplete_coverage_blocks_advancement(self):
        payload = complete_artifact()
        payload["successful_endpoints"][0]["coverage"]["status"] = "PARTIAL_INCOMPLETE"
        ok, errors = validate_s5_artifact(payload)
        self.assertFalse(ok)
        self.assertIn("successful_endpoints[0] coverage is not COMPLETE", errors)

    def test_incomplete_pair_universe_blocks_advancement(self):
        payload = complete_artifact()
        payload["pair_universe"]["status"] = "PAIR_UNIVERSE_INCOMPLETE"
        ok, errors = validate_s5_artifact(payload)
        self.assertFalse(ok)
        self.assertIn("aggregate pair universe is not COMPLETE_RECENT_WINDOW", errors)

    def test_economic_and_safety_claims_are_locked(self):
        payload = complete_artifact()
        payload["profit_claim"] = "PROFITABLE"
        ok, errors = validate_s5_artifact(payload)
        self.assertFalse(ok)
        self.assertIn("profit_claim must remain NONE", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
