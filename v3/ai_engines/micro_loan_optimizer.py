"""
PhantomX v3 Universal Profit Engine - Micro-Loan Scaler (ai_engines/micro_loan_optimizer.py)
==============================================================================================
Dynamic Loan Scaler ($L^*$ Optimizer) evaluating loan tiers from $1,000 up to $500,000.
Calculates pool reserve slippage degradation and maximizes Net USD Profit.
"""

import sys

class MicroLoanOptimizer:
    """
    Evaluates 7 loan tiers ($1k, $5k, $10k, $25k, $50k, $100k, $250k, $500k) to select optimal loan size L*.
    """
    def __init__(self):
        self.loan_tiers = [1_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000]

    def estimate_slippage_usd(self, loan_usd: float, pool_usdc_reserve: float) -> float:
        """
        Calculates price impact / slippage in USD based on pool USDC reserve depth.
        Slippage % = (Loan_USD / Pool_USDC_Reserve) * 0.02
        """
        if pool_usdc_reserve <= 0:
            return loan_usd * 0.01
        slippage_pct = (loan_usd / max(pool_usdc_reserve, 1.0)) * 0.02
        return loan_usd * slippage_pct

    def compute_optimal_loan_size(self, spread_pct: float, pool_reserve_usd: float, fee_load: float, gas_cost_usd: float) -> tuple:
        """
        Computes continuous L* (Optimal Loan Size) dynamically using marginal PnL calculus:
        d(Net_PnL)/dL = (Spread - FeeLoad) - (0.04 / PoolReserve) * L = 0
        => L* = ((Spread - FeeLoad) * PoolReserve) / 0.04
        No fixed loan tiers. Completely dynamic based on live market reserves & spread.
        """
        s = spread_pct / 100.0
        f = fee_load
        
        if s <= f or pool_reserve_usd <= 0:
            return 100.0, -gas_cost_usd
            
        margin = s - f
        # Continuous optimal loan size equation
        l_star_raw = (margin * pool_reserve_usd) / 0.04
        
        # Dynamic pool liquidity cap (max 35% of live pool reserves to prevent slippage collapse)
        max_loan_cap = max(pool_reserve_usd * 0.35, 500.0)
        best_loan = max(100.0, min(l_star_raw, max_loan_cap))
        
        gross_gain = best_loan * s
        fee_cost = best_loan * f
        slippage_cost = self.estimate_slippage_usd(best_loan, pool_reserve_usd)
        best_pnl = gross_gain - fee_cost - slippage_cost - gas_cost_usd
        
        return float(round(best_loan, 2)), float(round(best_pnl, 2))

if __name__ == "__main__":
    optimizer = MicroLoanOptimizer()
    print("🤖 PhantomX v3 Micro-Loan Optimizer Initialized")
    best_loan, best_pnl = optimizer.compute_optimal_loan_size(spread_pct=0.25, pool_reserve_usd=100_000, fee_load=0.0010, gas_cost_usd=0.15)
    print(f"Optimal Loan L*: ${best_loan:,} USD | Net Profit: ${best_pnl:.2f} USD")
