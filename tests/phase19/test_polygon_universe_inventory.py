import unittest
from unittest.mock import Mock

from phantomx.market_graph import PoolEdge
from phantomx.polygon_universe_inventory import InventoryTask, run_inventory_task
from phantomx.polygon_venue_inventory import VENUE_SPECS


class UniverseInventoryCoordinatorTests(unittest.TestCase):
    def test_empty_range_is_explicitly_onchain_unavailable(self):
        spec = next(x for x in VENUE_SPECS if x.venue_id == "uniswap_v3")
        rpc = Mock()
        rpc.call.return_value = []
        result = run_inventory_task(
            rpc, spec, InventoryTask("uniswap_v3", 100, 100, chunk_size=10)
        )
        self.assertEqual(result.status, "ONCHAIN_UNAVAILABLE")
        self.assertEqual(result.edges, ())
        self.assertTrue(result.evidence_hash)

    def test_decoded_log_becomes_graph_edge(self):
        spec = next(x for x in VENUE_SPECS if x.venue_id == "uniswap_v3")
        token0 = "0x" + "11" * 20
        token1 = "0x" + "22" * 20
        pool = "0x" + "33" * 20
        rpc = Mock()
        rpc.call.return_value = [{
            "blockNumber": "0x64",
            "transactionHash": "0x" + "aa" * 32,
            "logIndex": "0x0",
            "address": spec.factory_or_manager,
            "topics": [
                spec.topic0,
                "0x" + "00" * 12 + "11" * 20,
                "0x" + "00" * 12 + "22" * 20,
                "0x" + (500).to_bytes(32, "big").hex(),
            ],
            "data": "0x" + (10).to_bytes(32, "big").hex() + (int(pool,16)).to_bytes(32, "big").hex(),
        }]
        result = run_inventory_task(
            rpc, spec, InventoryTask("uniswap_v3", 100, 100, chunk_size=10)
        )
        self.assertEqual(result.status, "QUOTED")
        self.assertEqual(len(result.edges), 1)
        self.assertEqual(result.edges[0].token_in, token0.lower())

    def test_rpc_exhaustion_is_not_no_opportunity(self):
        spec = next(x for x in VENUE_SPECS if x.venue_id == "uniswap_v3")
        rpc = Mock()
        rpc.call.side_effect = RuntimeError("all eligible Polygon RPC providers failed: 429 timeout")
        result = run_inventory_task(
            rpc, spec, InventoryTask("uniswap_v3", 100, 100, chunk_size=10)
        )
        self.assertEqual(result.status, "RPC_EXHAUSTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
