"""
PhantomX AI Live-Calibrated Retrainer
=======================================
Fixes 3 critical issues from diagnosis:
  [FIX-A] Training only ran 1 generation → run full 150
  [FIX-B] Training token was WMATIC → use normalized/token-agnostic features
  [FIX-C] Training gas was 30 Gwei → use real Polygon gas range (100-500 Gwei)
  [FIX-D] Gas cost formula updated to real Polygon economics
  [FIX-E] Reward function updated with real fee structure (Aave+QS+UV3)

Output: real_trained_ai_weights.json (overwritten with better weights)

Usage: python retrain_ai_live.py
"""
import json, sys, os, time
import numpy as np
from web3 import Web3

sys.stdout.reconfigure(encoding="utf-8")

# ─── Real-world constants (fixed from diagnosis) ─────────────────────────────
AAVE_FEE    = 0.0009   # 0.09%
QS_FEE      = 0.003    # 0.30%
UV3_FEE     = 0.0005   # 0.05%
TOTAL_FEE   = AAVE_FEE + QS_FEE + UV3_FEE   # 0.44%
GAS_UNITS   = 500_000  # realistic for our arbitrage contract
POL_USD     = 0.50     # approximate MATIC/POL price

# ─── Calibrated Training Environment ─────────────────────────────────────────
class CalibratedEnv:
    """
    Fixed training environment with real Polygon economics.

    Observation (5D) — ALL NORMALIZED, token-agnostic:
      [0] spread_pct          : 0.0 to 0.05 (0% to 5%)
      [1] reserves_usd_norm   : 0.0 to 1.0  ($0 to $10M, normalized)
      [2] gas_gwei_norm       : 0.0 to 1.0  (0 to 1000 Gwei, normalized)
      [3] competitor_norm     : 0.0 to 1.0  (relative bribe pressure)
      [4] pool_depth_norm     : 0.0 to 1.0  (pool quality signal)

    Key fixes from original:
    - No 'real_price' (WMATIC-specific) → replaced with pool_depth_norm
    - Gas normalized to real Polygon range (100-500 Gwei)
    - Loan capped at 1% of pool (not 0.5%)
    - Reward includes all 3 fee layers
    """
    def __init__(self, data_file="real_training_data_50k.jsonl"):
        self.raw_data = []
        with open(data_file) as f:
            for line in f:
                if line.strip():
                    self.raw_data.append(json.loads(line))
        print(f"  ✅ Loaded {len(self.raw_data):,} training rows")
        self.idx = 0
        np.random.shuffle(self.raw_data)  # Shuffle for better generalization

    def _row_to_obs(self, row):
        """Convert raw training row to normalized, token-agnostic observation."""
        spread   = row.get("real_spread_pct", 0)   # already fractional
        reserves = row.get("qs_usdc_reserves", 5e6)

        # [FIX-C] Scale gas from training range (30-38) → real range (100-500)
        raw_gas  = row.get("base_gas_fee_gwei", 30)
        real_gas = 100 + (raw_gas - 30) * (400/8)   # linear map: [30,38] → [100,500]
        real_gas = max(100, min(real_gas, 500))

        comp_bribe = row.get("competitor_bribe_gwei", 0)
        # Scale competitor bribe similarly
        real_comp  = comp_bribe * (real_gas / max(raw_gas, 1))

        # [FIX-B] Normalize all features (no raw WMATIC price!)
        obs = np.array([
            min(spread, 0.05),          # [0] spread (capped at 5%)
            min(reserves / 10_000_000, 1.0),  # [1] reserves normalized to $10M max
            min(real_gas / 500.0, 1.0),       # [2] gas normalized to 500 Gwei max
            min(real_comp / 500.0, 1.0),      # [3] competitor bribe normalized
            min(reserves / 10_000_000, 1.0),  # [4] pool depth signal (same as reserves here)
        ], dtype=np.float32)
        return obs, reserves, real_gas, real_comp

    def step(self, action, obs, reserves, real_gas, real_comp):
        """
        Evaluate one action. Returns reward.
        action = [loan_pct (0-1), bribe_mult (0-3)]
        """
        loan_pct   = float(np.clip(action[0], 0, 1))
        bribe_mult = float(np.clip(action[1], 0, 3))
        spread     = float(obs[0])  # already fractional

        our_bribe  = real_gas * bribe_mult
        max_loan   = reserves * 0.01    # 1% of pool
        loan_amt   = max_loan * loan_pct

        # [FIX-E] Realistic reward function with all fee layers
        if spread <= TOTAL_FEE:
            # Below break-even → penalize any trade attempt
            if loan_pct > 0.01:
                return -200.0   # Severe penalty for trading below break-even
            else:
                return +5.0     # Good: correctly refused unprofitable trade

        # Calculate P&L with real fees
        gross_profit  = loan_amt * spread
        fee_cost      = loan_amt * TOTAL_FEE
        # [FIX-D] Real gas cost formula
        gas_cost_usd  = (real_gas + our_bribe) * GAS_UNITS * 1e-9 * POL_USD
        net_profit    = gross_profit - fee_cost - gas_cost_usd

        # Gas war simulation
        if our_bribe >= real_comp:
            # Won the block
            if net_profit > 0:
                return net_profit * 15.0   # Big reward for profitable, won trade
            else:
                return -500.0              # Worst: won block but still lost money
        else:
            # Lost gas war
            failed_cost = real_gas * 200_000 * 1e-9 * POL_USD  # partial gas burn
            return -(failed_cost * 5 + 20)  # Penalty

    def sample(self):
        """Get next observation from dataset."""
        if self.idx >= len(self.raw_data):
            self.idx = 0
            np.random.shuffle(self.raw_data)
        row = self.raw_data[self.idx]
        self.idx += 1
        return self._row_to_obs(row)


