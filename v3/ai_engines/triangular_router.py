"""
PhantomX v3 Universal Profit Engine - Triangular Multi-Hop Router (ai_engines/triangular_router.py)
===================================================================================================
Evaluates Direct Pair Arbitrage (USDC -> Token -> USDC) vs Triangular Multi-Hop Arbitrage (USDC -> TokenA -> TokenB -> USDC).
Calculates Cumulative Multi-Pool Spread & Fee Load (Balancer 0.00% + Curve 0.04% + UV3 0.05% = 0.09%).
"""

import sys
import math

class TriangularRouterEngine:
    """
    Evaluates multi-hop routing paths across QuickSwap v2/v3, Uniswap v3, Balancer v2, and Curve.
    """
    def __init__(self):
        # Supported Swap Routes
        self.routes = {
            "TRIANGULAR_LOW_FEE": {
                "name": "Balancer V2 (0%) + Curve (0.04%) + UV3 (0.05%)",
                "total_fee_load": 0.0009, # 0.09% Total Fee Load
                "is_triangular": True
            },
            "DIRECT_LOW_FEE": {
                "name": "Balancer V2 (0%) + UV3 (0.05%) + QuickSwap V3 (0.05%)",
                "total_fee_load": 0.0010, # 0.10% Total Fee Load
                "is_triangular": False
            },
            "STANDARD_QS_V2": {
                "name": "Aave V3 (0.05%) + QuickSwap V2 (0.30%) + UV3 (0.05%)",
                "total_fee_load": 0.0040, # 0.40% Total Fee Load
                "is_triangular": False
            }
        }

    def evaluate_triangular_spread(self, p_usdc_tokA: float, p_tokA_tokB: float, p_tokB_usdc: float) -> float:
        """
        Calculates cumulative triangular spread (%):
        Triangular Output = 1.0 * (1/P_A) * P_AB * P_B_USDC
        """
        if p_usdc_tokA <= 0 or p_tokA_tokB <= 0 or p_tokB_usdc <= 0:
            return 0.0
        
        # Expressed in USDC multiplier
        output_usdc = (1.0 / p_usdc_tokA) * p_tokA_tokB * p_tokB_usdc
        cumulative_spread_pct = (output_usdc - 1.0) * 100.0
        return max(cumulative_spread_pct, 0.0)

    def evaluate_all_routes(self, direct_spread_pct: float, triangular_spread_pct: float, usdc_reserves: float, gas_cost_usd: float, loan_tier=25_000) -> dict:
        """
        Evaluates Direct vs Triangular routes for a given market block scan.
        """
        evaluations = {}

        for rkey, rinfo in self.routes.items():
            fee_load = rinfo["total_fee_load"]
            effective_spread = triangular_spread_pct if rinfo["is_triangular"] else direct_spread_pct
            
            gross_gain = loan_tier * (effective_spread / 100.0)
            fee_cost = loan_tier * fee_load
            slippage_cost = (loan_tier / max(usdc_reserves, 1.0)) * 0.02 * loan_tier
            net_pnl = gross_gain - fee_cost - slippage_cost - gas_cost_usd

            evaluations[rkey] = {
                "route_name": rinfo["name"],
                "fee_load_pct": fee_load * 100.0,
                "effective_spread_pct": effective_spread,
                "gross_gain_usd": gross_gain,
                "fee_cost_usd": fee_cost,
                "slippage_usd": slippage_cost,
                "gas_cost_usd": gas_cost_usd,
                "net_pnl_usd": net_pnl,
                "is_triangular": rinfo["is_triangular"],
                "is_profitable": net_pnl >= 0.20  # FIXED: project goal is $0.20 net profit minimum
            }

        # Pick Best Route
        best_rkey = max(evaluations.keys(), key=lambda k: evaluations[k]["net_pnl_usd"])
        best_res = evaluations[best_rkey]

        return {
            "best_route_key": best_rkey,
            "best_route_name": best_res["route_name"],
            "best_net_pnl_usd": best_res["net_pnl_usd"],
            "is_triangular": best_res["is_triangular"],
            "evaluations": evaluations
        }

if __name__ == "__main__":
    router = TriangularRouterEngine()
    print("🤖 PhantomX v3 Triangular Router Engine Initialized")
    res = router.evaluate_all_routes(direct_spread_pct=0.15, triangular_spread_pct=0.32, usdc_reserves=100_000, gas_cost_usd=0.15, loan_tier=25_000)
    print(f"Best Route: {res['best_route_name']} | Net Profit: ${res['best_net_pnl_usd']:.2f} USD")
