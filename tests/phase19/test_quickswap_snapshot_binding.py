import unittest

from phantomx.quickswap_v2 import BlockSnapshot, QuickSwapV2ExactQuoter

ROUTER = "0x" + "11" * 20
TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20


def encode_uint_array(values):
    raw = bytearray()
    raw.extend((32).to_bytes(32, "big"))
    raw.extend(len(values).to_bytes(32, "big"))
    for value in values:
        raw.extend(value.to_bytes(32, "big"))
    return "0x" + bytes(raw).hex()


class FakeRpc:
    def __init__(self):
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_call":
            return encode_uint_array([10**18, 997 * 10**15])
        raise AssertionError(method)


class QuickSwapSnapshotBindingTests(unittest.TestCase):
    def test_snapshot_binds_router_block_timestamp_amounts_and_hash(self):
        rpc = FakeRpc()
        snapshot = QuickSwapV2ExactQuoter(rpc, ROUTER).quote_snapshot(
            10**18,
            [TOKEN_A, TOKEN_B],
            BlockSnapshot(137, 0x1234, 1_757_000_000),
            gas_estimate=180_000,
        )
        self.assertEqual(snapshot.chain_id, 137)
        self.assertEqual(snapshot.block_number, 0x1234)
        self.assertEqual(snapshot.observed_at_unix, 1_757_000_000)
        self.assertEqual(snapshot.pool_or_router, ROUTER)
        self.assertEqual(snapshot.amount_in, 10**18)
        self.assertEqual(snapshot.amount_out, 997 * 10**15)
        self.assertEqual(snapshot.gas_estimate, 180_000)
        self.assertEqual(snapshot.compute_hash(), snapshot.quote_hash)


if __name__ == "__main__":
    unittest.main()
