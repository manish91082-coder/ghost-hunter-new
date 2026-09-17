import unittest
from decimal import Decimal

from phantomx.governor import GovernorError, GovernorDecision, GovernorPolicy, govern_execution
from phantomx.execution import ExecutionState
from phantomx.live_opportunity_pipeline import LiveOpportunityPipelineError, discover_prepare_preflight_and_govern_best_opportunity

from tests.phase19.test_live_opportunity_pipeline import A, B, LiveOpportunityPipelineTests


class ExecutionGovernorTests(LiveOpportunityPipelineTests):
    def _govern(self, **changes):
        params = {
            "live_execution_enabled": True,
            "max_block_drift": 0,
            "max_gas_limit": 500000,
            "max_fee_per_gas": 100,
            "max_priority_fee_per_gas": 10,
            "max_gas_usd": Decimal("1.00"),
            "max_relay_usd": Decimal("1.00"),
            "minimum_net_profit_usd": Decimal("0.20"),
            "approved_executors": (self.addresses["executor"],),
            "approved_senders": (self.addresses["sender"],),
            "allowed_loan_assets": (A,),
        }
        params.update(changes)
        return GovernorPolicy(**params)

    def _allowed_route(self, discovery):
        return (discovery.evaluated[0].simulation.route_hash, discovery.evaluated[1].simulation.route_hash)

    def test_complete_live_pipeline_reaches_canonical_governor(self):
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
            governor_policy=self._govern(allowed_route_hashes=()),
            executor_authority=self._authority(),
        )
        self.assertEqual(len(discovery.evaluated), 2)
        self.assertEqual(economics.best.candidate.loan_amount, 1000)
        self.assertTrue(preflight.passed)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.reason, "live governor bridge requires canonical governance evidence")

    def test_governor_requires_nonce_reservation_and_allowlists(self):
        with self.assertRaises(GovernorError):
            govern_execution(
                policy=self._govern(allowed_route_hashes=("0x" + "44" * 32,)),
                preflight=None,
                intent=None,
                envelope=None,
                economic_proof=None,
                executor_authority=None,
                lifecycle_state=ExecutionState.VERIFIED,
                nonce_reserved=False,
                replay_consumed=False,
                current_block_number=0,
                now=0,
            )

    def test_pipeline_kill_switch_fails_closed(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            self._complete(live_execution_enabled=False)

    def _complete(self, **policy_changes):
        discovery, *_ = self._prepare_bundle()
        policy = self._govern(allowed_route_hashes=self._allowed_route(discovery), **policy_changes)
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
            deadline=2000,
            amount_out_min_first=1090,
            amount_out_min_second=1110,
            minimum_surplus=1,
            gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
            now=1500,
            governor_policy=policy,
            executor_authority=self._authority(),
        )

    def _prepare_bundle(self):
        return self._prepare()


if __name__ == "__main__":
    unittest.main()
