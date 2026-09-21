import unittest

from phantomx.market_block import MarketBlockSnapshot
from phantomx.ramses_v3 import (
    DEFAULT_TICK_SPACINGS,
    FEE_SELECTOR,
    GET_POOL_SELECTOR,
    QUOTE_EXACT_INPUT_SINGLE_SELECTOR,
    SLOT0_SELECTOR,
    LIQUIDITY_SELECTOR,
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
        if method != "eth_call" or block not in (hex(100), hex(101)):
            raise AssertionError("unexpected RPC envelope")
        if data.startswith("0x" + GET_POOL_SELECTOR):
            return "0x" + "00" * 12 + self.pool[2:]
        if data == "0x" + FEE_SELECTOR:
            return "0x" + self.fee.to_bytes(32, "big").hex()
        if data == "0x" + SLOT0_SELECTOR:
            words = [
                (2**96).to_bytes(32, "big"),
                (0).to_bytes(32, "big"),
                (0).to_bytes(32, "big"),
                (1).to_bytes(32, "big"),
                (1).to_bytes(32, "big"),
                (0).to_bytes(32, "big"),
                (1).to_bytes(32, "big"),
            ]
            return "0x" + b"".join(words).hex()
        if data == "0x" + LIQUIDITY_SELECTOR:
            return "0x" + (10**18).to_bytes(32, "big").hex()
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
        self.assertEqual(SLOT0_SELECTOR, "3850c7bd")
        self.assertEqual(LIQUIDITY_SELECTOR, "1a686502")

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

    def test_pool_state_requires_initialized_active_unlocked_pool(self):
        rpc = FakeRpc()
        quoter = RamsesV3ExactQuoter(
            rpc,
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        state = quoter.pool_state(rpc.pool, snapshot())
        self.assertEqual(state.sqrt_price_x96, 2**96)
        self.assertEqual(state.active_liquidity, 10**18)
        self.assertTrue(state.unlocked)
        self.assertTrue(state.initialized_and_swappable)

        class DormantRpc(FakeRpc):
            def call(self, method, params):
                call = params[0]
                if method == "eth_call" and call["data"] == "0x" + SLOT0_SELECTOR:
                    words = [
                        (0).to_bytes(32, "big"),
                        (0).to_bytes(32, "big"),
                        (0).to_bytes(32, "big"),
                        (0).to_bytes(32, "big"),
                        (0).to_bytes(32, "big"),
                        (0).to_bytes(32, "big"),
                        (1).to_bytes(32, "big"),
                    ]
                    return "0x" + b"".join(words).hex()
                if method == "eth_call" and call["data"] == "0x" + LIQUIDITY_SELECTOR:
                    return "0x" + (0).to_bytes(32, "big").hex()
                return super().call(method, params)

        dormant = RamsesV3ExactQuoter(
            DormantRpc(),
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        dormant_state = dormant.pool_state(rpc.pool, snapshot())
        self.assertFalse(dormant_state.initialized_and_swappable)

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

    def test_supplied_snapshot_block_is_used_for_pool_resolution(self):
        rpc = FakeRpc()
        quoter = RamsesV3ExactQuoter(
            rpc,
            "0x" + "33" * 20,
            "0x" + "44" * 20,
        )
        pool = quoter.resolve_pool(
            "0x" + "11" * 20,
            "0x" + "22" * 20,
            10,
            snapshot(101),
        )
        self.assertEqual(pool.lower(), rpc.pool)
        self.assertEqual(rpc.calls[-1][1][1], hex(101))

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