# ─── Evolutionary Trainer ─────────────────────────────────────────────────────
class CalibratedTrainer:
    def __init__(self, generations=150, episodes_per_gen=800):
        self.env             = CalibratedEnv()
        self.generations     = generations
        self.episodes        = episodes_per_gen
        # [FIX-B] 5D weights matching new normalized observation space
        self.best_loan_w     = np.array([2.0, 1.0, -0.5, -0.5, 0.5])
        self.best_bribe_w    = np.array([0.1, 0.2,  2.0,  2.5, 0.1])
        self.best_reward     = -float("inf")
        self.log_file        = "real_training_log.jsonl"
        self.history         = []
        # Clear old log
        open(self.log_file, "w").close()
        print(f"  📋 Training: {generations} generations × {episodes_per_gen} episodes")
        print(f"  📋 Observation: 5D normalized (no WMATIC price bias)")
        print(f"  📋 Gas range: 100-500 Gwei (real Polygon)")

    def get_action(self, obs, wl, wb):
        raw_loan  = np.dot(obs, wl)
        loan_pct  = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        raw_bribe = np.dot(obs, wb)
        bribe_mul = float(np.clip(raw_bribe, 0, 3))
        return [loan_pct, bribe_mul]

    def evaluate(self, wl, wb):
        total_reward  = 0.0
        profitable    = 0
        unprofitable  = 0
        for _ in range(self.episodes):
            obs, reserves, gas, comp = self.env.sample()
            action = self.get_action(obs, wl, wb)
            r      = self.env.step(action, obs, reserves, gas, comp)
            total_reward += r
            if r > 0: profitable += 1
            else: unprofitable += 1
        return total_reward, profitable, unprofitable

    def train(self):
        print(f"\n  🏋️ Starting calibrated training...\n")
        t0 = time.time()

        for gen in range(self.generations):
            # Adaptive mutation — smaller noise as we converge
            sigma = max(0.05, 0.5 * (1 - gen / self.generations))
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
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(log) + "\n")
                self.history.append(log)
                print(f"  🏆 Gen {gen:3d}: Reward={reward:>10.2f} | Prof={prof:3d} | Unprof={unprof:3d} | σ={sigma:.3f}")
            elif gen % 15 == 0:
                elapsed = time.time() - t0
                print(f"  🔄 Gen {gen:3d}: Best={self.best_reward:>10.2f} | Elapsed={elapsed:.0f}s | σ={sigma:.3f}")

        elapsed = time.time() - t0
        print(f"\n  ✅ Training complete in {elapsed:.1f}s")
        print(f"  🏆 Best reward: {self.best_reward:.2f}")
        print(f"  📈 Improvements found: {len(self.history)}")
        return self.best_loan_w, self.best_bribe_w

    def save_weights(self, wl, wb):
        # Save v2 weights
        weights = {
            "loan_sizing_weights":  wl.tolist(),
            "dynamic_bribe_weights": wb.tolist(),
            "_metadata": {
                "version": "v2-calibrated",
                "training_generations": self.generations,
                "gas_range_gwei": "100-500",
                "observation": ["spread_pct", "reserves_norm", "gas_norm", "competitor_norm", "pool_depth"],
                "fixes": ["removed_wmatic_price_bias", "real_polygon_gas", "full_150gen", "real_fee_structure"],
            }
        }
        with open("real_trained_ai_weights.json", "w") as f:
            json.dump(weights, f, indent=4)
        print(f"  💾 Weights saved to real_trained_ai_weights.json")

        # Verify by loading
        with open("real_trained_ai_weights.json") as f:
            verify = json.load(f)
        assert len(verify["loan_sizing_weights"]) == 5
        print(f"  ✅ Weights verified: {verify['_metadata']['version']}")


