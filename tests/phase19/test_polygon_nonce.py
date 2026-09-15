import unittest

from phantomx.polygon_nonce import (
    ChainNonceObservation,
    PolygonNonceError,
    parse_rpc_nonce_response,
    pending_nonce,
    quorum_pending_nonce,
    reconcile,
)


class PolygonNonceTests(unittest.TestCase):
    def test_pending_rpc_quantity_is_parsed(self):
        seen = []

        def transport(method, sender, tag):
            seen.append((method, sender, tag))
            return {"jsonrpc": "2.0", "id": 1, "result": "0x2a"}

        obs = pending_nonce(transport, "0xAbC", provider="rpc-a")
        self.assertEqual(obs.pending_nonce, 42)
        self.assertEqual(obs.sender, "0xabc")
        self.assertEqual(seen, [("eth_getTransactionCount", "0xAbC", "pending")])

    def test_rpc_error_fails_closed(self):
        with self.assertRaises(PolygonNonceError):
            parse_rpc_nonce_response({"error": {"code": -32000}}, sender="0xabc")

    def test_invalid_quantity_fails_closed(self):
        with self.assertRaises(PolygonNonceError):
            parse_rpc_nonce_response({"result": "42"}, sender="0xabc")

    def test_reconciliation_only_advances(self):
        obs = ChainNonceObservation("0xabc", 105)
        result = reconcile(100, obs)
        self.assertTrue(result.advanced)
        self.assertEqual(result.reconciled_next_nonce, 105)
        self.assertEqual(reconcile(110, obs).reconciled_next_nonce, 110)

    def test_quorum_requires_unique_consensus(self):
        observations = [
            ChainNonceObservation("0xabc", 10, provider="a"),
            ChainNonceObservation("0xabc", 10, provider="b"),
            ChainNonceObservation("0xabc", 9, provider="c"),
        ]
        result = quorum_pending_nonce(observations, quorum=2)
        self.assertEqual(result.pending_nonce, 10)
        self.assertIn("quorum", result.provider)

    def test_no_quorum_fails_closed(self):
        observations = [
            ChainNonceObservation("0xabc", 10, provider="a"),
            ChainNonceObservation("0xabc", 11, provider="b"),
        ]
        with self.assertRaises(PolygonNonceError):
            quorum_pending_nonce(observations, quorum=2)


if __name__ == "__main__":
    unittest.main()
