import unittest
from decimal import Decimal

from phantomx.economic_proof import EconomicProof
from phantomx.economics import CostBreakdown
from phantomx.loan_optimizer import (
    LoanEvaluation,
    LoanOptimizationError,
    candidate_amount_grid,
    optimize_exact_candidates,
)

ROUTE = "0x" + "11" * 32
VALUATION = "0x" + "44" * 32


def proof_for(amount: int, final_settlement: str) -> EconomicProof:
    return EconomicProof(
        schema_version=1,
        route_hash=ROUTE,
        quote_hashes=("0x" + format(amount, "064x"), "0x" + "22" * 32),
        valuation_hash=VALUATION,
        final_settlement_usd=Decimal(final_settlement),
        loan_principal_usd=Decimal(amount),
        costs=CostBreakdown(flash_loan_fee=Decimal("0.01")),
        max_gas_usd=Decimal("0"),
        max_relay_usd=Decimal("0"),
    )


def evaluate(amount: int) -> LoanEvaluation:
    # Synthetic exact-evidence function: no spread/slippage proxy is used.
    # The caller supplies the final settlement resulting from exact quote evaluation.
    settlements = {
        100: "100.50",
        200: "201.00",
        300: "301.00",
        400: "400.50",
    }
    return LoanEvaluation(amount, 137, 5000, proof_for(amount, settlements[amount]))


class LoanOptimizerTests(unittest.TestCase):
    def test_selects_best_exact_candidate_not_continuous_proxy(self):
        result = optimize_exact_candidates((100, 200, 300, 400), evaluate)
        self.assertEqual(result.best.loan_amount, 300)
        self.assertEqual(result.best_net_profit_usd, Decimal("0.99"))
        self.assertEqual(tuple(item.loan_amount for item in result.evaluated), (100, 200, 300, 400))

    def test_candidates_at_or_below_floor_are_not_eligible(self):
        def evaluate_floor(amount):
            settlement = Decimal(amount) + Decimal("0.21")
            return LoanEvaluation(
                amount,
                137,
                5000,
                proof_for(amount, str(settlement)),
            )

        result = optimize_exact_candidates((100, 200), evaluate_floor)
        self.assertEqual(result.best.loan_amount, 200)
        self.assertTrue(result.best.proof.economically_valid)

    def test_no_profitable_candidate_fails_closed(self):
        def evaluate_bad(amount):
            return LoanEvaluation(
                amount,
                137,
                5000,
                proof_for(amount, str(Decimal(amount) + Decimal("0.21"))),
            )

        with self.assertRaises(LoanOptimizationError):
            optimize_exact_candidates((100, 200), evaluate_bad)

    def test_all_candidates_are_evaluated_and_errors_are_not_skipped(self):
        calls = []

        def evaluator(amount):
            calls.append(amount)
            if amount == 200:
                raise RuntimeError("quote unavailable")
            return evaluate(amount)

        with self.assertRaises(LoanOptimizationError):
            optimize_exact_candidates((100, 200, 300), evaluator)
        self.assertEqual(calls, [100, 200])

    def test_mismatched_return_amount_is_rejected(self):
        def bad(amount):
            return LoanEvaluation(amount + 1, 137, 5000, proof_for(amount + 1, str(amount + 1.0)))

        with self.assertRaises(LoanOptimizationError):
            optimize_exact_candidates((100,), bad)

    def test_mixed_market_blocks_are_rejected(self):
        def bad(amount):
            return LoanEvaluation(amount, 137, 5000 + amount, proof_for(amount, str(amount + 1.0)))

        with self.assertRaises(LoanOptimizationError):
            optimize_exact_candidates((100, 200), bad)

    def test_duplicate_candidate_is_rejected(self):
        with self.assertRaises(LoanOptimizationError):
            optimize_exact_candidates((100, 100), evaluate)

    def test_empty_candidate_domain_is_rejected(self):
        with self.assertRaises(LoanOptimizationError):
            optimize_exact_candidates((), evaluate)

    def test_grid_is_integer_and_inclusive(self):
        self.assertEqual(candidate_amount_grid(100, 500, 100), (100, 200, 300, 400, 500))

    def test_grid_rejects_invalid_parameters(self):
        for args in ((0, 500, 100), (100, 0, 100), (100, 500, 0), (500, 100, 100)):
            with self.assertRaises(LoanOptimizationError):
                candidate_amount_grid(*args)

    def test_tie_breaks_to_smaller_loan(self):
        def tied(amount):
            return LoanEvaluation(
                amount,
                137,
                5000,
                proof_for(amount, str(Decimal(amount) + Decimal("0.51"))),
            )

        result = optimize_exact_candidates((100, 200), tied)
        self.assertEqual(result.best.loan_amount, 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
