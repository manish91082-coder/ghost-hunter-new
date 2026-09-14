import unittest

from phantomx.polygon_rpc import PolygonRPCError, RPCProvider, pending_nonce_observation, quorum_pending_nonce_from_providers, read_contract_code, read_contract_owner, verify_chain


class PolygonRPCTests(unittest.TestCase):
    def provider(self, name, chain="0x89", nonce="0x2a"):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": chain}
            if method == "eth_getTransactionCount":
                self.assertEqual(params[1], "pending")
                return {"result": nonce}
            if method == "eth_blockNumber":
                return {"result": "0x100"}
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

    def test_executor_owner_is_read_at_explicit_block(self):
        executor = "0x" + "aa" * 20
        owner = "0x" + "bb" * 20
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": "0x100"}
            if method == "eth_call":
                self.assertEqual(params[0]["to"], executor)
                self.assertEqual(params[0]["data"], "0x8da5cb5b")
                self.assertEqual(params[1], "0x100")
                return {"result": "0x" + "00" * 12 + owner[2:]}
            raise AssertionError(method)
        self.assertEqual(read_contract_owner(RPCProvider("owner", transport), executor), owner)

    def test_executor_owner_malformed_result_fails_closed(self):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": "0x100"}
            if method == "eth_call":
                return {"result": "0x1234"}
            raise AssertionError(method)
        with self.assertRaises(PolygonRPCError):
            read_contract_owner(RPCProvider("bad-owner", transport), "0x" + "aa" * 20)

    def test_executor_runtime_code_is_nonempty_and_block_bound(self):
        executor = "0x" + "aa" * 20
        code = "0x6001600055"
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": "0x101"}
            if method == "eth_getCode":
                self.assertEqual(params[0], executor)
                self.assertEqual(params[1], "0x101")
                return {"result": code}
            raise AssertionError(method)
        block, observed = read_contract_code(RPCProvider("code", transport), executor)
        self.assertEqual(block, 257)
        self.assertEqual(observed, code)

    def test_empty_runtime_code_is_rejected(self):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": "0x101"}
            if method == "eth_getCode":
                return {"result": "0x"}
            raise AssertionError(method)
        with self.assertRaises(PolygonRPCError):
            read_contract_code(RPCProvider("empty-code", transport), "0x" + "aa" * 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)