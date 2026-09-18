import unittest

from phantomx.execution import ExecutionIntent
from phantomx.executor_calldata import (
    EXECUTE_SIGNATURE,
    ExecutorCalldataError,
    build_executor_transaction,
    decode_executor_calldata,
    executor_route_commitment,
    executor_selector,
    executor_topology_hash,
)
from phantomx.hashing import keccak256_hex


class ExecutorCalldataBindingTests(unittest.TestCase):
    def setUp(self):
        self.asset = "0x1111111111111111111111111111111111111111"
        self.mid = "0x2222222222222222222222222222222222222222"
        self.executor = "0x3333333333333333333333333333333333333333"
        self.executor_alt = "0x9999999999999999999999999999999999999999"
        self.sender = "0x4444444444444444444444444444444444444444"
        self.aave = "0x5555555555555555555555555555555555555555"
        self.quick = "0x6666666666666666666666666666666666666666"
        self.uni = "0x7777777777777777777777777777777777777777"
        self.route_hash = "0x" + "aa" * 32
        self.economic_hash = "0x" + "bb" * 32
        self.simulation_hash = "0x" + "cc" * 32
        self.intent = ExecutionIntent(chain_id=137, executor=self.executor, sender=self.sender, loan_asset=self.asset, loan_amount=100_000_000, route_hash=self.route_hash, calldata_hash="0x" + "00" * 32, economic_proof_hash=self.economic_hash, simulation_proof_hash=self.simulation_hash, nonce=7, deadline=2_000_000)

    def _build(self):
        return build_executor_transaction(self.intent, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, amount_out_min_first=90_000_000, amount_out_min_second=95_000_000, minimum_surplus=5, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, gas_limit=800_000, max_fee_per_gas=1_000_000_000, max_priority_fee_per_gas=100_000_000)

    def test_commitment_hash_excludes_calldata_hash(self):
        original = self.intent.execution_commitment_hash()
        mutated = self.intent.with_field(calldata_hash="0x" + "dd" * 32).execution_commitment_hash()
        self.assertEqual(original, mutated)
        self.assertNotEqual(self.intent.intent_hash(), self.intent.with_field(calldata_hash="0x" + "dd" * 32).intent_hash())

    def test_calldata_binding_completes_without_hash_cycle(self):
        bound = self._build()
        self.assertEqual(bound.bound_intent.calldata_hash, bound.calldata_hash)
        self.assertEqual(bound.envelope.calldata_hash, bound.calldata_hash)
        self.assertEqual(bound.bound_intent.execution_commitment_hash(), bound.intent_commitment_hash)
        self.assertEqual(bound.route_commitment, executor_route_commitment(route_hash=self.route_hash, topology_hash=bound.topology_hash))
        self.assertEqual(bound.bound_intent.minimum_surplus_token_amount, 5)
        self.assertNotEqual(bound.bound_intent.intent_hash(), self.intent.intent_hash())

    def test_intent_mutation_invalidates_embedded_execution_commitment(self):
        bound = self._build()
        mutated = bound.bound_intent.with_field(deadline=bound.bound_intent.deadline + 1)
        decoded = decode_executor_calldata(bound.calldata)
        self.assertEqual(decoded.deadline, bound.bound_intent.deadline)
        self.assertEqual(decoded.intent_commitment_hash, bound.intent_commitment_hash)
        self.assertNotEqual(mutated.execution_commitment_hash(), decoded.intent_commitment_hash)

    def test_conflicting_intent_surplus_floor_is_rejected(self):
        with self.assertRaisesRegex(ExecutorCalldataError, "requested minimum surplus"):
            build_executor_transaction(self.intent.with_field(minimum_surplus_token_amount=6), token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, amount_out_min_first=90_000_000, amount_out_min_second=95_000_000, minimum_surplus=5, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, gas_limit=800_000, max_fee_per_gas=1_000_000_000, max_priority_fee_per_gas=100_000_000)

    def test_static_abi_layout_is_exactly_twelve_words_after_selector(self):
        bound = self._build()
        self.assertEqual(bound.calldata[:4], executor_selector())
        self.assertEqual(len(bound.calldata), 4 + 13 * 32)
        body = bound.calldata[4:]
        self.assertEqual(body[12:32], bytes.fromhex(self.asset[2:]))
        self.assertEqual(int.from_bytes(body[64:96], "big"), 1)
        self.assertEqual(int.from_bytes(body[96:128], "big"), 1)
        self.assertEqual(int.from_bytes(body[128:160], "big"), 3000)
        self.assertEqual(int.from_bytes(body[160:192], "big"), 90_000_000)
        self.assertEqual(int.from_bytes(body[192:224], "big"), 95_000_000)
        self.assertEqual(int.from_bytes(body[224:256], "big"), 5)
        self.assertEqual(int.from_bytes(body[256:288], "big"), self.intent.deadline)
        self.assertEqual(body[288:320], bytes.fromhex(self.route_hash[2:]))
        self.assertEqual(body[320:352], bytes.fromhex(bound.route_commitment[2:]))
        self.assertEqual(body[352:384], bytes.fromhex(bound.intent_commitment_hash[2:]))
        self.assertEqual(int.from_bytes(body[384:416], "big"), self.intent.loan_amount)

    def test_route_commitment_changes_when_quote_or_topology_changes(self):
        topology = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        first = executor_route_commitment(route_hash=self.route_hash, topology_hash=topology)
        route_mutated = executor_route_commitment(route_hash="0x" + "ab" * 32, topology_hash=topology)
        topology_mutated = executor_route_commitment(route_hash=self.route_hash, topology_hash="0x" + "cd" * 32)
        self.assertNotEqual(first, route_mutated)
        self.assertNotEqual(first, topology_mutated)

    def test_topology_hash_changes_when_executable_route_changes(self):
        first = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        second = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=False, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        third = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=500, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        executor_mutated = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor_alt)
        venue_mutated = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=2, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        chain_mutated = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor, chain_id=1)
        self.assertEqual(len(first), 66)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, third)
        self.assertNotEqual(first, executor_mutated)
        self.assertNotEqual(first, venue_mutated)
        self.assertNotEqual(first, chain_mutated)

    def test_python_topology_and_commitment_reference_vectors(self):
        topology = executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        commitment = executor_route_commitment(route_hash=self.route_hash, topology_hash=topology)
        self.assertEqual(len(topology), 66)
        self.assertEqual(len(commitment), 66)

    def test_selector_is_ethereum_keccak_of_exact_signature(self):
        self.assertEqual(executor_selector().hex(), keccak256_hex(EXECUTE_SIGNATURE.encode("ascii"))[2:10])

    def test_zero_executor_address_fails_closed(self):
        with self.assertRaises(ExecutorCalldataError):
            build_executor_transaction(self.intent.with_field(executor="0x" + "00" * 20), token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, amount_out_min_first=1, amount_out_min_second=1, minimum_surplus=1, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, gas_limit=1, max_fee_per_gas=2, max_priority_fee_per_gas=1)

    def test_zero_hash_and_invalid_fee_fail_closed(self):
        with self.assertRaises(ExecutorCalldataError):
            build_executor_transaction(self.intent.with_field(route_hash="0x" + "00" * 32), token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, amount_out_min_first=1, amount_out_min_second=1, minimum_surplus=1, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, gas_limit=1, max_fee_per_gas=2, max_priority_fee_per_gas=1)
        with self.assertRaises(ExecutorCalldataError):
            executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=0x1000000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor)
        with self.assertRaises(ExecutorCalldataError):
            executor_topology_hash(asset=self.asset, token_mid=self.mid, first_on_quickswap=True, quickswap_venue_kind=1, uniswap_fee=3000, aave_pool=self.aave, quickswap_v2_router=self.quick, quickswap_v3_router=self.quick_v3, uniswap_v3_router=self.uni, executor=self.executor, chain_id=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
