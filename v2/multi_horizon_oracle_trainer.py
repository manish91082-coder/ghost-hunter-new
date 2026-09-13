"""
PhantomX Level 5 Multi-Horizon Time-Series Predictive Forecasting Engine
======================================================================
Trains the PhantomOracle model to predict market volatility and spread
widenings across 4 distinct advance time horizons:
  - Horizon 1h: 1-Hour Forecast (12 blocks ahead)
  - Horizon 2h: 2-Hour Forecast (24 blocks ahead)
  - Horizon 3h: 3-Hour Forecast (36 blocks ahead)
  - Horizon 24h: 24-Hour Forecast (288 blocks ahead)

Data Source: 106,000+ real sequential Polygon mainnet records.
Output: multi_horizon_oracle_weights.json
"""

import os
import sys
import json
import time
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

HORIZONS = {
    "1h":  {"blocks": 12,  "label": "1-Hour Forecast"},
    "2h":  {"blocks": 24,  "label": "2-Hour Forecast"},
    "3h":  {"blocks": 36,  "label": "3-Hour Forecast"},
    "24h": {"blocks": 288, "label": "24-Hour Forecast"}
}

class MultiHorizonOracleTrainer:
    def __init__(self, history_file="sanitized_1yr_data.jsonl"):
        self.history_file = history_file
        self.data = []
        self.lookback = 5

    def load_data(self):
        print("🧠 [Multi-Horizon Oracle] Loading sanitized sequential dataset...")
        if not os.path.exists(self.history_file):
            print(f"❌ File not found: {self.history_file}")
            return False

        with open(self.history_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.data.append(json.loads(line))

        print(f"  ✅ Loaded {len(self.data):,} sequential mainnet records")
        return True

    def train_horizon(self, horizon_key, target_blocks, epochs=60, lr=0.01):
        spreads = [row.get("real_spread_pct", 0.0) for row in self.data]
        n_samples = len(spreads)

        X, y = [], []
        for i in range(n_samples - self.lookback - target_blocks):
            X.append(spreads[i : i + self.lookback])
            y.append(spreads[i + self.lookback + target_blocks - 1])

        X = np.array(X, dtype=np.float64)
        y = np.array(y, dtype=np.float64)

        if len(X) == 0:
            print(f"⚠️ No samples for horizon {horizon_key}")
            return None, None, 0.0

        weights = np.random.randn(self.lookback) * 0.1
        bias = np.random.randn(1) * 0.1

        for epoch in range(epochs):
            predictions = np.dot(X, weights) + bias
            errors = predictions - y

            dw = (2.0 / len(X)) * np.dot(X.T, errors)
            db = (2.0 / len(X)) * np.sum(errors)

            weights -= lr * dw
            bias -= lr * db

        final_preds = np.dot(X, weights) + bias
        mse = float(np.mean((final_preds - y) ** 2))

        # Directional Accuracy %
        actual_dirs = np.sign(y - X[:, -1])
        pred_dirs = np.sign(final_preds - X[:, -1])
        directional_acc = float(np.mean(actual_dirs == pred_dirs) * 100.0)

        print(f"  🔮 [{horizon_key.upper()} - {HORIZONS[horizon_key]['label']}] MSE: {mse:.6f} | Directional Accuracy: {directional_acc:.2f}%")
        return weights.tolist(), float(bias[0]), directional_acc

    def train_all_horizons(self):
        if not self.load_data():
            return False

        print(f"\n🔮 Training Multi-Horizon Predictive Time-Series Forecasting Models...")
        start_time = time.time()

        horizon_results = {}
        for h_key, h_info in HORIZONS.items():
            w, b, acc = self.train_horizon(h_key, h_info["blocks"])
            if w is not None:
                horizon_results[h_key] = {
                    "horizon_label": h_info["label"],
                    "target_blocks_ahead": h_info["blocks"],
                    "weights": w,
                    "bias": b,
                    "directional_accuracy_pct": round(acc, 2)
                }

        elapsed = time.time() - start_time
        print(f"\n=================================================")
        print(f"🏆 MULTI-HORIZON ORACLE TRAINING COMPLETE IN {elapsed:.2f}s")

        output_payload = {
            "timestamp": int(time.time()),
            "model_version": "PhantomOracle_MultiHorizon_v5.0",
            "historical_records_trained": len(self.data),
            "lookback_periods": self.lookback,
            "horizons": horizon_results
        }

        output_path = "multi_horizon_oracle_weights.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

        print(f"💾 Multi-horizon weights saved to: {output_path}")
        return True

if __name__ == "__main__":
    trainer = MultiHorizonOracleTrainer()
    trainer.train_all_horizons()
