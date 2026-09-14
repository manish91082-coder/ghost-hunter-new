import unittest

from phantomx.quickswap_v2 import (
    BlockSnapshot,
    QuickSwapV2Error,
    QuickSwapV2ExactQuoter,
    _decode_uint_array,
    _encode_get_amounts_out,
)

ROUTER = "0x" + "11" * 20
TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20
TOKEN_C = "0x" + "cc" * 20


def encode_uint_array(values):
    raw = bytearray()
    raw.extend((32).to_bytes(32, "big"))
    raw.extend(len(values).to_bytes(32, "big"))
    for value in values:
        raw.extend(value.to_bytes(32, "big"))
    return "0x" + bytes(raw).hex()


class FakeRpc:
    def __init__(self, chain="0x89", block="0x1234", timestamp="0x2000", quote=None):
        self.chain = chain
        self.block = block
        self.timestamp = timestamp
        self.quote = quote
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return self.chain
        if method == "eth_blockNumber":
            return self.block
        if method == "eth_getBlockByNumber":
            return {"timestamp": self.timestamp}
        if method == "eth_call":
            if self.quote is None:
                raise AssertionError("unexpected eth_call")
            return self.quote
        raise AssertionError(method)


class QuickSwapV2ExactQuoteTests(unittest.TestCase):
    def test_abi_selector_and_dynamic_path_encoding(self):
        data = _encode_get_amounts_out(123, [TOKEN_A, TOKEN_B])
        self.assertTrue(data.startswith("0xd06ca61f"))
        raw = bytes.fromhex(data[2:])
        self.assertEqual(int.from_bytes(raw[4:36], "big"), 123)
        self.assertEqual(int.from_bytes(raw[36:68], "big"), 64)
        self.assertEqual(int.from_bytes(raw[68:100], "big"), 2)
        self.assertEqual(raw[112:132], bytes.fromhex("aa" * 20))
        self.assertEqual(raw[144:164], bytes.fromhex("bb" * 20))

    def test_snapshot_verifies_polygon_chain_pins_block_and_timestamp(self):
        rpc = FakeRpc(block="0x4567", timestamp="0x89ab")
        snapshot = QuickSwapV2ExactQuoter(rpc, ROUTER).snapshot()
        self.assertEqual(snapshot, BlockSnapshot(137, 0x4567, 0x89AB))
        self.assertEqual(
            [c[0] for c in rpc.calls],
            ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"],
        )
        self.assertEqual(rpc.calls[-1][1], ["0x4567", False])

    def test_missing_block_timestamp_fails_closed(self):
        class BadBlockRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_getBlockByNumber":
                    return {"number": self.block}
                return super().call(method, params)

        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(BadBlockRpc(), ROUTER).snapshot()

    def test_malformed_block_result_fails_closed(self):
        class BadBlockRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_getBlockByNumber":
                    return "0x1000"
                return super().call(method, params)

        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(BadBlockRpc(), ROUTER).snapshot()

    def test_non_positive_block_timestamp_fails_closed(self):
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(FakeRpc(timestamp="0x0"), ROUTER).snapshot()

    def test_wrong_chain_fails_closed(self):
        rpc = FakeRpc(chain="0x1")
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).snapshot()

    def test_quote_uses_exact_router_output_at_snapshot_block(self):
        amount_in = 10**18
        amount_out = 997 * 10**15
        rpc = FakeRpc(quote=encode_uint_array([amount_in, amount_out]))
        quoter = QuickSwapV2ExactQuoter(rpc, ROUTER)
        quote = quoter.quote(amount_in, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 0x1234, 0x2000))

        self.assertEqual(quote.amount_in, amount_in)
        self.assertEqual(quote.amount_out, amount_out)
        self.assertEqual(quote.block_number, 0x1234)
        call = rpc.calls[-1]
        self.assertEqual(call[0], "eth_call")
        self.assertEqual(call[1][0]["to"], ROUTER)
        self.assertEqual(call[1][1], "0x1234")

    def test_quote_snapshot_uses_pinned_block_timestamp(self):
        amount_in = 100
        rpc = FakeRpc(timestamp="0x2000", quote=encode_uint_array([amount_in, 120]))
        quoter = QuickSwapV2ExactQuoter(rpc, ROUTER)
        snapshot = quoter.snapshot()
        evidence = quoter.quote_snapshot(amount_in, [TOKEN_A, TOKEN_B], snapshot, gas_estimate=120000)
        self.assertEqual(evidence.chain_id, 137)
        self.assertEqual(evidence.block_number, 0x1234)
        self.assertEqual(evidence.observed_at_unix, 0x2000)
        self.assertEqual(evidence.amount_out, 120)
        self.assertEqual(len(evidence.quote_hash), 66)

    def test_quote_rejects_non_positive_snapshot_timestamp(self):
        rpc = FakeRpc(quote=encode_uint_array([10, 20]))
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).quote(10, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 99, 0))

    def test_multihop_path_preserves_router_returned_final_integer(self):
        amount_in = 123456789012345678901
        rpc = FakeRpc(quote=encode_uint_array([amount_in, 456789, 987654321]))
        quote = QuickSwapV2ExactQuoter(rpc, ROUTER).quote(
            amount_in, [TOKEN_A, TOKEN_B, TOKEN_C], BlockSnapshot(137, 99, 2000)
        )
        self.assertEqual(quote.amount_out, 987654321)
        self.assertEqual(quote.token_in, TOKEN_A)
        self.assertEqual(quote.token_out, TOKEN_C)

    def test_quote_rejects_snapshot_from_wrong_chain(self):
        rpc = FakeRpc(quote=encode_uint_array([10, 20]))
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).quote(10, [TOKEN_A, TOKEN_B], BlockSnapshot(1, 99, 2000))

    def test_malformed_rpc_result_fails_closed(self):
        rpc = FakeRpc(quote="0x1234")
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).quote(10, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 1, 2000))

    def test_unexpected_array_length_fails_closed(self):
        rpc = FakeRpc(quote=encode_uint_array([10, 20, 30]))
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).quote(10, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 1, 2000))

    def test_router_input_mismatch_fails_closed(self):
        rpc = FakeRpc(quote=encode_uint_array([11, 20]))
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).quote(10, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 1, 2000))

    def test_zero_output_fails_closed(self):
        rpc = FakeRpc(quote=encode_uint_array([10, 0]))
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(rpc, ROUTER).quote(10, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 1, 2000))

    def test_invalid_address_fails_closed(self):
        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(FakeRpc(), "0x123")

    def test_eth_call_error_object_is_not_accepted_as_quote(self):
        class ErrorRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call":
                    return {"error": {"code": 3, "message": "execution reverted"}}
                return super().call(method, params)

        with self.assertRaises(QuickSwapV2Error):
            QuickSwapV2ExactQuoter(ErrorRpc(), ROUTER).quote(
                10, [TOKEN_A, TOKEN_B], BlockSnapshot(137, 1, 2000)
            )

    def test_decode_rejects_bad_offset(self):
        bad = bytearray(bytes.fromhex(encode_uint_array([10, 20])[2:]))
        bad[:32] = (64).to_bytes(32, "big")
        with self.assertRaises(QuickSwapV2Error):
            _decode_uint_array("0x" + bytes(bad).hex(), 2)


if __name__ == "__main__":
    unittest.main()
