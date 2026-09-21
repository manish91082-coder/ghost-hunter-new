import unittest

from phantomx.execution import TransactionEnvelope
from phantomx.gas_observation import GasObservationError, observe_exact_gas

class FakeRPC:
    def __init__(self, chain="0x89", block_number="0x7b"):
        self.calls = []
        self.chain = chain
        self.block_number = block_number

    def call(self, method, params=()):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return {"result": self.chain}
        if method == "eth_getBlockByNumber":
            return {"result": {"number": self.block_number, "baseFeePerGas": "0x3b9aca00"}}
        if method == "eth_estimateGas":
            return {"result": "0x186a0"}
        if method == "eth_maxPriorityFeePerGas":
            return {"result": "0x3b9aca"}
        raise AssertionError(f"unexpected RPC method: {method}")

def envelope():
    return TransactionEnvelope(
        chain_id=137, sender="0x"+"11"*20, executor="0x"+"22"*20,
        nonce=7, calldata=b"\x12\x34", gas_limit=1,
        max_fee_per_gas=1, max_priority_fee_per_gas=1,
    )

class GasObservationTests(unittest.TestCase):
    def test_exact_gas_uses_pinned_block_and_transaction_fields(self):
        rpc = FakeRPC()
        obs = observe_exact_gas(rpc, envelope(), block_number=123)
        self.assertEqual(obs.block_number, 123)
        self.assertGreater(obs.gas_estimate, 0)
        estimate = next(params for method, params in rpc.calls if method == "eth_estimateGas")
        self.assertEqual(estimate[1], "0x7b")
        tx = estimate[0]
        self.assertEqual(tx["from"], "0x" + "11"*20)
        self.assertEqual(tx["to"], "0x" + "22"*20)
        self.assertEqual(tx["data"], "0x1234")

    def test_gas_is_not_loan_percentage(self):
        rpc1 = FakeRPC(); rpc2 = FakeRPC()
        a = observe_exact_gas(rpc1, envelope(), block_number=123)
        b = observe_exact_gas(rpc2, TransactionEnvelope(**{**envelope().__dict__, "nonce": 9000000}), block_number=123)
        self.assertEqual(a.gas_estimate, b.gas_estimate)

    def test_wrong_chain_blocks(self):
        with self.assertRaises(GasObservationError):
            observe_exact_gas(FakeRPC(chain="0x1"), envelope(), block_number=123)

    def test_block_mismatch_blocks(self):
        with self.assertRaises(GasObservationError):
            observe_exact_gas(FakeRPC(block_number="0x7c"), envelope(), block_number=123)

    def test_gas_limit_contains_fixed_policy_headroom(self):
        obs = observe_exact_gas(FakeRPC(), envelope(), block_number=123, gas_safety_bps=2000)
        self.assertGreaterEqual(obs.gas_limit, obs.gas_estimate)
        self.assertEqual(obs.max_gas_cost_native, obs.gas_limit * obs.max_fee_per_gas)

if __name__ == "__main__":
    unittest.main(verbosity=2)
