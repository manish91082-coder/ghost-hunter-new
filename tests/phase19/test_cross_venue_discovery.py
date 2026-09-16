import unittest

from phantomx.cross_venue_discovery import (
    QUICKSWAP_TO_UNISWAP_PATH,
    UNISWAP_TO_QUICKSWAP_PATH,
    discover_cross_venue_opportunities,
)
from phantomx.market_block import MarketBlockSnapshot
from phantomx.quickswap_v2 import QuickSwapV2ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

ROUTER = "0x" + "11" * 20
FACTORY = "0x" + "22" * 20
QUOTER = "0x" + "33" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
POOL = "0x" + "cc" * 20


def array_result(amount_in, amount_out):
    values = (amount_in, amount_out)
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

    @staticmethod
    def _quick_amount(data):
        return int(data[10:74], 16)

    @staticmethod
    def _uniswap_amount(data):
        return int(data[202:266], 16)

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId": return "0x89"
        if method == "eth_blockNumber": return "0x1234"
        if method == "eth_getBlockByNumber": return {"timestamp": "0x1000"}
        if method == "eth_call":
            to = params[0]["to"]
            data = params[0]["data"]
            if to == ROUTER:
                amount = self._quick_amount(data)
                return array_result(amount, amount + 100)
            if to == FACTORY: return address_result(POOL)
            if to == QUOTER:
                amount = self._uniswap_amount(data)
                return amount_result(amount + 100)
        raise AssertionError((method, params))


class CrossVenueDiscoveryTests(unittest.TestCase):
    def test_scans_both_directions_and_all_loan_sizes_on_one_pinned_block(self):
        rpc = FakeRpc()
        result = discover_cross_venue_opportunities(
            rpc,
            QuickSwapV2ExactQuoter(rpc, ROUTER),
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
            token_pairs=((A, B),),
            loan_amounts=(1_000, 2_000),
            uniswap_fee=500,
        )

        self.assertEqual(len(result.evaluated), 4)
        self.assertEqual(len(result.gross_positive), 4)
        self.assertEqual(
            [candidate.venue_path for candidate in result.evaluated],
            [QUICKSWAP_TO_UNISWAP_PATH, QUICKSWAP_TO_UNISWAP_PATH,
             UNISWAP_TO_QUICKSWAP_PATH, UNISWAP_TO_QUICKSWAP_PATH],
        )
        self.assertEqual({candidate.simulation.block_number for candidate in result.evaluated}, {0x1234})
        self.assertEqual({candidate.simulation.chain_id for candidate in result.evaluated}, {137})
        self.assertEqual({candidate.loan_amount for candidate in result.evaluated}, {1_000, 2_000})

        block_queries = [call for call in rpc.calls if call[0] in {"eth_blockNumber", "eth_getBlockByNumber"}]
        self.assertEqual([call[0] for call in block_queries], ["eth_blockNumber", "eth_getBlockByNumber"])

    def test_explicit_block_context_avoids_any_block_discovery_io(self):
        rpc = FakeRpc()
        context = MarketBlockSnapshot(137, 0x7777, 0x3000)
        result = discover_cross_venue_opportunities(
            rpc,
            QuickSwapV2ExactQuoter(rpc, ROUTER),
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
            token_pairs=((A, B),),
            loan_amounts=(1_000,),
            uniswap_fee=500,
            block=context,
        )

        self.assertEqual(len(result.evaluated), 2)
        self.assertTrue(all(candidate.simulation.block_number == 0x7777 for candidate in result.evaluated))
        self.assertFalse(any(call[0] == "eth_blockNumber" for call in rpc.calls))
        self.assertFalse(any(call[0] == "eth_getBlockByNumber" for call in rpc.calls))

    def test_invalid_fee_fails_before_market_io(self):
        rpc = FakeRpc()
        with self.assertRaises(ValueError):
            discover_cross_venue_opportunities(
                rpc,
                QuickSwapV2ExactQuoter(rpc, ROUTER),
                UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
                token_pairs=((A, B),),
                loan_amounts=(1_000,),
                uniswap_fee=1 << 24,
            )
        self.assertEqual(rpc.calls, [])


if __name__ == "__main__":
    unittest.main()
