import unittest

from phantomx.market_block import MarketBlockError, MarketBlockSnapshot, acquire_market_block


class FakeRpc:
    def __init__(self, chain="0x89", block="0x1234", timestamp="0x1000"):
        self.chain, self.block, self.timestamp = chain, block, timestamp
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId": return self.chain
        if method == "eth_blockNumber": return self.block
        if method == "eth_getBlockByNumber": return {"timestamp": self.timestamp}
        raise AssertionError(method)


class MarketBlockTests(unittest.TestCase):
    def test_acquires_one_canonical_block_and_timestamp(self):
        rpc = FakeRpc()
        block = acquire_market_block(rpc)
        self.assertEqual(block, MarketBlockSnapshot(137, 0x1234, 0x1000))
        self.assertEqual(rpc.calls, [
            ("eth_chainId", []),
            ("eth_blockNumber", []),
            ("eth_getBlockByNumber", ["0x1234", False]),
        ])

    def test_wrong_chain_fails_closed(self):
        with self.assertRaises(MarketBlockError):
            acquire_market_block(FakeRpc(chain="0x1"))

    def test_malformed_block_fails_closed(self):
        class BadRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_getBlockByNumber": return None
                return super().call(method, params)
        with self.assertRaises(MarketBlockError):
            acquire_market_block(BadRpc())

    def test_malformed_timestamp_fails_closed(self):
        with self.assertRaises(MarketBlockError):
            acquire_market_block(FakeRpc(timestamp="not_hex"))

    def test_snapshot_is_immutable_and_validated(self):
        block = MarketBlockSnapshot(137, 100, 200)
        self.assertEqual(block.block_number, 100)
        with self.assertRaises(MarketBlockError):
            MarketBlockSnapshot(1, 100, 200)
        with self.assertRaises(MarketBlockError):
            MarketBlockSnapshot(137, 100, 0)


if __name__ == "__main__":
    unittest.main()
