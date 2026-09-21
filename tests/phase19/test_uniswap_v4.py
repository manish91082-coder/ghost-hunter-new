import unittest

from phantomx.market_block import MarketBlockSnapshot
from phantomx.uniswap_v4 import (
    DEFAULT_FEE_TIERS,
    DEFAULT_TICK_SPACINGS,
    POOL_MANAGER,
    QUOTE_EXACT_INPUT_SINGLE_SELECTOR,
    V4PoolKey,
    UniswapV4Error,
    UniswapV4ExactQuoter,
    _encode_quote_exact_input_single,
)

A = "0x" + "11" * 20
B = "0x" + "22" * 20
HOOK = "0x" + "00" * 20
SNAPSHOT = MarketBlockSnapshot(chain_id=137, block_number=123, timestamp=1_700_000_000)


class FakeRpc:
    def __init__(self, result="0x" + ("00" * 31 + "01") + ("00" * 31 + "02")):
        self.result = result
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method != "eth_call":
            raise AssertionError("unexpected method")
        if params[1] != hex(123):
            raise AssertionError("quote was not block pinned")
        return self.result


class UniswapV4Tests(unittest.TestCase):
    def test_polygon_deployment_constants_are_present(self):
        self.assertEqual(POOL_MANAGER.lower(), "0x67366782805870060151383f4bbff9dab53e5cd6")
        self.assertEqual(DEFAULT_FEE_TIERS, (100, 500, 3000, 10000))
        self.assertEqual(DEFAULT_TICK_SPACINGS, (1, 10, 20, 60, 100, 200))

    def test_pool_key_is_sorted_and_calldata_has_dynamic_hook_data_tail(self):
        key = V4PoolKey(A, B, 3000, 60, HOOK)
        data = _encode_quote_exact_input_single(key, True, 1000, b"")
        self.assertTrue(data.startswith("0xaa9d21cb"))
        self.assertEqual(len(data), 2 + 8 + (10 * 64))

    def test_quote_snapshot_decodes_amount_and_gas(self):
        amount_out = 987654
        gas = 43210
        raw = amount_out.to_bytes(32, "big") + gas.to_bytes(32, "big")
        rpc = FakeRpc("0x" + raw.hex())
        quoter = UniswapV4ExactQuoter(rpc)
        key = V4PoolKey(A, B, 500, 10, HOOK)
        quote = quoter.quote_snapshot(100000, A, B, key, SNAPSHOT)
        self.assertEqual(quote.amount_in, 100000)
        self.assertEqual(quote.amount_out, amount_out)
        self.assertEqual(quote.gas_estimate, gas)
        self.assertEqual(quote.fee_raw, 500)
        self.assertEqual(quote.block_number, 123)

    def test_direction_must_match_pool_key(self):
        rpc = FakeRpc()
        quoter = UniswapV4ExactQuoter(rpc)
        key = V4PoolKey(A, B, 500, 10, HOOK)
        with self.assertRaises(UniswapV4Error):
            quoter.quote_snapshot(1000, B, A, key, SNAPSHOT, zero_for_one=True)

    def test_unsorted_pool_key_fails_closed(self):
        key = V4PoolKey(B, A, 500, 10, HOOK)
        with self.assertRaises(UniswapV4Error):
            _encode_quote_exact_input_single(key, True, 1000)

    def test_malformed_quote_fails_closed(self):
        rpc = FakeRpc("0x" + "00" * 32)
        quoter = UniswapV4ExactQuoter(rpc)
        key = V4PoolKey(A, B, 500, 10, HOOK)
        with self.assertRaises(UniswapV4Error):
            quoter.quote_snapshot(1000, A, B, key, SNAPSHOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
