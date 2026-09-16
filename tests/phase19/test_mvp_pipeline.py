import unittest
from decimal import Decimal

from phantomx.economics import CostBreakdown
from phantomx.mvp_pipeline import MvpPipelineError, MvpPipelineRequest, UsdValuation, build_mvp_candidate
from phantomx.quickswap_v2 import QuickSwapV2ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

ROUTER = "0x" + "11" * 20
FACTORY = "0x" + "22" * 20
QUOTER = "0x" + "33" * 20
AAVE = "0x" + "44" * 20
EXECUTOR = "0x" + "55" * 20
SENDER = "0x" + "66" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20


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
        if method == "eth_chainId":
            return "0x89"
        if method == "eth_blockNumber":
            return "0x1234"
        if method == "eth_getBlockByNumber":
            return {"timestamp": "0x1000"}
        if method == "eth_call":
            to = params[0]["to"]
            if to == ROUTER:
                return array_result([1_000_000, 900_000])
            if to == FACTORY:
                return address_result("0x" + "77" * 20)
            if to == QUOTER:
                return amount_result(1_100_000)
        raise AssertionError((method, params))


def make_request(**overrides):
    values = dict(
        amount_in=1_000_000,
        token_a=A,
        token_b=B,
        uniswap_fee=500,
        aave_pool=AAVE,
        quickswap_router=ROUTER,
        uniswap_v3_router="0x" + "88" * 20,
        executor=EXECUTOR,
        sender=SENDER,
        nonce=7,
        deadline=2_000_000_000,
        amount_out_min_first=890_000,
        amount_out_min_second=1_090_000,
        minimum_surplus=1_000,
        gas_limit=500_000,
        max_fee_per_gas=100,
        max_priority_fee_per_gas=30,
        max_gas_usd=Decimal("0.50"),
        max_relay_usd=Decimal("0.20"),
        valuation=UsdValuation("0x" + "99" * 32, Decimal("102.00"), Decimal("100.00")),
        costs=CostBreakdown(gas=Decimal("0.20"), relay=Decimal("0.05"), other=Decimal("0.10")),
    )
    values.update(overrides)
    return MvpPipelineRequest(**values)


class MvpPipelineTests(unittest.TestCase):
    def test_full_pre_execution_mvp_path_produces_bound_candidate(self):
        rpc = FakeRpc()
        candidate = build_mvp_candidate(
            rpc,
            QuickSwapV2ExactQuoter(rpc, ROUTER),
            UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
            make_request(),
        )
        self.assertEqual(candidate.simulation.initial_amount, 1_000_000)
        self.assertEqual(candidate.simulation.final_amount, 1_100_000)
        self.assertTrue(candidate.economically_valid)
        self.assertTrue(candidate.route_hash.startswith("0x"))
        self.assertTrue(candidate.intent_hash.startswith("0x"))
        self.assertEqual(candidate.assembly.envelope.chain_id, 137)
        self.assertEqual(candidate.assembly.envelope.nonce, 7)
        self.assertTrue(all(method in {"eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_call"} for method, _ in rpc.calls))

    def test_candidate_below_strict_profit_floor_is_rejected(self):
        rpc = FakeRpc()
        request = make_request(
            valuation=UsdValuation("0x" + "99" * 32, Decimal("100.36"), Decimal("100.00")),
            costs=CostBreakdown(gas=Decimal("0.20"), relay=Decimal("0.05"), other=Decimal("0.10")),
        )
        with self.assertRaises(MvpPipelineError.__mro__[1]):
            build_mvp_candidate(
                rpc,
                QuickSwapV2ExactQuoter(rpc, ROUTER),
                UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
                request,
            )

    def test_max_priority_fee_cannot_exceed_max_fee(self):
        rpc = FakeRpc()
        request = make_request(max_fee_per_gas=20, max_priority_fee_per_gas=30)
        with self.assertRaises(MvpPipelineError):
            build_mvp_candidate(
                rpc,
                QuickSwapV2ExactQuoter(rpc, ROUTER),
                UniswapV3ExactQuoter(rpc, FACTORY, QUOTER),
                request,
            )


if __name__ == "__main__":
    unittest.main()
