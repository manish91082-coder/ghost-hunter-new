import unittest

from phantomx.execution import ExecutionState
from phantomx.governor import GovernorPolicy
from phantomx.live_canonical_governor import (
    CanonicalGovernorPipelineError,
    discover_prepare_preflight_and_canonical_govern_best_opportunity,
)

from tests.phase19.test_live_opportunity_pipeline import A, B, LiveOpportunityPipelineTests


class CanonicalGovernorPipelineTests(LiveOpportunityPipelineTests):
    def _policy(self, assembly):
        return GovernorPolicy(
            expected_chain_id=137,
            live_execution_enabled=True,
            max_block_drift=2,
            max_gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
            max_gas_usd="0.10",
            max_relay_usd="0.05",
            minimum_net_profit_usd="0.20",
            approved_executors=(assembly.intent.executor,),
            approved_senders=(assembly.intent.sender,),
            allowed_loan_assets=(assembly.intent.loan_asset,),
            allowed_route_hashes=(assembly.intent.route_hash,),
        )

    def _complete(self, **changes):
        params = dict(
            rpc=self.rpc,
            quickswap=self.quickswap,
            uniswap=self.uniswap,
            token_pairs=((A, B),),
            loan_amounts=(1000,),
            uniswap_fee=500,
            build_proof_for=self._proof,
            **self.addresses,
            nonce=7,
            deadline=2000,
            amount_out_min_first=1090,
            amount_out_min_second=1110,
            minimum_surplus=1,
            gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
            now=1500,
            policy_factory=self._policy,
            executor_authority=self._authority(),
            lifecycle_state=ExecutionState.VERIFIED,
            nonce_reserved=True,
            replay_consumed=False,
            current_block_number=0x1234,
        )
        params.update(changes)
        return discover_prepare_preflight_and_canonical_govern_best_opportunity(**params)

    def test_canonical_governor_approves_exact_preflight_artifact(self):
        discovery, economics, assembly, preflight, decision = self._complete()
        self.assertEqual(len(discovery.evaluated), 2)
        self.assertTrue(preflight.passed)
        self.assertTrue(decision.approved)
        self.assertEqual(decision.intent_hash, assembly.intent_hash)
        self.assertEqual(decision.executor_authority_hash, self._authority().evidence_hash)

    def test_canonical_governor_blocks_unverified_lifecycle(self):
        result = self._complete(lifecycle_state=ExecutionState.BUILT)
        self.assertFalse(result[-1].approved)
        self.assertIn("VERIFIED", result[-1].reason)

    def test_canonical_governor_blocks_missing_nonce_reservation(self):
        result = self._complete(nonce_reserved=False)
        self.assertFalse(result[-1].approved)
        self.assertIn("nonce reservation", result[-1].reason)

    def test_canonical_governor_blocks_replayed_intent(self):
        result = self._complete(replay_consumed=True)
        self.assertFalse(result[-1].approved)
        self.assertIn("replay", result[-1].reason)

    def test_canonical_governor_blocks_block_drift(self):
        result = self._complete(current_block_number=0x1237)
        self.assertFalse(result[-1].approved)
        self.assertIn("block-drift", result[-1].reason)

    def test_canonical_governor_requires_authoritative_policy_factory(self):
        with self.assertRaises(CanonicalGovernorPipelineError):
            self._complete(policy_factory=lambda assembly: object())


if __name__ == "__main__":
    unittest.main()
