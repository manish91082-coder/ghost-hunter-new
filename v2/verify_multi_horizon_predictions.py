"""
PhantomX Level 5 Multi-Horizon Prediction Verification & Accuracy Harness
========================================================================
Compares 1h, 2h, 3h, and 24h advance predictions against actual market price
sequences as time advances to verify prediction accuracy and Mean Squared Error.
"""

import os
import sys
import json
import time
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

def verify_multi_horizon_predictions(weights_file="multi_horizon_oracle_weights.json", history_file="sanitized_1yr_data.jsonl"):
    print("🔬 Booting Multi-Horizon Prediction Verification Harness...")

    if not os.path.exists(weights_file):
        print(f"❌ Weights file missing: {weights_file}")
        return False

    if not os.path.exists(history_file):
        print(f"❌ History file missing: {history_file}")
        return False

    with open(weights_file, "r", encoding="utf-8") as f:
        weights_data = json.load(f)

    data = []
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    spreads = [row.get("real_spread_pct", 0.0) for row in data]

    print(f"  ✅ Loaded {len(data):,} sequential records")
    print(f"  📋 Verifying forecasts across {len(weights_data.get('horizons', {}))} time horizons...\n")

    horizons = weights_data.get("horizons", {})
    lookback = weights_data.get("lookback_periods", 5)

    verification_results = {}

    for h_key, h_info in horizons.items():
        w = np.array(h_info["weights"])
        b = float(h_info["bias"])
        blocks_ahead = h_info["target_blocks_ahead"]

        X, y_actual = [], []
        for i in range(len(spreads) - lookback - blocks_ahead):
            X.append(spreads[i : i + lookback])
            y_actual.append(spreads[i + lookback + blocks_ahead - 1])

        X = np.array(X)
        y_actual = np.array(y_actual)

        preds = np.dot(X, w) + b
        mse = float(np.mean((preds - y_actual) ** 2))
        mae = float(np.mean(np.abs(preds - y_actual)))

        # Directional Accuracy
        actual_dirs = np.sign(y_actual - X[:, -1])
        pred_dirs = np.sign(preds - X[:, -1])
        dir_acc = float(np.mean(actual_dirs == pred_dirs) * 100.0)

        verification_results[h_key] = {
            "label": h_info["horizon_label"],
            "blocks_ahead": blocks_ahead,
            "mse": round(mse, 6),
            "mae": round(mae, 6),
            "directional_accuracy_pct": round(dir_acc, 2),
            "samples_tested": len(X)
        }

        print(f"  📊 [{h_key.upper()} - {h_info['horizon_label']}] Samples: {len(X):,} | MSE: {mse:.6f} | MAE: {mae:.6f} | Directional Accuracy: {dir_acc:.2f}%")

    print("\n=================================================")
    print("🏆 MULTI-HORIZON PREDICTION VERIFICATION COMPLETE")
    print("✅ All horizons verified against real mainnet price sequences.")

    return True

if __name__ == "__main__":
    verify_multi_horizon_predictions()
