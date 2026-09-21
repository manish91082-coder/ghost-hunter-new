import unittest

from phantomx.balancer_v2 import (
    BALANCER_V2_VAULT,
    POOL_REGISTERED_TOPIC,
    BalancerInventoryError,
    BalancerV2Inventory,
    BalancerPool,
)
from phantomx.market_block import MarketBlockSnapshot


class BalancerInventoryTests(unittest.TestCase):
    def snapshot(self):
        return MarketBlockSnapshot(137, 100, 1234567890)

    def test_pool_registered_decoding(self):
        rpc = object()
        inv = BalancerV2Inventory(rpc)
        pool_id = "0x" + "11" * 32
        pool = "0x" + "22" * 20
        log = {
            "address": BALANCER_V2_VAULT,
            "topics": [POOL_REGISTERED_TOPIC, pool_id, "0x" + "00" * 12 + "22" * 20],
            "data": "0x" + (1).to_bytes(32, "big").hex(),
        }
        self.assertEqual(inv.decode_pool_registered(log), (pool_id, pool, 1))

    def test_get_pool_tokens_decodes_dynamic_arrays(self):
        pool_id = "0x" + "11" * 32
        token_a = "0x" + "22" * 20
        token_b = "0x" + "33" * 20
        tokens_offset = 96
        balances_offset = 96 + 32 + 64
        encoded = (
            tokens_offset.to_bytes(32, "big")
            + balances_offset.to_bytes(32, "big")
            + (99).to_bytes(32, "big")
            + (2).to_bytes(32, "big")
            + (int(token_a, 16)).to_bytes(32, "big")
            + (int(token_b, 16)).to_bytes(32, "big")
            + (2).to_bytes(32, "big")
            + (1000).to_bytes(32, "big")
            + (2000).to_bytes(32, "big")
        )
        class RPC:
            def call(self, method, params):
                return "0x" + encoded.hex()
        inv = BalancerV2Inventory(RPC())
        tokens, balances, last = inv.get_pool_tokens(pool_id, self.snapshot())
        self.assertEqual(tokens, (token_a, token_b))
        self.assertEqual(balances, (1000, 2000))
        self.assertEqual(last, 99)

    def test_graph_edges_cover_all_positive_balance_directed_pairs(self):
        pool = BalancerPool(
            "0x" + "11" * 32,
            "0x" + "22" * 20,
            1,
            ("0x" + "33" * 20, "0x" + "44" * 20, "0x" + "55" * 20),
            (100, 200, 300),
            90,
            100,
        )
        edges = BalancerV2Inventory.graph_edges(pool)
        self.assertEqual(len(edges), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
