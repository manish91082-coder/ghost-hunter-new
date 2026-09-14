import unittest
from dataclasses import replace
from decimal import Decimal

from phantomx.economic_proof import EconomicProof, build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.evm_preflight import preflight_execution, simulation_hash
from phantomx.execution import Authorization, ExecutionIntent, ExecutionState
from phantomx.executor_authority import ExecutorAuthorityEvidence
from phantomx.executor_calldata import build_executor_transaction
from phantomx.governor import GovernorError, GovernorPolicy, govern_execution
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg

TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20
ROUTER_A = "0x" + "cc" * 20
ROUTER_B = "0x" + "dd" * 20
AAVE_POOL = "0x" + "11" * 20
EXECUTOR = "0x" + "ee" * 20
SENDER = "0x" + "ff" * 20
VALUATION = "0x" + "44" * 32
RUNTIME_CODE_HASH = "0x" + "55" * 32


class GovernorTests(unittest.TestCase):
    def setUp(self):
        self.block = 5000
        self.now = 1_700_000_000
        leg_one = QuoteSnapshot.from_exact_quote(
            ExactQuote("QuickSwapV2", TOKEN_A, TOKEN_B, 100, 110, self.block, 3),
            chain_id=137,
            observed_at_unix=self.now,
            pool_or_router=ROUTER_A,
            gas_estimate=100_000,
        )
        leg_two = QuoteSnapshot.from_exact_quote(
            ExactQuote("UniswapV3", TOKEN_B, TOKEN_A, 110, 101, self.block, 3000),
            chain_id=137,
            observed_at_unix=self.now,
            pool_or_router=ROUTER_B,
            gas_estimate=120_000,
        )
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
        seed_intent = ExecutionIntent(
            chain_id=137,
            executor=EXECUTOR,
            sender=SENDER,
            loan_asset=TOKEN_A,
            loan_amount=100,
            route_hash=self.simulation.route_hash,
            calldata_hash="0x" + "00" * 32,
            economic_proof_hash=self.proof.proof_hash,
            simulation_proof_hash=simulation_hash(self.simulation),
            nonce=7,
            deadline=self.now + 60,
            minimum_net_profit_usd="0.20",
        )
        bound = build_executor_transaction(
            seed_intent,
            token_mid=TOKEN_B,
            first_on_quickswap=True,
            uniswap_fee=3000,
            amount_out_min_first=100,
            amount_out_min_second=95,
            minimum_surplus=1,
            aave_pool=AAVE_POOL,
            quickswap_router=ROUTER_A,
            uniswap_v3_router=ROUTER_B,
            gas_limit=300_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
        )
        self.intent = bound.bound_intent
        self.envelope = bound.envelope
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
        self.authority = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=self.block + 1,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        self.preflight = preflight_execution(
            intent=self.intent,
            authorization=self.authorization,
            envelope=self.envelope,
            simulation=self.simulation,
            economic_proof=self.proof,
            now=self.now,
            executor_authority=self.authority,
        )
        self.policy = GovernorPolicy(
            live_execution_enabled=True,
            approved_executors=(EXECUTOR,),
            approved_senders=(SENDER,),
            allowed_loan_assets=(TOKEN_A,),
            allowed_route_hashes=(self.simulation.route_hash,),
            max_block_drift=2,
            max_gas_limit=300_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
            max_gas_usd="0.05",
            max_relay_usd="0.02",
        )

    def run_governor(self, **overrides):
        values = {
            "policy": self.policy,
            "preflight": self.preflight,
            "intent": self.intent,
            "envelope": self.envelope,
            "economic_proof": self.proof,
            "executor_authority": self.authority,
            "lifecycle_state": ExecutionState.VERIFIED,
            "nonce_reserved": True,
            "replay_consumed": False,
            "current_block_number": self.block + 1,
            "now": self.now,
        }
        values.update(overrides)
        return govern_execution(**values)

    def test_exact_verified_execution_is_approved(self):
        decision = self.run_governor(ai_rank="0.99")
        self.assertTrue(decision.approved)
        self.assertEqual(decision.reason, "all governor policy gates passed")
        self.assertEqual(decision.ai_rank, "0.99")
        self.assertEqual(decision.executor_authority_hash, self.authority.evidence_hash)
        self.assertEqual(self.preflight.authority_evidence_hash, self.authority.evidence_hash)
        self.assertEqual(len(decision.decision_hash), 66)

    def test_authority_mutation_is_blocked_and_decision_commits_to_evidence(self):
        mutated = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=TOKEN_B,
            observed_block=self.block + 1,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        blocked = self.run_governor(executor_authority=mutated)
        self.assertFalse(blocked.approved)
        self.assertIn("preflight authority evidence binding changed", blocked.reason)
        self.assertNotEqual(blocked.executor_authority_hash, self.authority.evidence_hash)

    def test_authority_observation_before_proven_block_is_blocked(self):
        stale = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=self.block - 1,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        blocked = self.run_governor(executor_authority=stale)
        self.assertFalse(blocked.approved)
        self.assertIn("preflight authority evidence binding changed", blocked.reason)

    def test_preflight_authority_binding_cannot_be_missing_or_mutated(self):
        missing = replace(self.preflight, authority_evidence_hash="")
        self.assertFalse(self.run_governor(preflight=missing).approved)
        mutated = replace(self.preflight, authority_evidence_hash="0x" + "66" * 32)
        self.assertFalse(self.run_governor(preflight=mutated).approved)

    def test_live_capital_lock_blocks_even_valid_preflight(self):
        decision = self.run_governor(policy=replace(self.policy, live_execution_enabled=False))
        self.assertFalse(decision.approved)
        self.assertIn("live execution is locked", decision.reason)

    def test_lifecycle_nonce_and_replay_gates_are_fail_closed(self):
        self.assertFalse(self.run_governor(lifecycle_state=ExecutionState.SIGNED).approved)
        self.assertFalse(self.run_governor(nonce_reserved=False).approved)
        self.assertFalse(self.run_governor(replay_consumed=True).approved)

    def test_block_drift_and_future_block_are_blocked(self):
        self.assertFalse(self.run_governor(current_block_number=self.block + 3).approved)
        self.assertFalse(self.run_governor(current_block_number=self.block - 1).approved)

    def test_deadline_and_chain_are_blocked(self):
        self.assertFalse(self.run_governor(now=self.intent.deadline + 1).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, expected_chain_id=1)).approved)
        self.assertFalse(self.run_governor(envelope=replace(self.envelope, chain_id=1)).approved)

    def test_gas_and_relay_ceiling_mutations_are_blocked(self):
        self.assertFalse(self.run_governor(policy=replace(self.policy, max_gas_limit=299_999)).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, max_fee_per_gas=99)).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, max_priority_fee_per_gas=29)).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, max_gas_usd="0.049")).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, max_relay_usd="0.019")).approved)

    def test_economic_floor_is_strict_and_ai_cannot_override_it(self):
        below_floor = EconomicProof(
            schema_version=1,
            route_hash=self.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in self.simulation.legs),
            valuation_hash=VALUATION,
            final_settlement_usd="100.25",
            loan_principal_usd="100.00",
            costs=CostBreakdown(other="0.06"),
            max_gas_usd="1.00",
            max_relay_usd="1.00",
            minimum_net_profit_usd="0.20",
        )
        self.assertFalse(below_floor.economically_valid)
        self.assertFalse(self.run_governor(economic_proof=below_floor, ai_rank="999999").approved)

    def test_allowlists_block_unknown_executor_sender_asset_and_route(self):
        self.assertFalse(self.run_governor(policy=replace(self.policy, approved_executors=(TOKEN_A,))).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, approved_senders=(TOKEN_A,))).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, allowed_loan_assets=(TOKEN_B,))).approved)
        self.assertFalse(self.run_governor(policy=replace(self.policy, allowed_route_hashes=("0x" + "77" * 32,))).approved)

    def test_preflight_identity_mutation_is_blocked(self):
        mutated = replace(self.preflight, calldata_hash="0x" + "55" * 32)
        self.assertFalse(self.run_governor(preflight=mutated).approved)
        mutated = replace(self.preflight, intent_hash="0x" + "66" * 32)
        self.assertFalse(self.run_governor(preflight=mutated).approved)

    def test_decision_hash_is_deterministic_and_ai_rank_is_audit_only(self):
        first = self.run_governor(ai_rank=Decimal("0.5"))
        second = self.run_governor(ai_rank=Decimal("0.5"))
        self.assertEqual(first.decision_hash, second.decision_hash)
        self.assertNotEqual(first.decision_hash, self.run_governor(ai_rank=Decimal("0.6")).decision_hash)
        self.assertTrue(self.run_governor(ai_rank="-999").approved)

    def test_policy_rejects_floor_below_canonical_invariant(self):
        with self.assertRaises(GovernorError):
            GovernorPolicy(minimum_net_profit_usd="0.199999")

    def test_policy_rejects_invalid_gas_ceiling(self):
        with self.assertRaises(GovernorError):
            GovernorPolicy(max_fee_per_gas=10, max_priority_fee_per_gas=11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
