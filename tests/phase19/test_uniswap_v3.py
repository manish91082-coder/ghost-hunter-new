import unittest

from phantomx.uniswap_v3 import (
    BlockSnapshot, UniswapV3Error, UniswapV3ExactQuoter,
    _encode_get_pool, _encode_quote_exact_input_single,
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
    def __init__(self, quote=None, pool=POOL, chain="0x89", block="0x100"):
        self.quote = quote
        self.pool = pool
        self.chain = chain
        self.block = block
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId": return self.chain
        if method == "eth_blockNumber": return self.block
        if method == "eth_call":
            to = params[0]["to"]
            if to == FACTORY: return addr_result(self.pool)
            return self.quote
        raise AssertionError(method)


class UniswapV3Tests(unittest.TestCase):
    def test_factory_and_quoter_calls_are_block_pinned(self):
        rpc = FakeRpc(quote=amount_result(999))
        q = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER)
        out = q.quote(100, A, B, 500, BlockSnapshot(137, 256))
        self.assertEqual(out.amount_out, 999)
        calls = [x for x in rpc.calls if x[0] == "eth_call"]
        self.assertEqual(calls[0][1][1], "0x100")
        self.assertEqual(calls[1][1][1], "0x100")
        self.assertIn(POOL.lower(), calls[1][1][0]["data"])

    def test_polygon_chain_is_required(self):
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(FakeRpc(chain="0x1"), FACTORY, QUOTER).snapshot()

    def test_missing_pool_fails_closed(self):
        rpc = FakeRpc(quote=amount_result(999), pool="0x" + "00" * 20)
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(100, A, B, 500, BlockSnapshot(137, 1))

    def test_zero_quote_fails_closed(self):
        rpc = FakeRpc(quote=amount_result(0))
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(100, A, B, 500, BlockSnapshot(137, 1))

    def test_rpc_error_fails_closed(self):
        class ErrorRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call" and params[0]["to"] == QUOTER:
                    return {"error": {"code": 3}}
                return super().call(method, params)
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(ErrorRpc(quote=amount_result(1)), FACTORY, QUOTER).quote(
                100, A, B, 500, BlockSnapshot(137, 1))

    def test_fee_is_explicit_and_encoded_as_uint24(self):
        data = _encode_get_pool(A, B, 3000)
        raw = bytes.fromhex(data[2:])
        self.assertEqual(int.from_bytes(raw[68:100], "big"), 3000)
        qdata = _encode_quote_exact_input_single(A, B, 500, 123)
        qraw = bytes.fromhex(qdata[2:])
        self.assertEqual(int.from_bytes(qraw[68:100], "big"), 500)

    def test_same_token_rejected(self):
        with self.assertRaises(UniswapV3Error):
            UniswapV3ExactQuoter(FakeRpc(quote=amount_result(1)), FACTORY, QUOTER).quote(
                100, A, A, 500, BlockSnapshot(137, 1))

    def test_result_preserves_exact_integer(self):
        value = 123456789012345678901234567890
        rpc = FakeRpc(quote=amount_result(value))
        out = UniswapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(
            100, A, B, 10000, BlockSnapshot(137, 1))
        self.assertEqual(out.amount_out, value)
        self.assertEqual(out.fee_raw, 10000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
