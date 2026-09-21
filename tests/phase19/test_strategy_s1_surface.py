import unittest

from scripts.s1_qsv3_live_scan import classify_s1_tile
from phantomx.opportunity_discovery import (
    OpportunityCandidate,
    OpportunityDiscoveryResult,
    OpportunityFailure,
)
from phantomx.quickswap_v3 import QuickSwapV3ExactQuoter
from phantomx.cross_venue_qsv3_route import build_quickswap_v3_to_uniswap_v3_route


class StrategyS1SurfaceTests(unittest.TestCase):
    def test_s1_tile_rejects_incomplete_coverage(self):
        class Simulation:
            def __init__(self, amount):
                self.initial_amount = amount
                self.final_amount = amount

        result = OpportunityDiscoveryResult(
            evaluated=(
                OpportunityCandidate(
                    "a", "b", "quickswap_v3->uniswap_v3", 100, Simulation(100)
                ),
            )
        )
        self.assertEqual(
            classify_s1_tile(result=result, expected_evaluations=2),
            "PARTIAL_INCOMPLETE",
        )

    def test_s1_tile_accepts_terminal_no_common_route(self):
        result = OpportunityDiscoveryResult(
            evaluated=(),
            failures=(
                OpportunityFailure(
                    "a", "b", "quickswap_v3->uniswap_v3", 100,
                    "EVM", "execution reverted", False
                ),
                OpportunityFailure(
                    "a", "b", "uniswap_v3->quickswap_v3", 100,
                    "EVM", "execution reverted", False
                ),
            ),
        )
        self.assertEqual(
            classify_s1_tile(result=result, expected_evaluations=2),
            "COMPLETE_NO_COMMON_ROUTE",
        )

    def test_s1_tile_accepts_complete_common_route(self):
        class Simulation:
            def __init__(self, amount):
                self.initial_amount = amount
                self.final_amount = amount

        result = OpportunityDiscoveryResult(
            evaluated=(
                OpportunityCandidate(
                    "a", "b", "quickswap_v3->uniswap_v3", 100, Simulation(100)
                ),
                OpportunityCandidate(
                    "a", "b", "uniswap_v3->quickswap_v3", 100, Simulation(100)
                ),
            )
        )
        self.assertEqual(
            classify_s1_tile(result=result, expected_evaluations=2),
            "COMPLETE",
        )

    def test_s1_objects_construct_with_polygon_adapters(self):
        class Rpc:
            def call(self, method, params):
                if method == "eth_chainId":
                    return "0x89"
                if method == "eth_blockNumber":
                    return "0x100"
                if method == "eth_getBlockByNumber":
                    return {"timestamp": "0x1000"}
                raise AssertionError(method)
        qsv3 = QuickSwapV3ExactQuoter(
            Rpc(),
            "0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28",
            "0xa15F0D7377B2A0C0c10db057f641beD21028FC89",
        )
        self.assertEqual(qsv3.chain_id, 137)


if __name__ == "__main__":
    unittest.main(verbosity=2)
