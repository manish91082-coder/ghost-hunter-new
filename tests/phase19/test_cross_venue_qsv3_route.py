import unittest

from phantomx.quickswap_v3 import QuickSwapV3ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from phantomx.cross_venue_qsv3_route import (
    build_quickswap_v3_to_uniswap_v3_route,
    build_uniswap_v3_to_quickswap_v3_route,
)


FACTORY_QS = "0x" + "11"*20
QUOTER_QS = "0x" + "22"*20
FACTORY_U3 = "0x" + "33"*20
QUOTER_U3 = "0x" + "44"*20
A = "0x" + "aa"*20
B = "0x" + "bb"*20
POOL_QS = "0x" + "55"*20
POOL_U3 = "0x" + "66"*20


def addr_result(address):
    return "0x" + (b"\x00"*12 + bytes.fromhex(address[2:])).hex()


def u256(value):
    return "0x" + value.to_bytes(32,"big").hex()


def qs_quote(amount, fee):
    return u256(amount) + u256(fee)


class FakeRPC:
    def __init__(self):
        self.calls=[]
        self.chain="0x89"; self.block="0x100"; self.ts="0x1000"
        self.default_qs_quote = qs_quote(99,157)
    def call(self, method, params):
        self.calls.append((method,params))
        if method=="eth_chainId": return self.chain
        if method=="eth_blockNumber": return self.block
        if method=="eth_getBlockByNumber": return {"timestamp":self.ts}
        if method=="eth_call":
            to=params[0]["to"]
            if to==FACTORY_QS: return addr_result(POOL_QS)
            if to==QUOTER_QS: return self.default_qs_quote
            if to==FACTORY_U3: return addr_result(POOL_U3)
            if to==QUOTER_U3: return u256(98)
        raise AssertionError(method)


class QSV3RouteTests(unittest.TestCase):
    def test_both_directions_share_one_block(self):
        rpc=FakeRPC()
        q=QuickSwapV3ExactQuoter(rpc,FACTORY_QS,QUOTER_QS)
        u=UniswapV3ExactQuoter(rpc,FACTORY_U3,QUOTER_U3)
        snap=q.snapshot()
        forward=build_quickswap_v3_to_uniswap_v3_route(
            rpc,q,u,amount_in=100,token_a=A,token_b=B,uniswap_fee=500,block=snap)
        reverse=build_uniswap_v3_to_quickswap_v3_route(
            rpc,q,u,amount_in=100,token_a=A,token_b=B,uniswap_fee=500,block=snap)
        self.assertEqual(forward.block_number,256)
        self.assertEqual(reverse.block_number,256)
        self.assertEqual(forward.legs[0].fee_raw,157)
        self.assertEqual(reverse.legs[1].fee_raw,157)
        self.assertEqual(forward.legs[1].fee_raw,500)
        self.assertEqual(reverse.legs[0].fee_raw,500)

    def test_route_requires_pinned_block_context(self):
        rpc=FakeRPC()
        q=QuickSwapV3ExactQuoter(rpc,FACTORY_QS,QUOTER_QS)
        u=UniswapV3ExactQuoter(rpc,FACTORY_U3,QUOTER_U3)
        route=build_quickswap_v3_to_uniswap_v3_route(
            rpc,q,u,amount_in=100,token_a=A,token_b=B,uniswap_fee=3000)
        self.assertEqual(route.chain_id,137)
        self.assertEqual(route.block_number,256)

if __name__=="__main__":
    unittest.main(verbosity=2)
