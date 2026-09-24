import unittest

from scripts.s5_curve_uv3_live_scan import (
    S5_MARKET_BLOCK_LAG_CANDIDATES,
    S5_MIN_HISTORICAL_RPC_PROVIDERS,
    _select_s5_historical_scope,
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

    def test_s5_historical_scope_selects_first_candidate_with_quorum(self) -> None:
        class FakePool:
            records = (
                type("R", (), {"provider_id": "p1"})(),
                type("R", (), {"provider_id": "p2"})(),
            )
            def call(self, method, params):
                self.assert_method = (method, params)
                return hex(1_000)
            def probe_historical_state(self, block_number, address):
                if block_number == 968:
                    return (
                        {"provider_id": "p1", "compatible": False, "latency_ms": 1.0, "error": "no"},
                        {"provider_id": "p2", "compatible": False, "latency_ms": 1.0, "error": "no"},
                    )
                return (
                    {"provider_id": "p1", "compatible": True, "latency_ms": 1.0, "error": None},
                    {"provider_id": "p2", "compatible": True, "latency_ms": 1.0, "error": None},
                )
        head, selected, lag, records, history = _select_s5_historical_scope(FakePool())
        self.assertEqual(head, 1_000)
        self.assertEqual(selected, 936)
        self.assertEqual(lag, 64)
        self.assertEqual([r.provider_id for r in records], ["p1", "p2"])
        self.assertEqual(len(history), 2)

    def test_s5_historical_scope_fails_closed_without_quorum(self) -> None:
        class FakePool:
            records = (type("R", (), {"provider_id": "p1"})(),)
            def call(self, method, params):
                return hex(1_000)
            def probe_historical_state(self, block_number, address):
                return ({"provider_id": "p1", "compatible": False, "latency_ms": 1.0, "error": "no"},)
        with self.assertRaises(RuntimeError):
            _select_s5_historical_scope(FakePool())

    def test_s5_market_block_lag_candidates_are_bounded(self) -> None:
        self.assertEqual(tuple(sorted(S5_MARKET_BLOCK_LAG_CANDIDATES)), S5_MARKET_BLOCK_LAG_CANDIDATES)
        self.assertGreater(S5_MARKET_BLOCK_LAG_CANDIDATES[0], 0)
        self.assertLessEqual(S5_MARKET_BLOCK_LAG_CANDIDATES[-1], 1024)
        self.assertEqual(S5_MIN_HISTORICAL_RPC_PROVIDERS, 2)

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