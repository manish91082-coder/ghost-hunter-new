import unittest
from unittest.mock import Mock, patch

from phantomx.rpc_failover import (
    DEFAULT_FREE_POLYGON_RPC_POOL,
    PolygonRPCFailoverPool,
    PublicRPCRecord,
    RPCPoolError,
    RPCSemanticRevertConsensusError,
)


class RPCFailoverTests(unittest.TestCase):

    def test_current_free_pool_matches_declared_public_registry(self):
        providers = {record.provider_id: record for record in DEFAULT_FREE_POLYGON_RPC_POOL}
        required = {
            "drpc-public",
            "tenderly-public",
            "publicnode-public",
            "nodies-public",
            "one-rpc-public",
            "onfinality-public",
            "tatum-public",
        }
        self.assertTrue(required.issubset(providers))
        self.assertNotIn("polygon-public", providers)

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

    def test_single_ambiguous_revert_gets_one_bounded_same_provider_retry(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(
            records=records,
            provider_admission_wait_seconds=0.01,
            ambiguous_revert_retry_delay_seconds=0.001,
        )
        response = {"error": {"code": 3, "message": "execution reverted"}}
        pool._states["p1"].transport.call = Mock(side_effect=[
            response,
            {"result": "0x89"},
        ])
        pool._states["p2"].in_flight = 1
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})

        self.assertEqual(
            pool.call_with_ambiguous_revert_failover("eth_call", []),
            "0x89",
        )
        self.assertEqual(pool._states["p1"].transport.call.call_count, 2)
        self.assertEqual(pool._states["p2"].transport.call.call_count, 0)

    def test_reasoned_rpc_execution_revert_is_not_retried_on_next_provider(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(
            return_value={"error": {"code": -32000, "message": "execution reverted: PoolSwapFailed"}}
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        with self.assertRaises(RPCPoolError):
            pool.call("eth_call", [])
        self.assertEqual([item.provider_id for item in pool.history], ["p1"])
        self.assertFalse(pool.history[0].recoverable)
        pool._states["p2"].transport.call.assert_not_called()

    def test_reasonless_rpc_execution_revert_is_opt_in_failover(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        pool._states["p1"].transport.call = Mock(
            return_value={"error": {"code": 3, "message": "execution reverted"}}
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        self.assertEqual(pool.call_with_ambiguous_revert_failover("eth_call", []), "0x89")
        self.assertEqual([item.provider_id for item in pool.history], ["p1", "p2"])
        self.assertTrue(pool.history[0].recoverable)

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
        self.assertEqual(pool.call_with_ambiguous_revert_failover("eth_call", []), "0x89")
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
    def test_ambiguous_revert_does_not_poison_provider_health(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
        )
        pool = PolygonRPCFailoverPool(
            records=records,
            failure_threshold=1,
            circuit_cooldown_seconds=100,
        )
        response = {"error": {"code": 3, "message": "execution reverted"}}
        pool._states["p1"].transport.call = Mock(return_value=response)

        for _ in range(2):
            with self.assertRaises(RPCPoolError):
                pool.call_with_ambiguous_revert_failover("eth_call", [])

        stats = {item["provider_id"]: item for item in pool.provider_stats()}
        self.assertFalse(stats["p1"]["circuit_open"])
        self.assertEqual(stats["p1"]["consecutive_failures"], 0)
        self.assertAlmostEqual(stats["p1"]["health_score"], 1.0)
        self.assertEqual(pool._states["p1"].transport.call.call_count, 4)

    def test_ambiguous_revert_consensus_stops_after_two_distinct_providers(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records)
        response = {"error": {"code": 3, "message": "execution reverted: Unexpected error"}}
        pool._states["p1"].transport.call = Mock(return_value=response)
        pool._states["p2"].transport.call = Mock(return_value=response)
        with self.assertRaises(RPCSemanticRevertConsensusError):
            pool.call_with_ambiguous_revert_failover("eth_call", [])
        self.assertEqual([item.provider_id for item in pool.history], ["p1", "p2"])
        self.assertTrue(all(item.recoverable for item in pool.history))
        pool._states["p1"].transport.call.assert_called_once()
        pool._states["p2"].transport.call.assert_called_once()

    def test_failed_provider_is_not_reused_when_alternates_are_unavailable(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records, provider_admission_wait_seconds=0.01)
        pool._states["p2"].in_flight = 1
        pool._states["p1"].transport.call = Mock(side_effect=TimeoutError("timeout"))
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})
        with self.assertRaises(RPCPoolError):
            pool.call("eth_chainId", [])
        self.assertEqual(pool._states["p1"].transport.call.call_count, 1)
        self.assertEqual(pool._states["p2"].transport.call.call_count, 0)

    def test_all_rpc_reverts_are_terminal_by_default(self):
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


    def test_threaded_requests_respect_per_provider_concurrency_limit(self):
        import threading
        import time

        records = tuple(
            PublicRPCRecord(f"p{i}", f"https://p{i}.example", f"f{i}", max_concurrency=1)
            for i in range(4)
        )
        pool = PolygonRPCFailoverPool(records=records)

        lock = threading.Lock()
        barrier = threading.Barrier(4)
        active = 0
        max_active = 0

        def call(provider_transport):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.03)
            with lock:
                active -= 1
            return {"result": "0x89"}

        for state in pool._states.values():
            state.transport.call = Mock(side_effect=lambda method, params, _state=state: call(_state.transport))

        results = [None] * 4
        errors = []

        def worker(index):
            try:
                barrier.wait(timeout=2)
                results[index] = pool.call("eth_chainId", [])
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        self.assertEqual(errors, [])
        self.assertEqual(results, ["0x89"] * 4)
        self.assertGreaterEqual(max_active, 2)
        for state in pool._states.values():
            self.assertLessEqual(state.transport.call.call_count, 1)


    def test_recovery_waits_for_a_different_provider_before_reusing_failed_one(self):
        import threading
        import time

        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1", max_concurrency=1),
            PublicRPCRecord("p2", "https://p2.example", "f2", max_concurrency=1),
        )
        pool = PolygonRPCFailoverPool(
            records=records,
            provider_admission_wait_seconds=1.0,
        )
        pool._states["p2"].in_flight = 1
        pool._states["p1"].transport.call = Mock(side_effect=TimeoutError("timeout"))
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})

        def release_provider():
            time.sleep(0.05)
            with pool._lock:
                pool._states["p2"].in_flight = 0

        releaser = threading.Thread(target=release_provider)
        releaser.start()
        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        releaser.join(timeout=1)

        self.assertEqual(
            [item.provider_id for item in pool.history if not item.success],
            ["p1"],
        )
        self.assertEqual([item.provider_id for item in pool.history if item.success], ["p2"])
        self.assertEqual(pool._states["p1"].transport.call.call_count, 1)
        self.assertEqual(pool._states["p2"].transport.call.call_count, 1)

    def test_saturated_provider_pool_waits_for_capacity_without_zero_attempt_failure(self):
        import threading
        import time

        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1", max_concurrency=1),
        )
        pool = PolygonRPCFailoverPool(
            records=records,
            provider_admission_wait_seconds=1.0,
        )
        started = threading.Event()
        release = threading.Event()

        def blocked_call(method, params):
            started.set()
            self.assertTrue(release.wait(timeout=1.0))
            return {"result": "0x89"}

        pool._states["p1"].transport.call = Mock(side_effect=blocked_call)
        first_result, second_result, errors = [], [], []

        def worker(target):
            try:
                target.append(pool.call("eth_chainId", []))
            except Exception as exc:
                errors.append(exc)

        first = threading.Thread(target=worker, args=(first_result,))
        first.start()
        self.assertTrue(started.wait(timeout=1.0))

        second = threading.Thread(target=worker, args=(second_result,))
        second.start()
        time.sleep(0.05)
        release.set()

        first.join(timeout=2)
        second.join(timeout=2)

        self.assertEqual(errors, [])
        self.assertEqual(first_result, ["0x89"])
        self.assertEqual(second_result, ["0x89"])
        self.assertEqual(pool._states["p1"].transport.call.call_count, 2)


    def test_auth_or_paid_plan_failure_quarantines_provider(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records, provider_fatal_cooldown_seconds=600)
        pool._states["p1"].transport.call = Mock(
            return_value={
                "error": {
                    "code": -32000,
                    "message": "Method 'eth_call' is available for paid plans only.",
                }
            }
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})

        self.assertEqual(pool.call("eth_call", []), "0x89")
        stats = {item["provider_id"]: item for item in pool.provider_stats()}
        self.assertTrue(stats["p1"]["quarantined"])
        pool._states["p1"].transport.call.assert_called_once()
        pool._states["p2"].transport.call.assert_called_once()

    def test_401_provider_is_quarantined_and_skipped_on_recovery_round(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records, provider_fatal_cooldown_seconds=600)
        pool._states["p1"].transport.call = Mock(
            side_effect=Exception("HTTP transport failure status=401")
        )
        pool._states["p2"].transport.call = Mock(
            return_value={
                "error": {
                    "code": 3,
                    "message": "execution reverted: Unexpected error",
                }
            }
        )

        with self.assertRaises(RPCPoolError):
            pool.call_with_ambiguous_revert_failover("eth_call", [])

        self.assertEqual(pool._states["p1"].transport.call.call_count, 1)
        self.assertEqual(pool._states["p2"].transport.call.call_count, 2)
        stats = {item["provider_id"]: item for item in pool.provider_stats()}
        self.assertTrue(stats["p1"]["quarantined"])


    def test_rate_limited_provider_is_temporarily_quarantined(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(records=records, provider_temporary_cooldown_seconds=60)
        pool._states["p1"].transport.call = Mock(
            side_effect=Exception("HTTP transport failure status=429")
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})

        self.assertEqual(pool.call("eth_chainId", []), "0x89")
        stats = {item["provider_id"]: item for item in pool.provider_stats()}
        self.assertTrue(stats["p1"]["quarantined"])
        self.assertEqual(pool._states["p1"].transport.call.call_count, 1)
        self.assertEqual(pool._states["p2"].transport.call.call_count, 1)

    def test_historical_state_failure_is_task_local_not_provider_health_failure(self):
        records = (
            PublicRPCRecord("p1", "https://p1.example", "f1"),
            PublicRPCRecord("p2", "https://p2.example", "f2"),
        )
        pool = PolygonRPCFailoverPool(
            records=records,
            failure_threshold=1,
            circuit_cooldown_seconds=600,
        )
        pool._states["p1"].transport.call = Mock(
            side_effect=Exception(
                "eth_call: RPC error code=-32000 message=historical state unavailable"
            )
        )
        pool._states["p2"].transport.call = Mock(return_value={"result": "0x89"})

        self.assertEqual(pool.call("eth_call", []), "0x89")
        stats = {item["provider_id"]: item for item in pool.provider_stats()}
        self.assertFalse(stats["p1"]["quarantined"])
        self.assertFalse(stats["p1"]["circuit_open"])
        self.assertEqual(stats["p1"]["consecutive_failures"], 0)
        self.assertAlmostEqual(stats["p1"]["health_score"], 1.0)
        self.assertEqual(pool._states["p1"].transport.call.call_count, 1)
        self.assertEqual(pool._states["p2"].transport.call.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)