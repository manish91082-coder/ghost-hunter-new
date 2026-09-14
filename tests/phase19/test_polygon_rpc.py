import unittest

from phantomx.polygon_rpc import PolygonRPCError, RPCProvider, pending_nonce_observation, quorum_pending_nonce_from_providers, verify_chain


class PolygonRPCTests(unittest.TestCase):
    def provider(self, name, chain="0x89", nonce="0x2a"):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": chain}
            if method == "eth_getTransactionCount":
                self.assertEqual(params[1], "pending")
                return {"result": nonce}
            raise AssertionError(method)
        return RPCProvider(name, transport)

    def test_chain_identity_is_verified(self):
        self.assertEqual(verify_chain(self.provider("a")), 137)

    def test_wrong_chain_fails_closed(self):
        with self.assertRaises(PolygonRPCError):
            verify_chain(self.provider("a", chain="0x1"))

    def test_pending_nonce_requires_chain_verification(self):
        obs = pending_nonce_observation(self.provider("a"), "0xABC")
        self.assertEqual(obs.pending_nonce, 42)
        self.assertEqual(obs.provider, "a")

    def test_provider_error_fails_closed(self):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            return {"error": {"code": -32000}}
        with self.assertRaises(PolygonRPCError):
            pending_nonce_observation(RPCProvider("bad", transport), "0xabc")

    def test_quorum_requires_distinct_provider_consensus(self):
        result = quorum_pending_nonce_from_providers([self.provider("a", nonce="0x2a"), self.provider("b", nonce="0x2a"), self.provider("c", nonce="0x29")], "0xabc", quorum=2)
        self.assertEqual(result.pending_nonce, 42)
        self.assertIn("quorum", result.provider)

    def test_quorum_failure_is_fail_closed(self):
        with self.assertRaises(PolygonRPCError):
            quorum_pending_nonce_from_providers([self.provider("a", nonce="0x2a"), self.provider("b", nonce="0x2b")], "0xabc", quorum=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
