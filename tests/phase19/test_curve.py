import unittest

from phantomx.curve import (
    _address_word,
    CURVE_FACTORY_REGISTRY,
    COINS_SELECTOR,
    FIND_POOL_FOR_COINS_INDEXED_SELECTOR,
    FEE_SELECTOR,
    FIND_POOL_FOR_COINS_SELECTOR,
    GET_COIN_INDICES_SELECTOR,
    GET_DY_SELECTOR,
    GET_FEES_SELECTOR,
    POOL_COUNT_SELECTOR,
    POOL_LIST_SELECTOR,
    CurveRegistryExactQuoter,
    CurvePoolRef,
)
from phantomx.market_block import MarketBlockSnapshot

A = "0x" + "11" * 20
B = "0x" + "22" * 20
POOL = "0x" + "33" * 20
SNAP = MarketBlockSnapshot(chain_id=137, block_number=77, timestamp=1_700_000_000)


class FakeRpc:
    def __init__(self):
        self.calls = []
        self.ambiguous_failover_calls = 0

    def call_with_ambiguous_revert_failover(self, method, params):
        self.ambiguous_failover_calls += 1
        return self.call(method, params)

    def call(self, method, params):
        self.calls.append((method, params))
        if method != "eth_call" or params[1] != hex(77):
            raise AssertionError("unexpected RPC envelope")
        data = params[0]["data"]
        if data.startswith(FIND_POOL_FOR_COINS_SELECTOR) or data.startswith(FIND_POOL_FOR_COINS_INDEXED_SELECTOR):
            return "0x" + "00" * 12 + POOL[2:]
        if data.startswith(GET_COIN_INDICES_SELECTOR):
            return "0x" + (0).to_bytes(32, "big").hex() + (1).to_bytes(32, "big").hex() + (0).to_bytes(32, "big").hex()
        if data.startswith(GET_FEES_SELECTOR):
            return "0x" + (4_000_000).to_bytes(32, "big").hex() + (0).to_bytes(32, "big").hex()
        if data.startswith(GET_DY_SELECTOR):
            return "0x" + (99_900).to_bytes(32, "big").hex()
        raise AssertionError("unexpected calldata")


class CurveAdapterTests(unittest.TestCase):
    def test_address_word_is_exactly_32_bytes(self):
        word = _address_word("0x" + "11" * 20)
        self.assertEqual(len(word), 32)
        self.assertEqual(word[:12], b"\x00" * 12)
        self.assertEqual(word[12:], bytes.fromhex("11" * 20))

    def test_selector_constants(self):
        self.assertEqual(POOL_COUNT_SELECTOR, "0x956aae3a")
        self.assertEqual(POOL_LIST_SELECTOR, "0x3a1d5d8e")
        self.assertEqual(FIND_POOL_FOR_COINS_SELECTOR, "0xa87df06c")
        self.assertEqual(FIND_POOL_FOR_COINS_INDEXED_SELECTOR, "0x6982eb0b")
        self.assertEqual(GET_COIN_INDICES_SELECTOR, "0xeb85226d")
        self.assertEqual(GET_FEES_SELECTOR, "0x7cdb72b0")
        self.assertEqual(GET_DY_SELECTOR, "0x5e0d443f")

    def test_rpc_transport_failure_is_wrapped_as_curve_error(self):
        class BrokenRpc(FakeRpc):
            def call(self, method, params):
                raise RuntimeError("429")

        q = CurveRegistryExactQuoter(BrokenRpc(), (("factory", CURVE_FACTORY_REGISTRY),))
        with self.assertRaises(Exception) as ctx:
            q.pool_count(CURVE_FACTORY_REGISTRY, SNAP)
        self.assertIn("transport failure", str(ctx.exception))

    def test_registry_execution_revert_is_terminal_no_pool(self):
        class RevertingRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call" and (
                    params[0]["data"].startswith(FIND_POOL_FOR_COINS_SELECTOR)
                    or params[0]["data"].startswith(FIND_POOL_FOR_COINS_INDEXED_SELECTOR)
                ):
                    raise RuntimeError("execution reverted")
                return super().call(method, params)

        rpc = RevertingRpc()
        q = CurveRegistryExactQuoter(rpc, (("factory", CURVE_FACTORY_REGISTRY),))
        pools = q.find_pools_for_pair(A, B, SNAP, max_pools_per_registry=2)
        self.assertEqual(pools, [])

    def test_find_pools_uses_pair_lookup_and_binds_block(self):
        rpc = FakeRpc()
        q = CurveRegistryExactQuoter(rpc, (( "factory", CURVE_FACTORY_REGISTRY),))
        pools = q.find_pools_for_pair(A, B, SNAP, max_pools_per_registry=2)
        self.assertEqual(len(pools), 1)
        self.assertEqual(pools[0].pool.lower(), POOL.lower())
        self.assertEqual(pools[0].i, 0)
        self.assertEqual(pools[0].j, 1)
        self.assertEqual(pools[0].fee_raw, 4_000_000)

    def test_direct_seed_pool_resolves_coin_indices_from_pool_state(self):
        class SeedRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call" and params[0]["data"].startswith(COINS_SELECTOR):
                    index = int(params[0]["data"][-64:], 16)
                    coin = A if index == 0 else B if index == 1 else "0x" + "00" * 20
                    return "0x" + "00" * 12 + coin[2:]
                if method == "eth_call" and params[0]["data"] == FEE_SELECTOR:
                    return "0x" + (4_000_000).to_bytes(32, "big").hex()
                return super().call(method, params)

        rpc = SeedRpc()
        q = CurveRegistryExactQuoter(rpc, (("factory", CURVE_FACTORY_REGISTRY),))
        ref = q.direct_pool_ref(POOL, A, B, SNAP)
        self.assertEqual((ref.i, ref.j), (0, 1))
        self.assertEqual(ref.fee_raw, 4_000_000)
    def test_quote_snapshot_is_block_pinned(self):
        rpc = FakeRpc()
        q = CurveRegistryExactQuoter(rpc, (( "factory", CURVE_FACTORY_REGISTRY),))
        ref = CurvePoolRef("factory", CURVE_FACTORY_REGISTRY, POOL, A, B, 0, 1, False, 4_000_000)
        snap = q.quote_snapshot(100_000, ref, SNAP)
        self.assertEqual(snap.amount_in, 100_000)
        self.assertEqual(snap.amount_out, 99_900)
        self.assertEqual(snap.fee_raw, 4_000_000)
        self.assertEqual(snap.block_number, 77)
        self.assertEqual(rpc.ambiguous_failover_calls, 1)

    def test_underlying_mode_uses_underlying_selector(self):
        class UnderlyingRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_call" and params[0]["data"].startswith("0x07211ef7"):
                    self.calls.append((method, params))
                    return "0x" + (100_100).to_bytes(32, "big").hex()
                return super().call(method, params)

        rpc = UnderlyingRpc()
        q = CurveRegistryExactQuoter(rpc, (( "factory", CURVE_FACTORY_REGISTRY),))
        ref = CurvePoolRef("factory", CURVE_FACTORY_REGISTRY, POOL, A, B, 0, 1, True, 4_000_000)
        snap = q.quote_snapshot(100_000, ref, SNAP)
        self.assertEqual(snap.amount_out, 100_100)
        self.assertTrue(any(c[1][0]["data"].startswith("0x07211ef7") for c in rpc.calls))

if __name__ == "__main__":
    unittest.main(verbosity=2)
