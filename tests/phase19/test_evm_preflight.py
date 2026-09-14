import unittest
from dataclasses import replace
from decimal import Decimal

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.evm_preflight import EVMPreflightError, preflight_execution, simulation_hash
from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope
from phantomx.hashing import keccak256_hex
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg

TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20
ROUTER_A = "0x" + "cc" * 20
ROUTER_B = "0x" + "dd" * 20
EXECUTOR = "0x" + "ee" * 20
SENDER = "0x" + "ff" * 20
ROUTE = "0x" + "11" * 32
VALUATION = "0x" + "44" * 32


class EVMPreflightTests(unittest.TestCase):
    def setUp(self):
        self.block = 5000
        self.now = 1_700_000_000
        self.calldata = bytes.fromhex("12345678" + "00" * 32)
        leg_one = QuoteSnapshot(
            schema_version=1,
            chain_id=137,
            block_number=self.block,
            observed_at_unix=self.now,
            dex="QuickSwapV2",
            pool_or_router=ROUTER_A,
            token_in=TOKEN_A,
            token_out=TOKEN_B,
            amount_in=100,
            amount_out=110,
            fee_raw=3,
            gas_estimate=100_000,
            quote_hash="0x" + "00" * 32,
        )
        leg_one = replace(leg_one, quote_hash=leg_one.compute_hash())
        leg_two = QuoteSnapshot(
            schema_version=1,
            chain_id=137,
            block_number=self.block,
            observed_at_unix=self.now,
            dex="UniswapV3",
            pool_or_router=ROUTER_B,
            token_in=TOKEN_B,
            token_out=TOKEN_A,
            amount_in=110,
            amount_out=101,
            fee_raw=3000,
            gas_estimate=120_000,
            quote_hash="0x" + "00" * 32,
        )
        leg_two = replace(leg_two, quote_hash=leg_two.compute_hash())
        self.simulation = simulate_two_leg(leg_one, leg_two)
        self.proof = build_economic_proof(
            route_hash=self.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in self.simulation.legs),
            valuation_hash=VALUATION,
            final_settlement_usd="101.00",
            loan_principal_usd="100.00",
            costs=CostBreakdown(
                flash_loan_fee="0.05",
                dex_fees="0.05",
                price_impact="0.05",
                gas="0.05",
                relay="0.02",
                other="0.01",
            ),
            max_gas_usd="0.05",
            max_relay_usd="0.02",
        )
        self.intent = ExecutionIntent(
            chain_id=137,
            executor=EXECUTOR,
            sender=SENDER,
            loan_asset=TOKEN_A,
            loan_amount=100,
            route_hash=self.simulation.route_hash,
            calldata_hash=keccak256_hex(self.calldata),
            economic_proof_hash=self.proof.proof_hash,
            simulation_proof_hash=simulation_hash(self.simulation),
            nonce=7,
            deadline=self.now + 60,
            minimum_net_profit_usd="0.20",
        )
        self.envelope = TransactionEnvelope(
            chain_id=137,
            sender=SENDER,
            executor=EXECUTOR,
            nonce=7,
            calldata=self.calldata,
            gas_limit=300_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
        )
        self.authorization = Authorization(
            intent_hash=self.intent.intent_hash(),
            calldata_hash=self.intent.calldata_hash,
            economic_proof_hash=self.proof.proof_hash,
            simulation_proof_hash=simulation_hash(self.simulation),
            chain_id=137,
            executor=EXECUTOR,
            sender=SENDER,
            nonce=7,
            deadline=self.now + 60,
            gas_limit=300_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
        )

    def run_preflight(self, **overrides):
        values = {
            "intent": self.intent,
            "authorization": self.authorization,
            "envelope": self.envelope,
            "simulation": self.simulation,
            "economic_proof": self.proof,
            "now": self.now,
        }
        values.update(overrides)
        return preflight_execution(**values)

    def test_exact_proven_execution_passes(self):
        result = self.run_preflight()
        self.assertTrue(result.passed)
        self.assertEqual(result.chain_id, 137)
        self.assertEqual(result.block_number, self.block)
        self.assertEqual(result.intent_hash, self.intent.intent_hash())
        self.assertEqual(result.calldata_hash, self.envelope.calldata_hash)

    def test_calldata_mutation_is_blocked(self):
        mutated = replace(self.envelope, calldata=b"mutated")
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(envelope=mutated)

    def test_route_mutation_is_blocked(self):
        mutated = replace(self.intent, route_hash="0x" + "55" * 32)
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(intent=mutated)

    def test_loan_asset_or_amount_mutation_is_blocked(self):
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(intent=replace(self.intent, loan_asset=TOKEN_B))
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(intent=replace(self.intent, loan_amount=101))

    def test_simulation_proof_mutation_is_blocked(self):
        mutated = replace(self.intent, simulation_proof_hash="0x" + "66" * 32)
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(intent=mutated)

    def test_economic_proof_mutation_is_blocked(self):
        mutated = build_economic_proof(
            route_hash=self.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in self.simulation.legs),
            valuation_hash="0x" + "77" * 32,
            final_settlement_usd="101.00",
            loan_principal_usd="100.00",
            costs=CostBreakdown(
                flash_loan_fee="0.05", dex_fees="0.05", price_impact="0.05",
                gas="0.05", relay="0.02", other="0.01",
            ),
            max_gas_usd="0.05", max_relay_usd="0.02",
        )
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(economic_proof=mutated)

    def test_expired_authorization_is_blocked(self):
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(now=self.intent.deadline + 1)

    def test_chain_mutation_is_blocked(self):
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(expected_chain_id=1)
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(envelope=replace(self.envelope, chain_id=1))

    def test_gas_fields_mutation_is_blocked(self):
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(envelope=replace(self.envelope, gas_limit=300_001))
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(envelope=replace(self.envelope, max_fee_per_gas=29))

    def test_quote_binding_must_match_route(self):
        altered = build_economic_proof(
            route_hash=self.simulation.route_hash,
            quote_hashes=("0x" + "88" * 32, self.simulation.legs[1].quote_hash),
            valuation_hash=VALUATION,
            final_settlement_usd="101.00",
            loan_principal_usd="100.00",
            costs=self.proof.costs,
            max_gas_usd=self.proof.max_gas_usd,
            max_relay_usd=self.proof.max_relay_usd,
        )
        with self.assertRaises(EVMPreflightError):
            self.run_preflight(economic_proof=altered)

    def test_simulation_hash_is_deterministic_and_changes_with_route(self):
        self.assertEqual(simulation_hash(self.simulation), simulation_hash(self.simulation))
        altered = replace(self.simulation, final_amount=102)
        self.assertNotEqual(simulation_hash(self.simulation), simulation_hash(altered))


if __name__ == "__main__":
    unittest.main(verbosity=2)
