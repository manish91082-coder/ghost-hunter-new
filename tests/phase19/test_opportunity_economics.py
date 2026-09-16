import unittest
from decimal import Decimal

from phantomx.economic_proof import EconomicProof, build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.opportunity_discovery import OpportunityCandidate
from phantomx.opportunity_economics import (
    OpportunityEconomicsError,
    evaluate_discovered_opportunities,
    make_economic_proof_builder,
)
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg


def snapshot(venue, token_in, token_out, amount_in, amount_out, fee, router):
    quote = ExactQuote(venue, token_in, token_out, amount_in, amount_out, 123, fee)
    return QuoteSnapshot.from_exact_quote(
        quote, chain_id=137, observed_at_unix=1000, pool_or_router=router, gas_estimate=100000
    )


class OpportunityEconomicsTests(unittest.TestCase):
    def setUp(self):
        self.token_a = "0x" + "aa" * 20
        self.token_b = "0x" + "bb" * 20
        self.q1 = snapshot(
            "quickswap_v2", self.token_a, self.token_b, 1000, 1100, 30, "0x" + "11" * 20
        )
        self.q2 = snapshot(
            "uniswap_v3", self.token_b, self.token_a, 1100, 1120, 500, "0x" + "22" * 20
        )
        self.simulation = simulate_two_leg(self.q1, self.q2)
        self.candidate = OpportunityCandidate(
            token_a=self.token_a,
            token_b=self.token_b,
            venue_path="quickswap_v2->uniswap_v3",
            loan_amount=1000,
            simulation=self.simulation,
        )

    @staticmethod
    def _costs():
        return CostBreakdown(
            flash_loan_fee=Decimal("0.10"),
            dex_fees=Decimal("0.20"),
            price_impact=Decimal("0.05"),
            gas=Decimal("0.10"),
            relay=Decimal("0.05"),
            other=Decimal("0.05"),
        )

    def _proof(self, candidate, final_settlement="100.95", route=None, quotes=None):
        return build_economic_proof(
            route_hash=route or candidate.simulation.route_hash,
            quote_hashes=quotes or tuple(leg.quote_hash for leg in candidate.simulation.legs),
            valuation_hash="0x" + "44" * 32,
            final_settlement_usd=Decimal(final_settlement),
            loan_principal_usd=Decimal("100.00"),
            costs=self._costs(),
            max_gas_usd=Decimal("0.10"),
            max_relay_usd=Decimal("0.05"),
        )

    def test_complete_frontier_is_evaluated_and_best_is_selected(self):
        second_q1 = snapshot(
            "uniswap_v3", self.token_a, self.token_b, 2000, 2200, 500, "0x" + "22" * 20
        )
        second_q2 = snapshot(
            "quickswap_v2", self.token_b, self.token_a, 2200, 2240, 30, "0x" + "11" * 20
        )
        second_simulation = simulate_two_leg(second_q1, second_q2)
        second = OpportunityCandidate(
            token_a=self.token_a,
            token_b=self.token_b,
            venue_path="uniswap_v3->quickswap_v2",
            loan_amount=2000,
            simulation=second_simulation,
        )
        result = evaluate_discovered_opportunities(
            (self.candidate, second),
            lambda candidate: self._proof(
                candidate, final_settlement="100.95" if candidate.loan_amount == 1000 else "100.90"
            ),
        )
        self.assertEqual(len(result.evaluated), 2)
        self.assertEqual(result.best.candidate.loan_amount, 1000)
        self.assertEqual(len(result.profitable), 2)

    def test_proof_builder_binds_route_and_quote_hashes(self):
        builder = make_economic_proof_builder(
            valuation_for=lambda candidate: ("0x" + "44" * 32, "100.95", "100.00"),
            costs_for=lambda candidate: self._costs(),
            max_gas_usd="0.10",
            max_relay_usd="0.05",
        )
        proof = builder(self.candidate)
        self.assertEqual(proof.route_hash, self.simulation.route_hash)
        self.assertEqual(tuple(proof.quote_hashes), tuple(leg.quote_hash for leg in self.simulation.legs))

    def test_route_or_quote_binding_mismatch_is_rejected(self):
        with self.assertRaises(OpportunityEconomicsError):
            evaluate_discovered_opportunities(
                (self.candidate,),
                lambda candidate: self._proof(candidate, route="0x" + "55" * 32),
            )
        with self.assertRaises(OpportunityEconomicsError):
            evaluate_discovered_opportunities(
                (self.candidate,),
                lambda candidate: self._proof(
                    candidate, quotes=("0x" + "66" * 32, self.q2.quote_hash)
                ),
            )

    def test_candidate_loan_amount_must_match_simulation_before_evaluation(self):
        malformed = OpportunityCandidate(
            token_a=self.token_a,
            token_b=self.token_b,
            venue_path=self.candidate.venue_path,
            loan_amount=2000,
            simulation=self.simulation,
        )
        called = []

        def unexpected_evaluator(candidate):
            called.append(candidate)
            return self._proof(self.candidate)

        with self.assertRaises(OpportunityEconomicsError):
            evaluate_discovered_opportunities((malformed,), unexpected_evaluator)
        self.assertEqual(called, [])

    def test_no_strictly_profitable_candidate_fails_closed(self):
        with self.assertRaises(OpportunityEconomicsError):
            evaluate_discovered_opportunities(
                (self.candidate,),
                lambda candidate: self._proof(candidate, final_settlement="100.74"),
            )

    def test_invalid_proof_object_is_rejected(self):
        with self.assertRaises(OpportunityEconomicsError):
            evaluate_discovered_opportunities((self.candidate,), lambda candidate: "not-a-proof")


if __name__ == "__main__":
    unittest.main()
