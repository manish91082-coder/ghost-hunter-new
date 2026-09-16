import unittest
from decimal import Decimal

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.opportunity_discovery import OpportunityCandidate
from phantomx.opportunity_pipeline import OpportunityPipelineError, prepare_best_opportunity_execution
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg


def snapshot(dex, token_in, token_out, amount_in, amount_out, fee, router):
    quote = ExactQuote(dex, token_in, token_out, amount_in, amount_out, 123, fee)
    return QuoteSnapshot.from_exact_quote(
        quote, chain_id=137, observed_at_unix=1000, pool_or_router=router, gas_estimate=100000
    )


class OpportunityPipelineTests(unittest.TestCase):
    def setUp(self):
        self.a = "0x" + "aa" * 20
        self.b = "0x" + "bb" * 20
        q1 = snapshot("quickswap_v2", self.a, self.b, 1000, 1100, 30, "0x" + "11" * 20)
        q2 = snapshot("uniswap_v3", self.b, self.a, 1100, 1120, 500, "0x" + "22" * 20)
        simulation = simulate_two_leg(q1, q2)
        self.candidate_1 = OpportunityCandidate(self.a, self.b, "quickswap_v2->uniswap_v3", 1000, simulation)
        self.candidate_2 = OpportunityCandidate(self.a, self.b, "quickswap_v2->uniswap_v3", 2000, simulation)
        self.addresses = {
            "executor": "0x" + "01" * 20,
            "sender": "0x" + "02" * 20,
            "aave_pool": "0x" + "03" * 20,
            "quickswap_router": "0x" + "04" * 20,
            "uniswap_v3_router": "0x" + "05" * 20,
        }

    def _proof(self, candidate):
        settlement = Decimal("100.90") if candidate.loan_amount == 1000 else Decimal("101.00")
        return build_economic_proof(
            route_hash=candidate.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in candidate.simulation.legs),
            valuation_hash="0x" + "44" * 32,
            final_settlement_usd=settlement,
            loan_principal_usd=Decimal("100.00"),
            costs=CostBreakdown(flash_loan_fee=Decimal("0.10")),
            max_gas_usd=Decimal("0.10"),
            max_relay_usd=Decimal("0.05"),
        )

    def _prepare(self, candidates, builder=None):
        return prepare_best_opportunity_execution(
            candidates,
            builder or self._proof,
            **self.addresses,
            nonce=7,
            deadline=2000,
            amount_out_min_first=1090,
            amount_out_min_second=1110,
            minimum_surplus=1,
            gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
        )

    def test_complete_frontier_selection_winner_reaches_assembly(self):
        economics, assembly = self._prepare((self.candidate_1, self.candidate_2))
        self.assertEqual(len(economics.evaluated), 2)
        self.assertEqual(economics.best.candidate.loan_amount, 2000)
        self.assertEqual(assembly.intent.loan_amount, 2000)
        self.assertEqual(assembly.intent.route_hash, economics.best.proof.route_hash)

    def test_evaluator_failure_does_not_create_execution_artifact(self):
        def fail(candidate):
            raise ValueError("valuation unavailable")

        with self.assertRaises(OpportunityPipelineError):
            self._prepare((self.candidate_1,), fail)


if __name__ == "__main__":
    unittest.main()
