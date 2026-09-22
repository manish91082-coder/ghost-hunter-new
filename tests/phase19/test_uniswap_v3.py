import unittest

from phantomx.uniswap_v3 import (
    BlockSnapshot, UniswapV3Error, UniswapV3ExactQuoter,
    _address_word, _encode_get_pool, _encode_quote_exact_input_single,
)

FACTORY = "0x" + "11" * 20
QUOTER = "0x" + "22" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
POOL = "0x" + "cc" * 20


def addr_result(address):
    return "0x" + (b"\x00" * 12 + bytes.fromhex(address[2:])).hex()


def amount_result(amount):
    return "0x" + amount.to_bytes(32, "big").hex()


class FakeRpc:
    def __init__(self, quote=None, pool=POOL, chain="0x89", block="0x100", timestamp="0x1000"):
        self.quote = quote
        self.pool = pool
        self.chain = chain
        self.ambiguous_failover_calls = 0
        self.block = block
        self.timestamp = timestamp
        self.calls = []

    def call_with_ambiguous_revert_failover(self, method, params):
        self.ambiguous_failover_calls += 1
        return self.call(method, params)

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId": return self.chain
        if method == "eth_blockNumber": return self.block
        if method == "eth_getBlockByNumber": return {"timestamp": self.timestamp}
        if method == "eth_call":
            to = params[0]["to"]
            if to == FACTORY: return addr_result(self.pool)
            return self.quote
        raise AssertionError(method)


