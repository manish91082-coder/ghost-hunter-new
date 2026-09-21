import unittest
from unittest.mock import Mock, patch

from phantomx.market_block import MarketBlockSnapshot

from phantomx.dynamic_pair_surface import discover_live_base_pairs


class DynamicPairSurfaceTests(unittest.TestCase):
    def test_seed_is_preserved_and_live_pair_is_added(self):
        rpc = Mock()
        rpc.call.side_effect = [
            "0x64",
            [],
        ]
        seeds = (("USDC/WETH", "0x" + "11" * 20),)
        result = discover_live_base_pairs(
            rpc,
            base_token="0x" + "22" * 20,
            seed_pairs=seeds,
            required_venues=("uniswap_v3",),
            lookback_blocks=10,
            chunk_size=10,
        )
        self.assertEqual(result.status, "COMPLETE_RECENT_WINDOW")
        self.assertEqual(len(result.pairs), 1)
        self.assertEqual(result.pairs[0].source, "SEED")

    def test_discovery_error_is_explicit(self):
        rpc = Mock()
        rpc.call.side_effect = RuntimeError("all eligible providers failed")
        with self.assertRaises(RuntimeError):
            discover_live_base_pairs(
                rpc,
                base_token="0x" + "22" * 20,
                seed_pairs=(),
                required_venues=("uniswap_v3",),
            )

    def test_curve_required_is_not_treated_as_unknown_venue(self):
        rpc = Mock()
        rpc.call.return_value = "0x64"
        with patch(
            "phantomx.dynamic_pair_surface.acquire_market_block_at",
            return_value=MarketBlockSnapshot(chain_id=137, block_number=100, timestamp=1_700_000_000),
        ), patch(
            "phantomx.dynamic_pair_surface.CurveRegistryExactQuoter"
        ) as curve_quoter:
            curve_quoter.return_value.find_pools_for_pair.return_value = []
            result = discover_live_base_pairs(
                rpc,
                base_token="0x" + "22" * 20,
                seed_pairs=(("USDC/WETH", "0x" + "11" * 20),),
                required_venues=("curve",),
                lookback_blocks=10,
                chunk_size=10,
            )
        self.assertEqual(result.status, "PAIR_UNIVERSE_INCOMPLETE")
        self.assertEqual(len(result.pairs), 1)
        self.assertEqual(result.pairs[0].source, "SEED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
