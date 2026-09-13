"""
PhantomX Real-Data Calibrated Evolutionary AI Brain Trainer
===========================================================
Trains AI Brain weights on 100% REAL Polygon Mainnet Data:
  - Fresh live real RPC scans (live_real_rpc_scans.jsonl)
  - 50,000 historical mainnet block records (real_training_data_50k.jsonl)
  - Multi-pair scenarios: WETH, WMATIC (POL), WBTC across Aave v3, QuickSwap v2, Uniswap v3

Economic Parameters:
  - Fee barrier: 0.44% (Aave 0.09% + QS 0.30% + UV3 0.05%)
  - Dynamic Gas Math: 500,000 gas * (base_gas + bribe) * 1e-9 * POL_USD
  - Dynamic Target Threshold: $0.50 USD
"""

import os
import sys
import json
import time
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

TOTAL_FEE_PCT = 0.0044  # 0.44%
GAS_UNITS = 500_000
MIN_PROFIT_USD = 0.50   # $0.50 threshold

class RealRpcEnv:
    def __init__(self, live_file="live_real_rpc_scans.jsonl", historical_file="real_training_data_50k.jsonl"):
        self.raw_scenarios = []

        # 1. Load live real RPC scans
        live_count = 0
        if os.path.exists(live_file):
            with open(live_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        scan = json.loads(line)
                        base_gas = scan.get("base_gas_gwei", 30.0)
                        pol_usd = scan.get("pol_usd", 0.45)
                        pairs = scan.get("pairs", {})
                        for sym, pdata in pairs.items():
                            spread_pct = pdata.get("spread_pct", 0) / 100.0
                            qs_reserves = pdata.get("qs_usdc_reserves", 500000)
                            if qs_reserves <= 0:
                                qs_reserves = 500000
                            self.raw_scenarios.append({
                                "spread_pct": spread_pct,
                                "reserves_usd": qs_reserves,
                                "gas_gwei": base_gas,
                                "pol_usd": pol_usd,
                                "competitor_gwei": 0.0,
                                "symbol": sym,
                                "source": "LIVE_RPC"
                            })
                            live_count += 1
            print(f"  ✅ Loaded {live_count} live pair scans from {live_file}")

        # 2. Load historical 50K mainnet records
        hist_count = 0
        if os.path.exists(historical_file):
            with open(historical_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        spread_pct = row.get("real_spread_pct", 0)
                        qs_reserves = row.get("qs_usdc_reserves", 5000000)
                        base_gas = row.get("base_gas_fee_gwei", 275.0)
                        pol_usd = row.get("pol_usd", 0.50)
                        self.raw_scenarios.append({
                            "spread_pct": spread_pct,
                            "reserves_usd": qs_reserves,
                            "gas_gwei": base_gas,
                            "pol_usd": pol_usd,
                            "competitor_gwei": row.get("competitor_bribe_gwei", 0.0),
                            "symbol": "HISTORICAL",
                            "source": "MAINNET_50K"
                        })
                        hist_count += 1
            print(f"  ✅ Loaded {hist_count:,} historical 50K mainnet records")

        print(f"  📊 Total Combined Real Dataset: {len(self.raw_scenarios):,} scenarios")
        np.random.shuffle(self.raw_scenarios)

    def _scenario_to_obs(self, sc):
        spread = sc["spread_pct"]
        reserves = sc["reserves_usd"]
        gas_gwei = max(10.0, min(sc["gas_gwei"], 1000.0))
        comp_gwei = sc["competitor_gwei"]

        obs = np.array([
            min(spread, 0.05),
            min(reserves / 10_000_000, 1.0),
            min(gas_gwei / 500.0, 1.0),
            min(comp_gwei / 500.0, 1.0),
            min(reserves / 10_000_000, 1.0)
        ], dtype=np.float32)

        return obs, reserves, gas_gwei, comp_gwei, spread, sc.get("pol_usd", 0.45)

def evaluate_chromosome(w_loan, w_bribe, scenarios):
    total_pnl = 0.0
    correct = 0
    false_positives = 0
    false_negatives = 0

    for sc in scenarios:
        spread = sc["spread_pct"]
        reserves = sc["reserves_usd"]
        gas_gwei = sc["gas_gwei"]
        comp_gwei = sc["competitor_gwei"]
        pol_usd = sc.get("pol_usd", 0.45)

        obs = np.array([
            min(spread, 0.05),
            min(reserves / 10_000_000, 1.0),
            min(gas_gwei / 500.0, 1.0),
            min(comp_gwei / 500.0, 1.0),
            min(reserves / 10_000_000, 1.0)
        ], dtype=np.float32)

        # Loan sizing
        raw_loan = np.dot(obs, w_loan)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0.0

        # Bribe multiplier
        raw_bribe = np.dot(obs, w_bribe)
        bribe_mult = min(max(raw_bribe, 0.0), 2.0)

        # Ground truth P&L math
        max_safe_borrow = reserves * 0.01
        optimal_loan = max_safe_borrow * loan_pct
        bribe_gwei = gas_gwei * bribe_mult

        gross_usd = optimal_loan * spread
        fee_usd = optimal_loan * TOTAL_FEE_PCT
        gas_usd = (gas_gwei + bribe_gwei) * GAS_UNITS * 1e-9 * pol_usd

        actual_net = gross_usd - fee_usd - gas_usd

        # Decision
        executed = (loan_pct > 0.01) and (actual_net >= MIN_PROFIT_USD)

        # Ground truth best possible profit
        best_possible_borrow = max_safe_borrow
        best_gross = best_possible_borrow * spread
        best_fee = best_possible_borrow * TOTAL_FEE_PCT
        best_gas = (gas_gwei) * GAS_UNITS * 1e-9 * pol_usd
        best_possible_net = best_gross - best_fee - best_gas
        should_execute = best_possible_net >= MIN_PROFIT_USD

        if executed and actual_net > 0:
            total_pnl += actual_net
            correct += 1
        elif executed and actual_net <= 0:
            total_pnl += actual_net * 2.0  # Double penalty for loss
            false_positives += 1
        elif not executed and should_execute:
            total_pnl -= 5.0  # Penalty for missed opportunity
            false_negatives += 1
        else:
            correct += 1

    fitness = total_pnl - (false_positives * 50.0) - (false_negatives * 5.0)
    return fitness, total_pnl, correct, false_positives, false_negatives

def train_evolutionary():
    print("🧬 Starting Calibrated Evolutionary AI Brain Retraining on 100% REAL Data...")
    start_time = time.time()

    env = RealRpcEnv()
    if len(env.raw_scenarios) == 0:
        print("❌ Dataset empty! Cannot train.")
        return False

    pop_size = 100
    generations = 150
    subset_size = min(5000, len(env.raw_scenarios))
    training_sample = env.raw_scenarios[:subset_size]

    # Initialize Population
    np.random.seed(42)
    pop_loan = np.random.uniform(-1.0, 1.0, (pop_size, 5))
    pop_bribe = np.random.uniform(0.0, 1.5, (pop_size, 5))

    best_fitness = -float('inf')
    best_w_loan = None
    best_w_bribe = None
    best_pnl = 0.0

    print(f"\n🔄 Running {generations} Evolutionary Generations across {subset_size:,} real scenarios...")

    for gen in range(1, generations + 1):
        fitnesses = []
        pnls = []
        for i in range(pop_size):
            fit, pnl, corr, fp, fn = evaluate_chromosome(pop_loan[i], pop_bribe[i], training_sample)
            fitnesses.append(fit)
            pnls.append(pnl)

        fitnesses = np.array(fitnesses)
        best_idx = np.argmax(fitnesses)

        if fitnesses[best_idx] > best_fitness:
            best_fitness = fitnesses[best_idx]
            best_w_loan = pop_loan[best_idx].copy()
            best_w_bribe = pop_bribe[best_idx].copy()
            best_pnl = pnls[best_idx]

        if gen % 15 == 0 or gen == 1 or gen == generations:
            avg_fit = np.mean(fitnesses)
            print(f"  🧬 Gen {gen:03d}/{generations} | Best Fitness: {best_fitness:.2f} | Best PnL: ${best_pnl:.2f} | Avg Fit: {avg_fit:.2f}")

        # Selection (Top 20%)
        top_k = int(pop_size * 0.2)
        survivor_indices = np.argsort(fitnesses)[-top_k:]

        new_loan = [pop_loan[idx].copy() for idx in survivor_indices]
        new_bribe = [pop_bribe[idx].copy() for idx in survivor_indices]

        # Crossover & Mutation to refill population
        while len(new_loan) < pop_size:
            p1, p2 = np.random.choice(survivor_indices, 2, replace=False)
            alpha = np.random.rand()
            child_loan = alpha * pop_loan[p1] + (1 - alpha) * pop_loan[p2]
            child_bribe = alpha * pop_bribe[p1] + (1 - alpha) * pop_bribe[p2]

            # Mutation (15% chance)
            if np.random.rand() < 0.15:
                child_loan += np.random.normal(0, 0.1, 5)
            if np.random.rand() < 0.15:
                child_bribe += np.random.normal(0, 0.1, 5)

            new_loan.append(child_loan)
            new_bribe.append(child_bribe)

        pop_loan = np.array(new_loan)
        pop_bribe = np.array(new_bribe)

    elapsed = time.time() - start_time
    print(f"\n=================================================")
    print(f"🏆 EVOLUTIONARY TRAINING COMPLETE IN {elapsed:.2f}s")
    print(f"🎯 Best Fitness: {best_fitness:.2f} | Peak Training PnL: ${best_pnl:.2f}")
    print(f"⚖️ Trained Loan Weights:  {best_w_loan.tolist()}")
    print(f"⚖️ Trained Bribe Weights: {best_w_bribe.tolist()}")

    # Save to real_trained_ai_weights.json
    output_path = "real_trained_ai_weights.json"
    weights_payload = {
        "timestamp": int(time.time()),
        "model_version": "PhantomX_AGI_v3.0_RealRPC",
        "loan_sizing_weights": best_w_loan.tolist(),
        "dynamic_bribe_weights": best_w_bribe.tolist(),
        "best_fitness": round(float(best_fitness), 2),
        "peak_pnl_usd": round(float(best_pnl), 2),
        "training_scenarios": len(env.raw_scenarios),
        "min_net_profit_usd": MIN_PROFIT_USD,
        "protocol_fee_pct": TOTAL_FEE_PCT
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(weights_payload, f, indent=2)

    print(f"💾 Updated weights saved to: {output_path}")
    return True

if __name__ == "__main__":
    train_evolutionary()
