import unittest

from scripts.s6_triangular_live_scan import _quote
from phantomx.market_block import MarketBlockSnapshot


class FakeUniswap:
    def __init__(self):
        self.calls = []

    def quote_snapshot(self, amount, token_in, token_out, fee, context):
        self.calls.append((amount, token_in, token_out, fee, context.block_number))
        return {"fee": fee}


class S6TriangularLiveScanTests(unittest.TestCase):
    def test_uniswap_fee_tier_is_explicitly_forwarded(self):
        adapter = FakeUniswap()
        context = MarketBlockSnapshot(chain_id=137, block_number=123, timestamp=1_700_000_000)
        adapters = {"uniswap": adapter}
        for fee in (100, 500, 3000, 10000):
            result = _quote(
                adapters,
                "uniswap_v3",
                1_000_000,
                "0x" + "11" * 20,
                "0x" + "22" * 20,
                context,
                uniswap_fee=fee,
            )
            self.assertEqual(result["fee"], fee)
        self.assertEqual([c[3] for c in adapter.calls], [100, 500, 3000, 10000])
        self.assertTrue(all(c[4] == 123 for c in adapter.calls))

    def test_unknown_venue_fails_closed(self):
        with self.assertRaises(RuntimeError):
            _quote(
                {"uniswap": FakeUniswap()},
                "unknown",
                1_000_000,
                "0x" + "11" * 20,
                "0x" + "22" * 20,
                MarketBlockSnapshot(chain_id=137, block_number=123, timestamp=1_700_000_000),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
