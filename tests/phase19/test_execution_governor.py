import unittest

from phantomx.execution_governor import (
    ExecutionGovernorError,
    GovernorPolicy,
    govern_execution,
)
from phantomx.executor_authority import ExecutorAuthorityEvidence
from phantomx.live_opportunity_pipeline import (
    LiveOpportunityPipelineError,
    discover_prepare_preflight_and_govern_best_opportunity,
)

from tests.phase19.test_live_opportunity_pipeline import A, B, LiveOpportunityPipelineTests


class ExecutionGovernorTests(LiveOpportunityPipelineTests):
    def _govern(self, **changes):
        params = {
            "max_loan_amount": 1000,
            "max_gas_limit": 500000,
            "max_fee_per_gas": 100,
            "max_priority_fee_per_gas": 10,
            "max_deadline_seconds": 600,
            "minimum_net_profit_usd": "0.20",
            "expected_executor": self.addresses["executor"],
            "expected_sender": self.addresses["sender"],
        }
        params.update(changes)
        return GovernorPolicy(**params)

    def test_complete_live_pipeline_reaches_governor(self):
        discovery, economics, assembly, preflight, decision = discover_prepare_preflight_and_govern_best_opportunity(
            self.rpc,
            self.quickswap,
            self.uniswap,
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
            governor_policy=self._govern(),
            executor_authority=self._authority(),
        )
        self.assertEqual(len(discovery.evaluated), 2)
        self.assertEqual(economics.best.candidate.loan_amount, 1000)
        self.assertTrue(preflight.passed)
        self.assertTrue(decision.approved)
        self.assertEqual(decision.intent_hash, assembly.intent_hash)
        self.assertEqual(decision.policy_hash, self._govern().policy_hash())

    def test_governor_kill_switch_fails_closed(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(governor_policy=self._govern(enabled=False))

    def test_governor_rejects_loan_cap(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(governor_policy=self._govern(max_loan_amount=999))

    def test_governor_rejects_gas_cap(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(governor_policy=self._govern(max_gas_limit=499999))

    def test_governor_rejects_fee_cap(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(governor_policy=self._govern(max_fee_per_gas=99))

    def test_governor_rejects_sender_identity(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(governor_policy=self._govern(expected_sender="0x" + "06" * 20))

    def test_governor_rejects_executor_identity(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(governor_policy=self._govern(expected_executor="0x" + "06" * 20))

    def test_governor_rejects_deadline_too_far_ahead(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(now=1500, deadline=2201, governor_policy=self._govern(max_deadline_seconds=700))

    def test_governor_requires_preflight_result(self):
        with self.assertRaises(ExecutionGovernorError):
            govern_execution(preflight=None, assembly=None, policy=self._govern(), now=1500)

    def _complete(self, *, governor_policy, now=1500, deadline=2000):
        return discover_prepare_preflight_and_govern_best_opportunity(
            self.rpc,
            self.quickswap,
            self.uniswap,
            token_pairs=((A, B),),
            loan_amounts=(1000,),
            uniswap_fee=500,
            build_proof_for=self._proof,
            **self.addresses,
            nonce=7,
            deadline=deadline,
            amount_out_min_first=1090,
            amount_out_min_second=1110,
            minimum_surplus=1,
            gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
            now=now,
            governor_policy=governor_policy,
            executor_authority=self._authority(),
        )


if __name__ == "__main__":
    unittest.main()
