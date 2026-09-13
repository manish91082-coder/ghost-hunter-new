"""
PhantomX v3 Universal Profit Engine - Automated Test Harness (test_universal_engine.py)
=======================================================================================
Verifies Triangular Multi-Hop routing, Micro-Loan Optimizer, Horizon Oracle, and AGI Decision Engine.
"""

import sys
import os
import unittest

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.join(os.path.dirname(__file__), "ai_engines"))

from triangular_router import TriangularRouterEngine
from micro_loan_optimizer import MicroLoanOptimizer
from horizon_oracle import TimeSeriesHorizonOracle
from universal_ai_brain import UniversalAIBrainV3

class TestUniversalEngineV3(unittest.TestCase):

    def setUp(self):
        self.router = TriangularRouterEngine()
        self.optimizer = MicroLoanOptimizer()
        self.oracle = TimeSeriesHorizonOracle()
        self.brain = UniversalAIBrainV3()

    def test_triangular_spread_calculation(self):
        spread = self.router.evaluate_triangular_spread(2500.0, 25000.0, 0.1005)
        self.assertGreater(spread, 0.0)
        print(f"✅ Test 1 Passed: Triangular Cumulative Spread = {spread:.4f}%")

    def test_micro_loan_optimization(self):
        best_loan, best_pnl = self.optimizer.compute_optimal_loan_size(spread_pct=0.25, pool_reserve_usd=100_000, fee_load=0.0010, gas_cost_usd=0.15)
        self.assertIn(best_loan, [1_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000])
        self.assertGreater(best_pnl, 0.50)
        print(f"✅ Test 2 Passed: Dynamic Micro-Loan L* = ${best_loan:,} USD | Net Profit = ${best_pnl:.2f}")

    def test_horizon_oracle_forecasting(self):
        history = [0.10, 0.12, 0.14, 0.17, 0.20]
        pred = self.oracle.predict_future_spread(history)
        self.assertGreater(pred, 0.15)
        print(f"✅ Test 3 Passed: 2-Block Forecast Spread = {pred:.4f}%")

    def test_integrated_5_brain_decision(self):
        eval_res = self.brain.analyze_block_opportunity("WMATIC", 0.0982, 0.0980, 150_000, 275.0, triangular_price=1.0028)
        self.assertEqual(eval_res["decision"], "EXECUTE")
        self.assertGreater(eval_res["expected_net_pnl_usd"], 0.50)
        print(f"✅ Test 4 Passed: AGI Decision = {eval_res['decision']} | Expected Net PnL = ${eval_res['expected_net_pnl_usd']:.2f}")

    def test_low_spread_protection(self):
        eval_res = self.brain.analyze_block_opportunity("WBTC", 79787.0, 79790.0, 100_000, 300.0, triangular_price=1.0001)
        self.assertIn(eval_res["decision"], ["IGNORE", "WAIT"])
        print(f"✅ Test 5 Passed: Low Spread Protection Decision = {eval_res['decision']}")

if __name__ == "__main__":
    print("======================================================================")
    print("🧪 PHANTOM-X v3 UNIVERSAL ENGINE AUTOMATED TEST HARNESS")
    print("======================================================================")
    unittest.main(verbosity=2)
