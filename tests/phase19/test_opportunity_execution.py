import unittest
from decimal import Decimal

from phantomx.economic_proof import EconomicProof, build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.opportunity_discovery import OpportunityCandidate
from phantomx.opportunity_economics import OpportunityEconomicEvaluation
from phantomx.opportunity_execution import OpportunityExecutionError, assemble_proven_opportunity
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg


def snapshot(dex, token_in, token_out, amount_in, amount_out, fee, router):
    quote = ExactQuote(dex, token_in, token_out, amount_in, amount_out, 123, fee)
    return QuoteSnapshot.from_exact_quote(
        quote, chain_id=137, observed_at_unix=1000, pool_or_router=router, gas_estimate=100000
    )


class OpportunityExecutionTests(unittest.TestCase):
    def setUp(self):
        self.token_a = "0x" + "aa" * 20
        self.token_b = "0x" + "bb" * 20
        self.q1 = snapshot(
            "quickswap_v2", self.token_a, self.token_b, 1000, 1100, 30, "0x" + "11" * 20
        )
        self.q2 = snapshot(
            "uniswap_v3", self.token_b, self.token_a, 1100, 1120, 500, "0x" + "22" * 20
        )
        simulation = simulate_two_leg(self.q1, self.q2)
        candidate = OpportunityCandidate(
            token_a=self.token_a,
            token_b=self.token_b,
            venue_path="quickswap_v2->uniswap_v3",
            loan_amount=1000,
            simulation=simulation,
        )
        proof = build_economic_proof(
            route_hash=simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in simulation.legs),
            valuation_hash="0x" + "44" * 32,
            final_settlement_usd=Decimal("100.95"),
            loan_principal_usd=Decimal("100.00"),
            costs=CostBreakdown(
                flash_loan_fee=Decimal("0.10"),
                dex_fees=Decimal("0.20"),
                price_impact=Decimal("0.05"),
                gas=Decimal("0.10"),
                relay=Decimal("0.05"),
                other=Decimal("0.05"),
            ),
            max_gas_usd=Decimal("0.10"),
            max_relay_usd=Decimal("0.05"),
        )
        self.evaluation = OpportunityEconomicEvaluation(candidate=candidate, proof=proof)
        self.addresses = {
            "executor": "0x" + "01" * 20,
            "sender": "0x" + "02" * 20,
            "aave_pool": "0x" + "03" * 20,
            "quickswap_router": "0x" + "04" * 20,
            "uniswap_v3_router": "0x" + "05" * 20,
        }

    def _assemble(self, evaluation=None):
        return assemble_proven_opportunity(
            evaluation or self.evaluation,
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

    def test_profitable_discovery_binds_to_execution_assembly(self):
        assembly = self._assemble()
        self.assertEqual(assembly.simulation.route_hash, self.evaluation.proof.route_hash)
        self.assertEqual(assembly.intent.loan_amount, self.evaluation.candidate.loan_amount)
        self.assertEqual(assembly.intent.route_hash, self.evaluation.candidate.simulation.route_hash)
        self.assertEqual(assembly.envelope.nonce, 7)

    def test_below_floor_evaluation_is_rejected_before_assembly(self):
        bad_proof = EconomicProof(
            schema_version=1,
            route_hash=self.evaluation.candidate.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in self.evaluation.candidate.simulation.legs),
            valuation_hash="0x" + "55" * 32,
            final_settlement_usd=Decimal("100.74"),
            loan_principal_usd=Decimal("100.00"),
            costs=CostBreakdown(flash_loan_fee=Decimal("0.30")),
            max_gas_usd=Decimal("0"),
            max_relay_usd=Decimal("0"),
            minimum_net_profit_usd=Decimal("0.20"),
        )
        evaluation = OpportunityEconomicEvaluation(candidate=self.evaluation.candidate, proof=bad_proof)
        with self.assertRaises(OpportunityExecutionError):
            self._assemble(evaluation)

    def test_unsupported_discovery_path_fails_closed(self):
        candidate = OpportunityCandidate(
            token_a=self.evaluation.candidate.token_a,
            token_b=self.evaluation.candidate.token_b,
            venue_path="unknown->venue",
            loan_amount=self.evaluation.candidate.loan_amount,
            simulation=self.evaluation.candidate.simulation,
        )
        evaluation = OpportunityEconomicEvaluation(candidate=candidate, proof=self.evaluation.proof)
        with self.assertRaises(OpportunityExecutionError):
            self._assemble(evaluation)


if __name__ == "__main__":
    unittest.main()
