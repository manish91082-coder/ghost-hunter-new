import unittest

from scripts.s3_ramses_uv3_live_scan import (
    classify_s3_tile_failure,
    summarize_s3_coverage,
)


class S3CoverageClassificationTests(unittest.TestCase):
    def test_ramses_missing_pool_is_terminal_no_route(self) -> None:
        exc = RuntimeError("Ramses V3 pool does not exist for requested tick spacing")
        self.assertEqual(classify_s3_tile_failure(exc), "COMPLETE_NO_COMMON_ROUTE")

    def test_uniswap_missing_pool_is_terminal_no_route(self) -> None:
        exc = RuntimeError("Uniswap V3 pool does not exist for requested fee tier")
        self.assertEqual(classify_s3_tile_failure(exc), "COMPLETE_NO_COMMON_ROUTE")

    def test_rpc_revert_is_incomplete(self) -> None:
        exc = RuntimeError("eth_call: RPC error code=3 message=execution reverted: Unexpected error")
        self.assertEqual(classify_s3_tile_failure(exc), "PARTIAL_INCOMPLETE")

    def test_generic_transport_failure_is_incomplete(self) -> None:
        exc = TimeoutError("read timed out")
        self.assertEqual(classify_s3_tile_failure(exc), "PARTIAL_INCOMPLETE")

    def test_all_tiles_terminal_or_complete_is_complete_coverage(self) -> None:
        tiles = [
            {"coverage_status": "COMPLETE", "pair": "USDC.e/WETH"},
            {"coverage_status": "COMPLETE_NO_COMMON_ROUTE", "pair": "USDC.e/WBTC"},
        ]
        coverage = summarize_s3_coverage(tiles, expected_tile_count=2)
        self.assertEqual(coverage["status"], "COMPLETE")
        self.assertEqual(coverage["completed_tile_count"], 2)
        self.assertEqual(coverage["incomplete_tile_count"], 0)

    def test_any_incomplete_tile_blocks_coverage(self) -> None:
        tiles = [
            {"coverage_status": "COMPLETE", "pair": "USDC.e/WETH"},
            {"coverage_status": "PARTIAL_INCOMPLETE", "pair": "USDC.e/DAI"},
        ]
        coverage = summarize_s3_coverage(tiles, expected_tile_count=2)
        self.assertEqual(coverage["status"], "PARTIAL_INCOMPLETE")
        self.assertEqual(coverage["completed_tile_count"], 1)
        self.assertEqual(coverage["incomplete_tile_count"], 1)

    def test_missing_tiles_block_coverage_even_without_errors(self) -> None:
        tiles = [{"coverage_status": "COMPLETE", "pair": "USDC.e/WETH"}]
        coverage = summarize_s3_coverage(tiles, expected_tile_count=2)
        self.assertEqual(coverage["status"], "PARTIAL_INCOMPLETE")
        self.assertEqual(coverage["observed_tile_count"], 1)


if __name__ == "__main__":
    unittest.main()
