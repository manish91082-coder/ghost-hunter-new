import unittest

from scripts.s9_qsv2_ramses_v3_live_scan import classify_s9_tile_failure, summarize_s9_coverage


class S9CoverageTests(unittest.TestCase):
    def test_ramses_missing_pool_is_terminal(self):
        self.assertEqual(
            classify_s9_tile_failure(RuntimeError("Ramses V3 pool does not exist for requested tick spacing")),
            "COMPLETE_NO_COMMON_ROUTE",
        )

    def test_generic_revert_is_incomplete(self):
        self.assertEqual(
            classify_s9_tile_failure(RuntimeError("execution reverted")),
            "PARTIAL_INCOMPLETE",
        )

    def test_complete_coverage_requires_complete_pair_surface(self):
        tiles=[{"coverage_status":"COMPLETE"},{"coverage_status":"COMPLETE_NO_COMMON_ROUTE"}]
        self.assertEqual(summarize_s9_coverage(tiles,2,"PAIR_UNIVERSE_INCOMPLETE")["status"],"PARTIAL_INCOMPLETE")

    def test_complete_tiles_and_pair_surface_certify_coverage(self):
        tiles=[{"coverage_status":"COMPLETE"},{"coverage_status":"COMPLETE_NO_COMMON_ROUTE"}]
        self.assertEqual(summarize_s9_coverage(tiles,2,"COMPLETE_RECENT_WINDOW")["status"],"COMPLETE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
