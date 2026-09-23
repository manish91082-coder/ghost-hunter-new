import unittest

from scripts.s5_curve_uv3_live_scan import (
    classify_s5_tile_failure,
    summarize_s5_coverage,
)


class S5CoverageClassificationTests(unittest.TestCase):
    def test_missing_pool_is_terminal_no_route(self) -> None:
        exc = RuntimeError("Uniswap V3 pool does not exist for requested fee tier")
        self.assertEqual(classify_s5_tile_failure(exc), "COMPLETE_NO_COMMON_ROUTE")

    def test_zero_output_is_terminal_no_route(self) -> None:
        exc = RuntimeError("Curve returned zero output")
        self.assertEqual(classify_s5_tile_failure(exc), "COMPLETE_NO_COMMON_ROUTE")

    def test_ambiguous_revert_consensus_is_terminal_no_route(self) -> None:
        exc = RuntimeError(
            "ambiguous execution revert consensus across distinct Polygon RPC providers: drpc-public, tenderly-public"
        )
        self.assertEqual(classify_s5_tile_failure(exc), "COMPLETE_NO_COMMON_ROUTE")

    def test_spl_execution_revert_is_terminal_no_route(self) -> None:
        exc = RuntimeError("eth_call: RPC error code=3 message=execution reverted: SPL")
        self.assertEqual(classify_s5_tile_failure(exc), "COMPLETE_NO_COMMON_ROUTE")

    def test_generic_execution_revert_is_incomplete(self) -> None:
        exc = RuntimeError("eth_call: RPC error code=3 message=execution reverted")
        self.assertEqual(classify_s5_tile_failure(exc), "PARTIAL_INCOMPLETE")

    def test_transport_exhaustion_is_incomplete(self) -> None:
        exc = RuntimeError("all bounded Polygon RPC recovery passes failed")
        self.assertEqual(classify_s5_tile_failure(exc), "PARTIAL_INCOMPLETE")

    def test_pair_universe_incomplete_blocks_certification(self) -> None:
        coverage = summarize_s5_coverage(
            [{"coverage_status": "COMPLETE", "pair": "USDC.e/WETH"}],
            pair_universe_status="PAIR_UNIVERSE_INCOMPLETE",
        )
        self.assertEqual(coverage["status"], "PARTIAL_INCOMPLETE")
        self.assertEqual(coverage["tile_status"], "COMPLETE")

    def test_complete_pair_surface_and_tiles_is_complete(self) -> None:
        coverage = summarize_s5_coverage(
            [{"coverage_status": "COMPLETE_NO_COMMON_ROUTE", "pair": "USDC.e/WETH"}],
            pair_universe_status="COMPLETE_RECENT_WINDOW",
        )
        self.assertEqual(coverage["status"], "COMPLETE")
        self.assertEqual(coverage["completed_tile_count"], 1)
        self.assertEqual(coverage["incomplete_tile_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)