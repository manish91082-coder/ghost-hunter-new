import sys
import os
import json
import importlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

from predictive_oracle_model import PhantomOracle

class PhantomAIBrain:
    """
    PhantomX AGI Brain for Dynamic Arbitrage & MEV Decision Making.
    Powered by 5-Year Trained Master AI Brain (39.3 Crore / 393M Records)
    Integrated with Predictive Oracle Time-Series Volatility Model.
    """
    def __init__(self, weights_path="real_trained_ai_weights.json"):
        self.weights_loan = np.array([1.0, 0.5, -0.1, 0.0, 0.0]) # Fallback
        self.weights_bribe = np.array([0.0, 0.0, 1.0, 1.1, 0.0]) # Fallback
        
        # 5-Year Master Brain Adapter Integration
        self.brain_5yr = None
        try:
            adapter_mod = importlib.import_module("phantomx_mvp.5year_brain_adapter")
            self.brain_5yr = adapter_mod.Phantom5YearBrainAdapter()
            if self.brain_5yr.loaded:
                print("🧠 [PhantomAIBrain V2] Connected to 5-Year Master Brain (393M Records)!")
        except Exception:
            try:
                adapter_mod = importlib.import_module("5year_brain_adapter")
                self.brain_5yr = adapter_mod.Phantom5YearBrainAdapter()
                if self.brain_5yr.loaded:
                    print("🧠 [PhantomAIBrain V2] Connected to 5-Year Master Brain (393M Records)!")
            except Exception as e:
                print(f"ℹ️ 5-Year Brain Adapter notice: {e}. Standard neural weights active.")

        if os.path.exists(weights_path):
            with open(weights_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.weights_loan = np.array(data.get("loan_sizing_weights", self.weights_loan))
                self.weights_bribe = np.array(data.get("dynamic_bribe_weights", self.weights_bribe))
                print(f"🧠 AGI Weights Loaded from {weights_path}")
        else:
            print("⚠️ Warning: No trained weights found. Using fallbacks.")
            
        self.total_decisions = 0
        self.correct_decisions = 0
        self.consecutive_correct = 0

        self.pol_usd = 0.50
        self.min_profit_usd = float(os.getenv("MIN_NET_PROFIT_USD", "0.50"))

        # Predictive Oracle Integration (Rolling sequence per pair)
        self.oracle = PhantomOracle()
        self.spread_history = {} # {token_pair: [last_5_spreads]}

    def set_pol_price(self, pol_usd: float):
        """Update real-time MATIC/POL price in USD for dynamic gas calculations."""
        if pol_usd and pol_usd > 0:
            self.pol_usd = float(pol_usd)
            return True
        return False

    def set_min_profit(self, min_profit_usd: float):
        """Update minimum net profit threshold in USD (e.g. 0.50 USD)."""
        if min_profit_usd is not None and min_profit_usd >= 0:
            self.min_profit_usd = float(min_profit_usd)
            return True
        return False

    def reload_weights(self, weights_path="real_trained_ai_weights.json"):
        """Dynamically hot-reload AI weights from disk without process restart."""
        if os.path.exists(weights_path):
            with open(weights_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.weights_loan = np.array(data.get("loan_sizing_weights", self.weights_loan))
                self.weights_bribe = np.array(data.get("dynamic_bribe_weights", self.weights_bribe))
                print(f"🔄 [AI Hot-Reload] Successfully reloaded weights from {weights_path}")
                return True
        return False

    def get_action(self, obs):
        """
        Uses trained neural weights to predict optimal loan size and bribe.
        """
        # Loan sizing logic (Sigmoid)
        raw_loan = np.dot(obs, self.weights_loan)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        # Bribe multiplier logic (Clipped 0 to 2)
        raw_bribe = np.dot(obs, self.weights_bribe)
        bribe_mult = min(max(raw_bribe, 0.0), 2.0)
        
        return loan_pct, bribe_mult

    def analyze_scenario(self, qs_price, uv3_price, qs_usdc_reserves, base_gas_fee_gwei, competitor_bribe_gwei=0, pair_id="WETH", pol_usd=None, min_profit_usd=None):
        """
        Analyzes a market scenario using the AGI trained model + Predictive Oracle.
        Returns: ACTION, OPTIMAL_LOAN, EXPECTED_PROFIT, MEV_BRIBE
        """
        self.total_decisions += 1
        current_pol_usd = float(pol_usd) if (pol_usd is not None and pol_usd > 0) else self.pol_usd
        target_min_profit = float(min_profit_usd) if (min_profit_usd is not None and min_profit_usd >= 0) else self.min_profit_usd
        
        spread_raw = abs(qs_price - uv3_price)
        spread_pct = spread_raw / max(qs_price, 1)
        
        # Track rolling spread history for Oracle
        if pair_id not in self.spread_history:
            self.spread_history[pair_id] = []
        self.spread_history[pair_id].append(spread_pct)
        if len(self.spread_history[pair_id]) > 5:
            self.spread_history[pair_id].pop(0)

        # Oracle future volatility prediction if 5 periods available
        oracle_pred = 0.0
        if len(self.spread_history[pair_id]) == 5 and self.oracle.trained:
            oracle_pred = self.oracle.predict_future(np.array(self.spread_history[pair_id]))

        if spread_pct <= 0.0001 and oracle_pred <= 0.0001:
            return "IGNORE", 0, 0, 0
            
        # Prepare observation array matching the calibrated training environment (5D normalized)
        obs = np.array([
            min(spread_pct, 0.05),                    # [0] spread_pct (capped at 5%)
            min(qs_usdc_reserves / 10_000_000, 1.0),   # [1] reserves normalized to $10M max
            min(base_gas_fee_gwei / 500.0, 1.0),      # [2] gas normalized to 500 Gwei max
            min(competitor_bribe_gwei / 500.0, 1.0),  # [3] competitor bribe normalized
            min(qs_usdc_reserves / 10_000_000, 1.0)   # [4] pool depth signal
        ], dtype=np.float32)
        
        # Get AI Predictions
        loan_pct, bribe_mult = self.get_action(obs)
        
        # Calculate real values
        max_safe_borrow = qs_usdc_reserves * 0.01 # Max 1% of pool
        if self.brain_5yr and self.brain_5yr.loaded:
            optimal_loan_brain = self.brain_5yr.predict_optimal_loan(
                qs_usdc_reserves, qs_usdc_reserves, spread_pct * 100.0, base_gas_fee_gwei, 85.0
            )
            optimal_loan = min(optimal_loan_brain, max_safe_borrow)
        else:
            if loan_pct == 0:
                return "IGNORE", 0, 0, 0
            optimal_loan = max_safe_borrow * loan_pct
        
        # Dynamic Miner Tip (Instead of hardcoded 90%)
        mev_bribe_gwei = base_gas_fee_gwei * bribe_mult
        
        # Calculate expected profitability with real fee structure & Polygon gas economics
        TOTAL_FEE_PCT = 0.0044  # 0.44% (Aave 0.09% + QS 0.30% + UV3 0.05%)
        GAS_UNITS = 500_000

        gross_profit_usd = optimal_loan * spread_pct
        total_fee_usd = optimal_loan * TOTAL_FEE_PCT
        gas_cost_usd = (base_gas_fee_gwei + mev_bribe_gwei) * GAS_UNITS * 1e-9 * current_pol_usd
        
        net_profit_estimate = gross_profit_usd - total_fee_usd - gas_cost_usd
        
        if net_profit_estimate >= target_min_profit:   # Dynamic threshold (default $0.50 USD)
            return "EXECUTE", optimal_loan, net_profit_estimate, mev_bribe_gwei
        elif net_profit_estimate > -1:
            return "WAIT", optimal_loan, net_profit_estimate, mev_bribe_gwei
        else:
            return "IGNORE", optimal_loan, net_profit_estimate, mev_bribe_gwei

    def record_result(self, was_correct):
        if was_correct:
            self.correct_decisions += 1
            self.consecutive_correct += 1
        else:
            self.consecutive_correct = 0

if __name__ == "__main__":
    brain = PhantomAIBrain()
    print("🧠 PhantomX AGI Brain (Deep Trained) Initialized")
    # Test Scenario: Base gas 50, Competitor 0, Spread 1%, Reserves 100k, POL_USD = $0.45, Min Profit = $0.50
    decision, loan, expected, bribe = brain.analyze_scenario(2500, 2525, 100000, 50.0, 0, pol_usd=0.45, min_profit_usd=0.50)
    print(f"Test -> Decision: {decision} | Optimal Loan: ${loan:.2f} | Net Profit: ${expected:.2f} | Dynamic Bribe: {bribe:.2f} Gwei | POL_USD: $0.45 | Min Profit: $0.50")
