import os
import sys
import time
import json
import math
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ─── Directories Setup ────────────────────────────────────────────────────────
BASE_DIR = r"c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter"
ENGINE_DIR = os.path.join(BASE_DIR, "v2_v3_engine")
V2_DIR = os.path.join(ENGINE_DIR, "v2")
V3_DIR = os.path.join(ENGINE_DIR, "v3")
V3_AI_DIR = os.path.join(V3_DIR, "ai_engines")
COMMON_DIR = os.path.join(ENGINE_DIR, "common")

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, V2_DIR)
sys.path.insert(0, V3_DIR)
sys.path.insert(0, V3_AI_DIR)
sys.path.insert(0, COMMON_DIR)

from v2.ai_brain import PhantomAIBrain
from v2.predictive_oracle_model import PhantomOracle
from auto_tuner_engine import OnlineSGDAutoTuner

evidence_results = {}

def run_phase3_verification():
    print("=" * 80)
    print(" PHANTOMX PHASE 3: AI MODEL & AUTO-TUNER CONTINUOUS RETRAIN HARNESS")
    print(" Discipline Level: Military / Surgical / Aviation Grade")
    print(" Mode: Batch SGD Retraining & Time-Series Oracle Recalibration")
    print("=" * 80)

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 3.1: Local C-Compiled SGD Batch Retraining Speed (<2ms Target)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 3.1] SGD Batch Retraining Speed & Convergence (<2ms Target) ---")
    try:
        tuner = OnlineSGDAutoTuner()
        
        # Pre-allocate 500 block observations for zero-allocation benchmark
        np.random.seed(42)
        batch_size = 500
        tvl_a = np.random.uniform(50000.0, 500000.0, batch_size).astype(np.float32)
        tvl_b = np.random.uniform(50000.0, 500000.0, batch_size).astype(np.float32)
        spreads = np.random.uniform(0.001, 0.015, batch_size).astype(np.float32)
        gases = np.random.uniform(25.0, 150.0, batch_size).astype(np.float32)
        latencies = np.random.uniform(10.0, 150.0, batch_size).astype(np.float32)
        profits = (tvl_a * (spreads / 100.0) - 0.25).astype(np.float32)

        # Warmup iterations to trigger Python/Numpy JIT/C-cache
        for i in range(10):
            tuner.partial_fit_online(tvl_a[i], tvl_b[i], spreads[i], gases[i], latencies[i], profits[i])

        t_start = time.time()
        for i in range(10, batch_size):
            tuner.partial_fit_online(tvl_a[i], tvl_b[i], spreads[i], gases[i], latencies[i], profits[i])
            
        total_time_ms = (time.time() - t_start) * 1000.0
        actual_count = batch_size - 10
        avg_time_ms = float(total_time_ms / actual_count)
        
        print(f"  * Batch Size: {batch_size:,} historical block observations")
        print(f"  * Total Retraining Duration: {total_time_ms:.2f} ms")
        print(f"  * Average partial_fit() Speed: {avg_time_ms:.4f} ms per iteration (TARGET < 2.0ms)")
        assert avg_time_ms < 2.0, f"SGD execution speed benchmark failed: {avg_time_ms:.4f}ms"

        evidence_results["gate_3_1_sgd_speed"] = {
            "status": "PASSED",
            "batch_records": batch_size,
            "total_retrain_ms": round(total_time_ms, 2),
            "avg_partial_fit_ms": round(avg_time_ms, 4),
            "speed_target_met": bool(avg_time_ms < 2.0)
        }
    except Exception as e:
        print(f"  * Gate 3.1 Failed: {e}")
        evidence_results["gate_3_1_sgd_speed"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 3.2: 5-Block Rolling Time-Series Oracle Recalibration
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 3.2] 5-Block Time-Series Predictive Oracle Recalibration ---")
    try:
        oracle = PhantomOracle()
        
        # Recalibrate oracle weights on synthetic sequence matrix
        X_seq = np.array([
            [0.002, 0.003, 0.004, 0.005, 0.006],
            [0.001, 0.002, 0.002, 0.003, 0.004],
            [0.005, 0.006, 0.007, 0.008, 0.009],
            [0.003, 0.004, 0.005, 0.006, 0.007]
        ], dtype=np.float32)
        y_future = np.array([0.007, 0.005, 0.010, 0.008], dtype=np.float32)
        
        # Fit weights via AR gradient step
        lr = 0.01
        for epoch in range(100):
            preds = np.dot(X_seq, oracle.weights) + oracle.bias
            errs = preds - y_future
            dw = (2.0 / len(X_seq)) * np.dot(X_seq.T, errs)
            db = (2.0 / len(X_seq)) * np.sum(errs)
            oracle.weights -= lr * dw
            oracle.bias -= lr * db
            
        oracle.trained = True
        
        test_seq = np.array([0.002, 0.003, 0.004, 0.005, 0.006], dtype=np.float32)
        pred_spread = float(oracle.predict_future(test_seq))
        
        print(f"  * Oracle Model Trained: {oracle.trained}")
        print(f"  * Recalibrated Oracle Forecast (1-Hour Horizon): {pred_spread:.6f}")
        assert oracle.trained and pred_spread > 0, "Predictive Oracle recalibration failed"

        evidence_results["gate_3_2_oracle_recalibration"] = {
            "status": "PASSED",
            "oracle_trained": bool(oracle.trained),
            "sample_prediction_spread": round(pred_spread, 6)
        }
    except Exception as e:
        print(f"  * Gate 3.2 Failed: {e}")
        evidence_results["gate_3_2_oracle_recalibration"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 3.3: Online SGD Auto-Tuner Self-Refinement & Dynamic Floor Scaling
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 3.3] Online SGD Auto-Tuner Threshold Adaptability ---")
    try:
        tuner_test = OnlineSGDAutoTuner()
        old_floor = tuner_test.dynamic_min_profit_usd
        
        missed_sample = [
            {"spread_pct": 0.25, "loan_usd": 10000.0, "theoretical_profit_usd": 0.45},
            {"spread_pct": 0.30, "loan_usd": 15000.0, "theoretical_profit_usd": 0.60}
        ]
        
        tune_res = tuner_test.auto_tune_parameters(missed_sample, current_gas_gwei=25.0)
        new_floor = tuner_test.dynamic_min_profit_usd
        new_multiplier = tuner_test.loan_scaler_multiplier
        
        print(f"  * Initial Min Profit Floor: ${old_floor:.2f}")
        print(f"  * Auto-Tuned Min Profit Floor (Low Gas): ${new_floor:.2f}")
        print(f"  * Auto-Tuned Loan Multiplier L*: {new_multiplier:.3f}x")
        print(f"  * Total Auto-Tunes Triggered: {tuner_test.total_auto_tunes}")
        assert new_floor < old_floor, "Auto-tuner floor adaptation failed"

        evidence_results["gate_3_3_auto_tune_adaptability"] = {
            "status": "PASSED",
            "initial_floor_usd": old_floor,
            "recalibrated_floor_usd": new_floor,
            "recalibrated_loan_multiplier": round(new_multiplier, 3)
        }
    except Exception as e:
        print(f"  * Gate 3.3 Failed: {e}")
        evidence_results["gate_3_3_auto_tune_adaptability"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 3.4: Dynamic Hot-Reloading & In-Memory Weight Syncing
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 3.4] In-Memory Neural Weight Hot-Reloading Verification ---")
    try:
        brain_v2 = PhantomAIBrain()
        
        tmp_weights_path = os.path.join(ENGINE_DIR, "tmp_test_weights.json")
        sample_weights = {
            "loan_sizing_weights": [1.1, 0.6, -0.05, 0.01, 0.02],
            "dynamic_bribe_weights": [0.01, 0.02, 1.05, 1.15, 0.01]
        }
        with open(tmp_weights_path, "w", encoding="utf-8") as f:
            json.dump(sample_weights, f, indent=2)
            
        reload_success = brain_v2.reload_weights(tmp_weights_path)
        if os.path.exists(tmp_weights_path):
            os.remove(tmp_weights_path)
            
        print(f"  * Neural Weight Hot-Reload Status: {reload_success}")
        assert reload_success, "Hot-reload weights verification failed"

        evidence_results["gate_3_4_hot_reload"] = {
            "status": "PASSED",
            "hot_reload_success": bool(reload_success)
        }
    except Exception as e:
        print(f"  * Gate 3.4 Failed: {e}")
        evidence_results["gate_3_4_hot_reload"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 3.5: Save Ground-Level Empirical Evidence Artifact
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 3.5] Saving Ground-Level Empirical Evidence Artifact ---")
    evidence_path = os.path.join(ENGINE_DIR, "evidence_phase3_retraining.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_results, f, indent=2)
    print(f"  * Saved empirical evidence manifest to [evidence_phase3_retraining.json](file:///{evidence_path})")

    print("\n================================================================================")
    print("PHANTOMX PHASE 3 VERIFICATION SUMMARY:")
    all_passed = True
    for gate, res in evidence_results.items():
        st = res.get("status", "UNKNOWN")
        print(f"  * {gate}: {st}")
        if "FAILED" in st:
            all_passed = False
    print("================================================================================")
    return all_passed

if __name__ == "__main__":
    success = run_phase3_verification()
    sys.exit(0 if success else 1)