def verify_new_ai_vs_old(new_wl, new_wb):
    """Compare new vs old weights on test scenarios."""
    print(f"\n  {'─'*60}")
    print(f"  VERIFICATION: New AI vs Old Weights")
    print(f"  {'─'*60}")

    # Load old weights
    old_wl = np.array([1.2063, 1.2349, -0.0691, -0.3209, -0.4295])
    old_wb = np.array([-0.0753, 0.2421, 1.3109, 1.4815, 0.2136])

    # Test scenarios (normalized)
    scenarios = [
        {"name": "Normal market (0.15% spread)", "obs": np.array([0.0015, 0.1, 0.55, 0.05, 0.1])},
        {"name": "Good opportunity (0.8% spread)", "obs": np.array([0.008,  0.3, 0.55, 0.05, 0.3])},
        {"name": "Excellent (2% spread)",         "obs": np.array([0.020,  0.5, 0.40, 0.10, 0.5])},
        {"name": "High gas (400 Gwei)",            "obs": np.array([0.008,  0.3, 0.80, 0.10, 0.3])},
    ]

    for sc in scenarios:
        obs = sc["obs"]
        # Old AI decision
        raw_old_loan  = np.dot(obs, old_wl)
        old_loan_pct  = 1 / (1 + np.exp(-raw_old_loan))
        # New AI decision
        raw_new_loan  = np.dot(obs, new_wl)
        new_loan_pct  = 1 / (1 + np.exp(-raw_new_loan))

        print(f"  Scenario: {sc['name']}")
        print(f"    Old AI loan%: {old_loan_pct:.3f} | New AI loan%: {new_loan_pct:.3f}")


def main():
    print("=" * 65)
    print("  PHANTOM-X LIVE-CALIBRATED AI RETRAINER v2")
    print("  Fixing: 1-gen training, WMATIC price bias, 9x gas mismatch")
    print("=" * 65)
    print()

    trainer = CalibratedTrainer(generations=150, episodes_per_gen=800)
    best_wl, best_wb = trainer.train()
    trainer.save_weights(best_wl, best_wb)
    verify_new_ai_vs_old(best_wl, best_wb)

    print(f"\n  {'═'*65}")
    print(f"  ✅ AI Retraining COMPLETE")
    print(f"  Run `python ai_diagnostic.py` again to verify improvement")
    print(f"  {'═'*65}\n")


if __name__ == "__main__":
    main()
