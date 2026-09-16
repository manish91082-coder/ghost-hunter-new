import unittest

from phantomx.cross_venue_route import build_quickswap_to_uniswap_route, build_uniswap_to_quickswap_route
from phantomx.market_block import MarketBlockSnapshot
from phantomx.quickswap_v2 import QuickSwapV2ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

ROUTER = "0x" + "11" * 20
FACTORY = "0x" + "22" * 20
QUOTER = "0x" + "33" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
POOL = "0x" + "cc" * 20


def array_result(values):
    raw = bytearray((32).to_bytes(32, "big") + len(values).to_bytes(32, "big"))
    for value in values:
        raw.extend(value.to_bytes(32, "big"))
    return "0x" + bytes(raw).hex()


def address_result(address):
    return "0x" + (b"\x00" * 12 + bytes.fromhex(address[2:])).hex()


def amount_result(value):
    return "0x" + value.to_bytes(32, "big").hex()


class FakeRpc:
    def __init__(self):
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId": return "0x89"
        if method == "eth_blockNumber": return "0x1234"
        if method == "eth_getBlockByNumber": return {"timestamp": "0x1000"}
        if method == "eth_call":
            to = params[0]["to"]
            if to == ROUTER:
                # Route direction is inferred from the quoted path and only
                # the amount continuity matters for this unit fixture.
                return array_result([1000, 900])
            if to == FACTORY: return address_result(POOL)
            if to == QUOTER: return amount_result(1100)
        raise AssertionError((method, params))


class CrossVenueRouteTests(unittest.TestCase):
    def test_quickswap_to_uniswap_uses_one_shared_block_and_exact_continuity(self):
        rpc = FakeRpc()
        route = build_quickswap_to_uniswap_route(
            rpc, QuickSwapV2ExactQuoter(rpc, ROUTER),
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
            amount_in=1000, token_a=A, token_b=B, uniswap_fee=500,
            quickswap_gas_estimate=100000, uniswap_gas_estimate=120000,
        )
        self.assertEqual(route.chain_id, 137)
        self.assertEqual(route.block_number, 0x1234)
        self.assertEqual(route.initial_amount, 1000)
        self.assertEqual(route.final_amount, 1100)
        self.assertEqual(route.legs[0].amount_out, 900)
        self.assertEqual(route.legs[1].amount_in, 900)
        self.assertEqual(route.legs[0].observed_at_unix, 0x1000)
        self.assertEqual(route.legs[1].observed_at_unix, 0x1000)
        eth_calls = [x for x in rpc.calls if x[0] == "eth_call"]
        self.assertTrue(all(x[1][1] == "0x1234" for x in eth_calls))

    def test_uniswap_to_quickswap_reverses_venue_order_at_same_block(self):
        rpc = FakeRpc()
        context = MarketBlockSnapshot(137, 0x9999, 0x2000)
        route = build_uniswap_to_quickswap_route(
            rpc, QuickSwapV2ExactQuoter(rpc, ROUTER),
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
            amount_in=1000, token_a=A, token_b=B, uniswap_fee=500, block=context,
        )
        self.assertEqual(route.block_number, 0x9999)
        self.assertEqual(route.initial_amount, 1000)
        self.assertEqual(route.final_amount, 1100)
        self.assertEqual(route.legs[0].venue.split(":", 1)[0], "uniswap_v3")
        self.assertEqual(route.legs[1].venue, "quickswap_v2")
        self.assertEqual(route.legs[0].amount_out, 1100)
        self.assertEqual(route.legs[1].amount_in, 1100)
        self.assertEqual(route.legs[0].observed_at_unix, 0x2000)
        self.assertEqual(route.legs[1].observed_at_unix, 0x2000)
        self.assertFalse(any(x[0] == "eth_blockNumber" for x in rpc.calls))

    def test_explicit_shared_context_prevents_second_block_acquisition(self):
        rpc = FakeRpc()
        context = MarketBlockSnapshot(137, 0x9999, 0x2000)
        route = build_quickswap_to_uniswap_route(
            rpc, QuickSwapV2ExactQuoter(rpc, ROUTER),
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
            amount_in=1000, token_a=A, token_b=B, uniswap_fee=500, block=context,
        )
        self.assertEqual(route.block_number, 0x9999)
        self.assertEqual(route.legs[0].observed_at_unix, 0x2000)
        self.assertEqual(route.legs[1].observed_at_unix, 0x2000)
        self.assertFalse(any(x[0] == "eth_blockNumber" for x in rpc.calls))


if __name__ == "__main__":
    unittest.main()
