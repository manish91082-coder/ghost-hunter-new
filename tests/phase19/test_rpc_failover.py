import unittest
from unittest.mock import Mock, patch

from phantomx.rpc_failover import PolygonRPCFailoverPool, PublicRPCRecord, RPCPoolError


class RPCFailoverTests(unittest.TestCase):
    def test_first_provider_failure_switches_same_logical_request(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(side_effect=TimeoutError("timeout"))
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        self.assertEqual([item.provider_id for item in pool.history], ["p1", "p2"])

    def test_rpc_execution_revert_is_not_retried_on_next_provider(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(
            return_value={"error": {"code": -32000, "message": "execution reverted"}}
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        with self.assertRaises(RPCPoolError):
            pool.call("eth_call", [])
        self.assertEqual([item.provider_id for item in pool.history], ["p1"])
        self.assertFalse(pool.history[0].recoverable)
        pool._states["p2"].transport.call.assert_not_called()

    def test_ambiguous_unexpected_revert_switches_to_next_provider(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(
            return_value={"error": {"code": 3, "message": "execution reverted: Unexpected error"}}
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call("eth_call", []), "0x89")
        self.assertEqual([item.provider_id for item in pool.history], ["p1", "p2"])
        self.assertTrue(pool.history[0].recoverable)

    def test_provider_access_error_403_switches_to_next_provider(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(side_effect=Exception("HTTP transport failure status=403"))
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        self.assertEqual([item.provider_id for item in pool.history], ["p1", "p2"])

    def test_wrong_chain_provider_is_rejected_then_next_provider_used(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(return_value={"result": "0x1"})
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        self.assertEqual([item.provider_id for item in pool.history], ["p1", "p2"])

    def test_bounded_second_pass_recovers_after_circuit_open(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records, failure_threshold=1)
        pool._states["p1"].transport.call = Mock(side_effect=[RuntimeError("timeout"), RuntimeError("timeout")])
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        self.assertEqual(pool.history[-1].provider_id, "p2")
    def test_all_ambiguous_reverts_are_reported_after_provider_exhaustion(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        response = {"error": {"code": 3, "message": "execution reverted: Unexpected error"}}
        pool._states["p1"].transport.call = Mock(return_value=response)
        pool._states["p2"].transport.call = Mock(return_value=response)
        with self.assertRaises(RPCPoolError):
            pool.call("eth_call", [])
        self.assertEqual(len(pool.history), 4)
        self.assertTrue(all(item.recoverable for item in pool.history))

    def test_all_rpc_reverts_are_reported_after_provider_exhaustion(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(
            return_value={"error": {"code": 3, "message": "execution reverted"}}
        )
        pool._states["p2"].transport.call = Mock(
            return_value={"error": {"code": 3, "message": "execution reverted"}}
        )
        with self.assertRaises(RPCPoolError):
            pool.call("eth_call", [{"to": "0x" + "11" * 20, "data": "0x"}, "latest"])
        self.assertEqual(len(pool.history), 1)
        self.assertFalse(pool.history[0].recoverable)
        pool._states["p2"].transport.call.assert_not_called()
    def test_all_transport_failures_are_reported_after_exhaustion(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(side_effect=TimeoutError("timeout"))
        pool._states["p2"].transport.call = Mock(side_effect=TimeoutError("timeout"))
        with self.assertRaises(RPCPoolError) as ctx:
            pool.call("eth_blockNumber", [])
        self.assertIn("all bounded Polygon RPC recovery passes failed", str(ctx.exception))
        self.assertEqual(len(pool.history), 4)

    def test_disabled_provider_is_never_used(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1", enabled=False),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(return_value={"result": "bad"})
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        self.assertEqual(pool.history[0].provider_id, "p2")

    def test_circuit_breaking_happens_after_repeated_transport_failures(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(
            records=records, failure_threshold=1, circuit_cooldown_seconds=100
        )
        pool._states["p1"].transport.call = Mock(side_effect=TimeoutError("timeout"))
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        with patch("phantomx.rpc_failover.monotonic", return_value=10.0):
            self.assertEqual(pool.call("eth_chainId", []), "0x89")
        self.assertGreater(pool._states["p1"].circuit_open_until, 10.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)