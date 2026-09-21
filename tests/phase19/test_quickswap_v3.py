import unittest

from phantomx.quickswap_v3 import (
    BlockSnapshot,
    QuickSwapV3Error,
    QuickSwapV3ExactQuoter,
    _encode_pool_by_pair,
    _encode_quote_exact_input_single,
)

FACTORY = "0x" + "11" * 20
QUOTER = "0x" + "22" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
POOL = "0x" + "cc" * 20


def addr_result(address):
    return "0x" + (b"\x00" * 12 + bytes.fromhex(address[2:])).hex()


def quote_result(amount_out, fee):
    return "0x" + amount_out.to_bytes(32, "big").hex() + fee.to_bytes(32, "big").hex()


class FakeRpc:
    def __init__(self, quote=None, pool=POOL, chain="0x89", block="0x100", timestamp="0x1000"):
        self.quote = quote
        self.pool = pool
        self.chain = chain
        self.block = block
        self.timestamp = timestamp
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
            to = params[0]["to"]
            if to == FACTORY:
                return addr_result(self.pool)
            return self.quote
        raise AssertionError(method)


class QuickSwapV3Tests(unittest.TestCase):
    def test_snapshot_binds_chain_block(self):
        rpc = FakeRpc(quote=quote_result(999, 157))
        snap = QuickSwapV3ExactQuoter(rpc, FACTORY, QUOTER).snapshot()
        self.assertEqual(snap, BlockSnapshot(137, 256, 4096))

    def test_pool_lookup_and_quote_are_block_pinned(self):
        rpc = FakeRpc(quote=quote_result(999, 157))
        q = QuickSwapV3ExactQuoter(rpc, FACTORY, QUOTER)
        out = q.quote(100, A, B, BlockSnapshot(137, 256, 4096))
        self.assertEqual(out.amount_out, 999)
        self.assertEqual(out.fee_raw, 157)
        calls = [x for x in rpc.calls if x[0] == "eth_call"]
        self.assertEqual(calls[0][1][1], "0x100")
        self.assertEqual(calls[1][1][1], "0x100")

    def test_pool_by_pair_selector_and_abi_shape(self):
        data = _encode_pool_by_pair(A, B)
        raw = bytes.fromhex(data[2:])
        self.assertEqual(raw[:4], bytes.fromhex("d9a641e1"))
        self.assertEqual(len(raw), 4 + 64)
        self.assertEqual(raw[4:36], b"\x00"*12 + bytes.fromhex(A[2:]))
        self.assertEqual(raw[36:68], b"\x00"*12 + bytes.fromhex(B[2:]))

    def test_quoter_selector_and_abi_shape(self):
        data = _encode_quote_exact_input_single(A, B, 123)
        raw = bytes.fromhex(data[2:])
        self.assertEqual(raw[:4], bytes.fromhex("2d9ebd1d"))
        self.assertEqual(len(raw), 4 + 4*32)
        self.assertEqual(raw[4:36], b"\x00"*12 + bytes.fromhex(A[2:]))
        self.assertEqual(raw[36:68], b"\x00"*12 + bytes.fromhex(B[2:]))
        self.assertEqual(int.from_bytes(raw[68:100],"big"),123)
        self.assertEqual(int.from_bytes(raw[100:132],"big"),0)

    def test_missing_pool_fails_closed(self):
        rpc = FakeRpc(quote=quote_result(1, 10), pool="0x"+"00"*20)
        with self.assertRaises(QuickSwapV3Error):
            QuickSwapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(100,A,B,BlockSnapshot(137,1,100))

    def test_zero_quote_fails_closed(self):
        rpc = FakeRpc(quote=quote_result(0,10))
        with self.assertRaises(QuickSwapV3Error):
            QuickSwapV3ExactQuoter(rpc, FACTORY, QUOTER).quote(100,A,B,BlockSnapshot(137,1,100))

    def test_dynamic_fee_is_taken_from_quoter(self):
        rpc = FakeRpc(quote=quote_result(1_000_000, 327))
        q = QuickSwapV3ExactQuoter(rpc, FACTORY, QUOTER)
        out = q.quote(100,A,B,BlockSnapshot(137,1,100))
        self.assertEqual(out.fee_raw,327)

    def test_quote_snapshot_preserves_dynamic_fee(self):
        rpc = FakeRpc(quote=quote_result(999,157))
        q=QuickSwapV3ExactQuoter(rpc,FACTORY,QUOTER)
        e=q.quote_snapshot(100,A,B,BlockSnapshot(137,256,4096))
        self.assertEqual(e.fee_raw,157)
        self.assertEqual(e.pool_or_router.lower(),POOL.lower())

    def test_wrong_chain_blocks(self):
        with self.assertRaises(QuickSwapV3Error):
            QuickSwapV3ExactQuoter(FakeRpc(chain="0x1",quote=quote_result(1,1)),FACTORY,QUOTER).snapshot()

    def test_same_token_blocks(self):
        with self.assertRaises(QuickSwapV3Error):
            QuickSwapV3ExactQuoter(FakeRpc(quote=quote_result(1,1)),FACTORY,QUOTER).quote(100,A,A,BlockSnapshot(137,1,100))

    def test_malformed_quoter_result_blocks(self):
        rpc=FakeRpc(quote="0x1234")
        with self.assertRaises(QuickSwapV3Error):
            QuickSwapV3ExactQuoter(rpc,FACTORY,QUOTER).quote(100,A,B,BlockSnapshot(137,1,100))


if __name__=="__main__":
    unittest.main(verbosity=2)
