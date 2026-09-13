"""
PhantomX v3 Universal Profit Engine - Integrated AI Brain (ai_engines/universal_ai_brain.py)
=============================================================================================
Integrates 5 Parallel AI Brains:
  1. Direct Pair Arbitrage Engine
  2. Triangular Multi-Hop Router
  3. Low-Fee Multi-Route Optimizer (0.09% Fee Load)
  4. Dynamic Micro-Loan Scaler L* ($1k - $500k)
  5. Time-Series Horizon Oracle
"""

import sys
import os
import importlib
import numpy as np

AI_ENGINES_DIR = os.path.abspath(os.path.dirname(__file__))
if AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, AI_ENGINES_DIR)

from triangular_router import TriangularRouterEngine
from micro_loan_optimizer import MicroLoanOptimizer
from horizon_oracle import TimeSeriesHorizonOracle

class UniversalAIBrainV3:
    """
    Master AGI Brain Engine for PhantomX v3.
    """
    def __init__(self):
        self.router = TriangularRouterEngine()
        self.optimizer = MicroLoanOptimizer()
        self.oracle = TimeSeriesHorizonOracle()
        self.spread_history = {} # {pair_symbol: [history]}

        # 5-Year Master Brain Adapter Integration
        self.brain_5yr = None
        try:
            adapter_mod = importlib.import_module("phantomx_mvp.5year_brain_adapter")
            self.brain_5yr = adapter_mod.Phantom5YearBrainAdapter()
            if self.brain_5yr.loaded:
                print("🧠 [Universal AGI Brain V3] Connected to 5-Year Master Brain (393M Records)!")
        except Exception:
            try:
                adapter_mod = importlib.import_module("5year_brain_adapter")
                self.brain_5yr = adapter_mod.Phantom5YearBrainAdapter()
                if self.brain_5yr.loaded:
                    print("🧠 [Universal AGI Brain V3] Connected to 5-Year Master Brain (393M Records)!")
            except Exception as e:
                print(f"ℹ️ V3 5-Year Brain Adapter notice: {e}. Micro-Loan Optimizer active.")

    def analyze_block_opportunity(self, pair_symbol: str, qs_price: float, uv3_price: float, pool_usdc_reserve: float, gas_fee_gwei: float, triangular_price=0.0, pol_usd=0.098) -> dict:
        """
        Analyzes a market opportunity across direct and triangular routes, optimal loan sizing, and horizon predictions.
        Returns complete AGI Decision Matrix.
        """
        # 1. Compute Direct Spread %
        spread_raw = abs(qs_price - uv3_price)
        max_p = max(qs_price, uv3_price, 1e-6)
        direct_spread_pct = (spread_raw / max_p) * 100.0

        # 2. Compute Triangular Spread %
        triangular_spread_pct = 0.0
        if triangular_price > 0:
            triangular_spread_pct = max((triangular_price - 1.0) * 100.0, 0.0)

        # 3. Update Time-Series Oracle History
        if pair_symbol not in self.spread_history:
            self.spread_history[pair_symbol] = []
        self.spread_history[pair_symbol].append(direct_spread_pct)
        if len(self.spread_history[pair_symbol]) > 5:
            self.spread_history[pair_symbol].pop(0)

        forecast_spread_pct = self.oracle.predict_future_spread(self.spread_history[pair_symbol])

        # Real Polygon Gas Cost (320k gas units compressed for v3)
        gas_units = 320_000
        gas_cost_usd = gas_units * (gas_fee_gwei * 1e-9) * pol_usd

        # 4. Route Evaluation & Loan Size Optimization
        effective_spread = max(direct_spread_pct, triangular_spread_pct, forecast_spread_pct)
        best_route_eval = self.router.evaluate_all_routes(direct_spread_pct, triangular_spread_pct, pool_usdc_reserve, gas_cost_usd, loan_tier=25_000)
        
        fee_load = best_route_eval["evaluations"][best_route_eval["best_route_key"]]["fee_load_pct"] / 100.0
        optimal_loan, net_pnl = self.optimizer.compute_optimal_loan_size(effective_spread, pool_usdc_reserve, fee_load, gas_cost_usd)

        # FIXED: EXECUTE only when net profit >= $0.20 after ALL expenses (project goal)
        decision = "EXECUTE" if net_pnl >= 0.20 else ("WAIT" if net_pnl > -1.0 else "IGNORE")

        return {
            "pair": pair_symbol,
            "direct_spread_pct": round(direct_spread_pct, 4),
            "triangular_spread_pct": round(triangular_spread_pct, 4),
            "forecast_spread_pct": round(forecast_spread_pct, 4),
            "effective_spread_pct": round(effective_spread, 4),
            "decision": decision,
            "best_route_name": best_route_eval["best_route_name"],
            "optimal_loan_usd": optimal_loan,
            "expected_net_pnl_usd": round(net_pnl, 2),
            "gas_cost_usd": round(gas_cost_usd, 4),
            "is_triangular": best_route_eval["is_triangular"]
        }

if __name__ == "__main__":
    brain = UniversalAIBrainV3()
    print("🧠 Master Universal AGI Brain v3 Initialized")
    res = brain.analyze_block_opportunity("WMATIC", 0.0982, 0.0980, 150_000, 275.0, triangular_price=1.0028, pol_usd=0.098)
    print(f"Decision: {res['decision']} | Route: {res['best_route_name']} | Loan L*: ${res['optimal_loan_usd']:,} | Net Profit: ${res['expected_net_pnl_usd']:.2f} USD")
