"""
PhantomX AI Live Stress Data Retrainer
======================================
Trains neural weights on combined dataset:
  - 50,000 historical Polygon mainnet records (real_training_data_50k.jsonl)
  - 7,800+ live stress test Polygon mainnet scans (stress_test_20260905_204526/raw_scans.jsonl)
  - Pair-specific scenarios for WETH ($2.4k), WMATIC ($0.09), and WBTC ($79k)

Usage: python retrain_from_stress_data.py
"""
import os
import sys
import json
import time
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# ─── Economic Constants ───────────────────────────────────────────────────────
AAVE_FEE    = 0.0009   # 0.09%
QS_FEE      = 0.0030   # 0.30%
UV3_FEE     = 0.0005   # 0.05%
TOTAL_FEE   = AAVE_FEE + QS_FEE + UV3_FEE  # 0.44%
GAS_UNITS   = 500_000  # Arbitrage tx gas limit
POL_USD     = 0.50     # MATIC/POL price in USD

# ─── Data Loader & Training Environment ───────────────────────────────────────
class CombinedStressEnv:
    def __init__(self, historical_file="real_training_data_50k.jsonl", stress_dir="stress_test_20260905_204526"):
        self.raw_data = []

        # 1. Load historical 50K records
        if os.path.exists(historical_file):
            with open(historical_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        self.raw_data.append({
                            "spread_pct": row.get("real_spread_pct", 0),
                            "reserves_usd": row.get("qs_usdc_reserves", 5e6),
                            "gas_gwei": row.get("base_gas_fee_gwei", 275),
                            "competitor_gwei": row.get("competitor_bribe_gwei", 0),
                            "symbol": "HISTORICAL"
                        })
            print(f"  ✅ Loaded {len(self.raw_data):,} historical training records")

        # 2. Load live stress test scans
        raw_scans_path = os.path.join(stress_dir, "raw_scans.jsonl")
        stress_count = 0
        if os.path.exists(raw_scans_path):
            with open(raw_scans_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        spread = row.get("spread_pct", 0)
                        if spread > 1.0: # If percentage (e.g. 0.15%), convert to fractional (0.0015)
                            spread = spread / 100.0
                        self.raw_data.append({
                            "spread_pct": spread,
                            "reserves_usd": row.get("qs_usdc_reserves", 5e6),
                            "gas_gwei": row.get("gas_gwei", 275),
                            "competitor_gwei": 0,
                            "symbol": row.get("sym", "UNKNOWN")
                        })
                        stress_count += 1
            print(f"  ✅ Loaded {stress_count:,} live stress test mainnet scans from {stress_dir}")

        # 3. Add pair-specific synthetic volatility scenarios (WETH, WMATIC, WBTC)
        synthetic_scenarios = [
            # WETH Volatility (Spread > 0.45%)
            {"spread_pct": 0.0065, "reserves_usd": 8e6, "gas_gwei": 250, "competitor_gwei": 10, "symbol": "WETH"},
            {"spread_pct": 0.0120, "reserves_usd": 6e6, "gas_gwei": 300, "competitor_gwei": 25, "symbol": "WETH"},
            # WMATIC Volatility
            {"spread_pct": 0.0080, "reserves_usd": 3e6, "gas_gwei": 220, "competitor_gwei": 5, "symbol": "WMATIC"},
            # WBTC Volatility
            {"spread_pct": 0.0055, "reserves_usd": 12e6, "gas_gwei": 350, "competitor_gwei": 50, "symbol": "WBTC"},
            {"spread_pct": 0.0200, "reserves_usd": 10e6, "gas_gwei": 400, "competitor_gwei": 100, "symbol": "WBTC"},
        ]
        self.raw_data.extend(synthetic_scenarios * 500)
        print(f"  ✅ Total Combined Training Dataset: {len(self.raw_data):,} rows")

        self.idx = 0
        np.random.shuffle(self.raw_data)

    def _row_to_obs(self, row):
        spread     = row["spread_pct"]
        reserves   = row["reserves_usd"]
        gas_gwei   = max(50.0, min(row["gas_gwei"], 1000.0))
        comp_gwei  = row["competitor_gwei"]

        # 5D Normalized Observation Matching ai_brain.py
        obs = np.array([
            min(spread, 0.05),
            min(reserves / 10_000_000, 1.0),
            min(gas_gwei / 500.0, 1.0),
            min(comp_gwei / 500.0, 1.0),
            min(reserves / 10_000_000, 1.0)
        ], dtype=np.float32)

        return obs, reserves, gas_gwei, comp_gwei, spread

    def step(self, action, obs, reserves, gas_gwei, comp_gwei, spread, pol_usd=None):
        loan_pct   = float(np.clip(action[0], 0, 1))
        bribe_mult = float(np.clip(action[1], 0, 3))

        max_loan   = reserves * 0.01
        loan_amt   = max_loan * loan_pct
        our_bribe  = gas_gwei * bribe_mult

        current_pol_usd = float(pol_usd) if (pol_usd is not None and pol_usd > 0) else POL_USD

        if spread <= TOTAL_FEE:
            if loan_pct > 0.01:
                return -250.0 # Heavy penalty for trading below 0.44% fee barrier
            else:
                return +10.0 # Reward for correctly ignoring unprofitable spread

        gross_profit = loan_amt * spread
        fee_cost     = loan_amt * TOTAL_FEE
        gas_cost_usd = (gas_gwei + our_bribe) * GAS_UNITS * 1e-9 * current_pol_usd
        net_profit   = gross_profit - fee_cost - gas_cost_usd

        if our_bribe >= comp_gwei:
            if net_profit > 0:
                return net_profit * 20.0  # Big reward for profitable trade
            else:
                return -400.0             # Won block but unprofitable
        else:
            failed_cost = gas_gwei * 200_000 * 1e-9 * current_pol_usd
            return -(failed_cost * 5 + 15)

    def sample(self):
        if self.idx >= len(self.raw_data):
            self.idx = 0
            np.random.shuffle(self.raw_data)
        row = self.raw_data[self.idx]
        self.idx += 1
        return self._row_to_obs(row)


# ─── Evolutionary Trainer ─────────────────────────────────────────────────────
class CombinedTrainer:
    def __init__(self, generations=150, episodes_per_gen=800):
        self.env         = CombinedStressEnv()
        self.generations = generations
        self.episodes    = episodes_per_gen
        self.best_loan_w = np.array([2.5, 1.2, -0.6, -0.4, 0.6])
        self.best_bribe_w= np.array([0.2, 0.3,  1.8,  2.2, 0.2])
        self.best_reward = -float("inf")
        self.log_file    = "real_training_log.jsonl"
        self.history     = []

    def get_action(self, obs, wl, wb):
        raw_loan  = np.dot(obs, wl)
        loan_pct  = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        raw_bribe = np.dot(obs, wb)
        bribe_mul = float(np.clip(raw_bribe, 0, 3))
        return [loan_pct, bribe_mul]

    def evaluate(self, wl, wb):
        total_reward = 0.0
        profitable   = 0
        unprofitable = 0
        for _ in range(self.episodes):
            obs, reserves, gas, comp, spread = self.env.sample()
            action = self.get_action(obs, wl, wb)
            r = self.env.step(action, obs, reserves, gas, comp, spread)
            total_reward += r
            if r > 0: profitable += 1
            else: unprofitable += 1
        return total_reward, profitable, unprofitable

    def train(self):
        print(f"\n  🏋️ Starting AI Evolutionary Retraining on Stress Test Data...\n")
        t0 = time.time()

        for gen in range(self.generations):
            sigma = max(0.03, 0.4 * (1 - gen / self.generations))
            noise_loan  = np.random.normal(0, sigma, 5)
            noise_bribe = np.random.normal(0, sigma, 5)

            test_wl = self.best_loan_w  + noise_loan
            test_wb = self.best_bribe_w + noise_bribe
            reward, prof, unprof = self.evaluate(test_wl, test_wb)

            if reward > self.best_reward:
                self.best_reward  = reward
                self.best_loan_w  = test_wl.copy()
                self.best_bribe_w = test_wb.copy()
                log = {
                    "generation": gen, "reward": float(reward),
                    "profitable_episodes": prof, "unprofitable_episodes": unprof,
                    "best_weights_loan":  test_wl.tolist(),
                    "best_weights_bribe": test_wb.tolist(),
                }
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log) + "\n")
                self.history.append(log)
                print(f"  🏆 Gen {gen:3d}: Reward={reward:>10.2f} | Profitable={prof:3d} | Unprofitable={unprof:3d} | σ={sigma:.3f}")
            elif gen % 20 == 0:
                elapsed = time.time() - t0
                print(f"  🔄 Gen {gen:3d}: Best={self.best_reward:>10.2f} | Elapsed={elapsed:.0f}s")

        elapsed = time.time() - t0
        print(f"\n  ✅ Training complete in {elapsed:.1f}s")
        print(f"  🏆 Best reward achieved: {self.best_reward:.2f}")
        return self.best_loan_w, self.best_bribe_w

    def save_weights(self, wl, wb):
        weights = {
            "loan_sizing_weights":   wl.tolist(),
            "dynamic_bribe_weights": wb.tolist(),
            "_metadata": {
                "version": "v3-stress-calibrated",
                "training_generations": self.generations,
                "dataset": "50K_historical + 7.8K_live_stress_scans",
                "gas_range_gwei": "50-500",
                "observation": ["spread_pct", "reserves_norm", "gas_norm", "competitor_norm", "pool_depth"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
        with open("real_trained_ai_weights.json", "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=4)
        print(f"  💾 Saved updated v3 weights to real_trained_ai_weights.json")

def main():
    print("=" * 65)
    print("  PHANTOM-X LIVE STRESS DATA AI RETRAINER")
    print("  Combining 50K Historical Data + 7.8K Live Stress Test Mainnet Scans")
    print("=" * 65)
    print()

    trainer = CombinedTrainer(generations=150, episodes_per_gen=800)
    best_wl, best_wb = trainer.train()
    trainer.save_weights(best_wl, best_wb)

    print("\n  ✅ Phase 3 Retraining Completed Successfully!\n")

if __name__ == "__main__":
    main()
