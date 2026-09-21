import unittest

from scripts.s10_qsv3_ramses_v3_live_scan import classify_s10_tile_failure, summarize_s10_coverage


class S10CoverageTests(unittest.TestCase):
    def test_ramses_missing_pool_is_terminal(self):
        self.assertEqual(
            classify_s10_tile_failure(RuntimeError("Ramses V3 pool does not exist for requested tick spacing")),
            "COMPLETE_NO_COMMON_ROUTE",
        )

    def test_quickswap_pool_missing_is_terminal(self):
        self.assertEqual(
            classify_s10_tile_failure(RuntimeError("QuickSwap V3 pool does not exist")),
            "COMPLETE_NO_COMMON_ROUTE",
        )

    def test_generic_revert_is_incomplete(self):
        self.assertEqual(
            classify_s10_tile_failure(RuntimeError("execution reverted")),
            "PARTIAL_INCOMPLETE",
        )

    def test_complete_coverage_requires_complete_pair_surface(self):
        tiles=[{"coverage_status":"COMPLETE"}]
        self.assertEqual(summarize_s10_coverage(tiles,1,"COMPLETE_RECENT_WINDOW")["status"],"COMPLETE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
