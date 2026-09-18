import unittest

from phantomx.market_block import MarketBlockSnapshot
from phantomx.ramses_v3 import (
    DEFAULT_TICK_SPACINGS,
    FEE_SELECTOR,
    GET_POOL_SELECTOR,
    QUOTE_EXACT_INPUT_SINGLE_SELECTOR,
    RamsesV3Error,
    RamsesV3ExactQuoter,
    _encode_get_pool,
    _encode_quote_exact_input_single,
)


class FakeRpc:
    def __init__(self):
        self.calls = []
        self.pool = "0x" + "99" * 20
        self.fee = 3000
        self.amount_out = 101_234
        self.sqrt_after = 2**96
        self.ticks_crossed = 7
        self.gas_estimate = 180_000

    def call(self, method, params):
        self.calls.append((method, params))
        call = params[0]
        data = call["data"]
        block = params[1]
        if method != "eth_call" or block != hex(100):
            raise AssertionError("unexpected RPC envelope")
        if data.startswith("0x" + GET_POOL_SELECTOR):
            return "0x" + "00" * 12 + self.pool[2:]
        if data == "0x" + FEE_SELECTOR:
            return "0x" + self.fee.to_bytes(32, "big").hex()
        if data.startswith("0x" + QUOTE_EXACT_INPUT_SINGLE_SELECTOR):
            values = (
                self.amount_out.to_bytes(32, "big")
                + self.sqrt_after.to_bytes(32, "big")
                + self.ticks_crossed.to_bytes(32, "big")
                + self.gas_estimate.to_bytes(32, "big")
            )
            return "0x" + values.hex()
        raise AssertionError(f"unexpected calldata prefix: {data[:10]}")


def snapshot(block=100):
    return MarketBlockSnapshot(
        chain_id=137,
        block_number=block,
        timestamp=1_700_000_000,
    )


class RamsesV3AdapterTests(unittest.TestCase):
    def test_abi_selectors_and_default_tick_spacings(self):
        self.assertEqual(GET_POOL_SELECTOR, "28af8d0b")
        self.assertEqual(QUOTE_EXACT_INPUT_SINGLE_SELECTOR, "9e7defe6")
        self.assertEqual(FEE_SELECTOR, "ddca3f43")
        self.assertEqual(DEFAULT_TICK_SPACINGS, (1, 5, 10, 50, 100, 200))

    def test_pool_encoder_has_int24_word(self):
        data = _encode_get_pool(
            "0x" + "11" * 20,
            "0x" + "22" * 20,
            -5,
        )
        self.assertTrue(data.startswith("0x28af8d0b"))
        self.assertEqual(len(data), 2 + 8 + 32 * 3 * 2)

    def test_quote_encoder_binds_tick_spacing_and_limit(self):
        data = _encode_quote_exact_input_single(
            "0x" + "11" * 20,
            "0x" + "22" * 20,
            1234,
            10,
            99,
        )
        self.assertTrue(data.startswith("0x9e7defe6"))
        self.assertEqual(len(data), 2 + 8 + 32 * 5 * 2)

    def test_quote_snapshot_reads_pool_fee_and_preserves_block(self):
        rpc = FakeRpc()
        quoter = RamsesV3ExactQuoter(
            rpc,
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        quote = quoter.quote_snapshot(
            100_000,
            "0x" + "11" * 20,
            "0x" + "22" * 20,
            10,
            snapshot(),
        )
        self.assertEqual(quote.amount_in, 100_000)
        self.assertEqual(quote.amount_out, rpc.amount_out)
        self.assertEqual(quote.fee_raw, rpc.fee)
        self.assertEqual(quote.pool_or_router.lower(), rpc.pool)
        self.assertEqual(quote.block_number, 100)
        self.assertEqual(quote.gas_estimate, rpc.gas_estimate)
        self.assertEqual(len(rpc.calls), 3)

    def test_snapshot_mismatch_fails_closed(self):
        rpc = FakeRpc()
        quoter = RamsesV3ExactQuoter(
            rpc,
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        with self.assertRaises(RamsesV3Error):
            quoter.resolve_pool(
                "0x" + "11" * 20,
                "0x" + "22" * 20,
                10,
                snapshot(101),
            )

    def test_zero_fee_is_rejected(self):
        rpc = FakeRpc()
        rpc.fee = 0
        quoter = RamsesV3ExactQuoter(
            rpc,
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        with self.assertRaises(RamsesV3Error):
            quoter.pool_fee(rpc.pool, snapshot())

    def test_malformed_quote_is_rejected(self):
        class BadRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call" and params[0]["data"].startswith("0x" + QUOTE_EXACT_INPUT_SINGLE_SELECTOR):
                    return "0x" + "00" * 32
                return super().call(method, params)

        quoter = RamsesV3ExactQuoter(
            BadRpc(),
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        with self.assertRaises(RamsesV3Error):
            quoter.quote_snapshot(
                100_000,
                "0x" + "11" * 20,
                "0x" + "22" * 20,
                10,
                snapshot(),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