class UniswapV3Tests(unittest.TestCase):
    def test_snapshot_binds_chain_block_and_timestamp(self):
        rpc = FakeRpc()
        snapshot = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).snapshot()
        self.assertEqual(snapshot, BlockSnapshot(137, 256, 4096))
        block_calls = [x for x in rpc.calls if x[0] == "eth_getBlockByNumber"]
        self.assertEqual(block_calls[0][1], ["0x100", False])

    def test_factory_and_quoter_calls_are_block_pinned(self):
        rpc = FakeRpc(quote=amount_result(999))
        q = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER)
        out = q.quote(100, A, B, 500, BlockSnapshot(137, 256, 4096))
        self.assertEqual(out.amount_out, 999)
        self.assertEqual(rpc.ambiguous_failover_calls, 1)
        calls = [x for x in rpc.calls if x[0] == "eth_call"]
        self.assertEqual(calls[0][1][1], "0x100")
        self.assertEqual(calls[1][1][1], "0x100")
        # Quoter V1 quoteExactInputSingle is keyed by tokenIn/tokenOut/fee,
        # not by pool address. Pool resolution belongs to the preceding
        # factory call, so the quoter calldata must contain the requested
        # token addresses rather than the resolved pool address.
        self.assertIn(A[2:].lower(), calls[1][1][0]["data"])
        self.assertIn(B[2:].lower(), calls[1][1][0]["data"])
        self.assertNotIn(POOL[2:].lower(), calls[1][1][0]["data"])

    def test_polygon_chain_is_required(self):
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(FakeRpc(chain="0x1"), FACTORY, QUOTER).snapshot()

    def test_missing_block_timestamp_fails_closed(self):
        class BadBlockRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_getBlockByNumber":
                    return {"number": self.block}
                return super().call(method, params)
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(BadBlockRpc(), FACTORY, QUOTER).snapshot()

    def test_malformed_block_result_fails_closed(self):
        class BadBlockRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_getBlockByNumber":
                    return "0x1000"
                return super().call(method, params)
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(BadBlockRpc(), FACTORY, QUOTER).snapshot()

    def test_missing_pool_fails_closed(self):
        rpc = FakeRpc(quote=amount_result(999), pool="0x" + "00" * 20)
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(100, A, B, 500, BlockSnapshot(137, 1, 100))

    def test_missing_pool_is_cached_across_amounts_and_directions(self):
        rpc = FakeRpc(quote=amount_result(999), pool="0x" + "00" * 20)
        q = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER)
        snapshot = BlockSnapshot(137, 1, 100)
        with self.assertRaises(UniswapV3Error):
            q.quote(100, A, B, 500, snapshot)
        with self.assertRaises(UniswapV3Error):
            q.quote(200, B, A, 500, snapshot)
        factory_calls = [
            call for call in rpc.calls
            if call[0] == "eth_call" and call[1][0]["to"] == FACTORY
        ]
        self.assertEqual(len(factory_calls), 1)

    def test_missing_pool_cache_is_block_scoped(self):
        rpc = FakeRpc(quote=amount_result(999), pool="0x" + "00" * 20)
        q = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER)
        with self.assertRaises(UniswapV3Error):
            q.quote(100, A, B, 500, BlockSnapshot(137, 1, 100))
        with self.assertRaises(UniswapV3Error):
            q.quote(100, A, B, 500, BlockSnapshot(137, 2, 101))
        factory_calls = [
            call for call in rpc.calls
            if call[0] == "eth_call" and call[1][0]["to"] == FACTORY
        ]
        self.assertEqual(len(factory_calls), 2)

    def test_zero_quote_fails_closed(self):
        rpc = FakeRpc(quote=amount_result(0))
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(100, A, B, 500, BlockSnapshot(137, 1, 100))

    def test_rpc_error_fails_closed(self):
        class ErrorRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call" and params[0]["to"] == QUOTER:
                    return {"error": {"code": 3}}
                return super().call(method, params)
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(ErrorRpc(quote=amount_result(1)), FACTORY, QUOTER).quote(
                100, A, B, 500, BlockSnapshot(137, 1, 100))

    def test_quoter_v1_selector_and_abi_shape_are_exact(self):
        data = _encode_quote_exact_input_single(A, B, 500, 123)
        raw = bytes.fromhex(data[2:])
        self.assertEqual(raw[:4], bytes.fromhex("f7729d43"))
        self.assertEqual(len(raw), 4 + 5 * 32)
        self.assertEqual(raw[4:36], _address_word(A))
        self.assertEqual(raw[36:68], _address_word(B))
        self.assertEqual(int.from_bytes(raw[68:100], "big"), 500)
        self.assertEqual(int.from_bytes(raw[100:132], "big"), 123)
        self.assertEqual(int.from_bytes(raw[132:164], "big"), 0)

    def test_swap_router_selector_is_not_used_for_quoter(self):
        data = _encode_quote_exact_input_single(A, B, 500, 123)
        self.assertFalse(data.startswith("0x414bf389"))
        self.assertTrue(data.startswith("0xf7729d43"))

    def test_fee_is_explicit_and_encoded_as_uint24(self):
        data = _encode_get_pool(A, B, 3000)
        raw = bytes.fromhex(data[2:])
        self.assertEqual(int.from_bytes(raw[68:100], "big"), 3000)

    def test_same_token_rejected(self):
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(FakeRpc(quote=amount_result(1)), FACTORY, QUOTER).quote(
                100, A, A, 500, BlockSnapshot(137, 1, 100))

    def test_result_preserves_exact_integer(self):
        value = 123456789012345678901234567890
        rpc = FakeRpc(quote=amount_result(value))
        out = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(
            100, A, B, 10000, BlockSnapshot(137, 1, 100))
        self.assertEqual(out.amount_out, value)
        self.assertEqual(out.fee_raw, 10000)

    def test_quote_snapshot_is_hash_bound_to_block_timestamp(self):
        rpc = FakeRpc(quote=amount_result(999))
        q = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER)
        snapshot = q.snapshot()
        evidence = q.quote_snapshot(100, A, B, 500, snapshot, gas_estimate=180000)
        self.assertEqual(evidence.chain_id, 137)
        self.assertEqual(evidence.block_number, 256)
        self.assertEqual(evidence.observed_at_unix, 4096)
        self.assertEqual(evidence.amount_out, 999)
        self.assertEqual(len(evidence.quote_hash), 66)


if __name__ == "__main__":
    unittest.main(verbosity=2)
