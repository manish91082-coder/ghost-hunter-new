"""
PhantomX v3 Universal Profit Engine - Live Real-Time Online Weight Tuner (ai_engines/live_online_tuner_v3.py)
================================================================================================================
Updates 1D CNN + Horizon Oracle neural weights dynamically on live Polygon Mainnet block streams.
Features:
  - Online Gradient Descent Weight Adaptation (Learning Rate alpha = 0.01)
  - Real-Time Prediction Error Tracking (MSE Tracking)
  - State Persistence in `logs/live_online_tuner_state_v3.json`
"""

import sys
import os
import time
import json
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.join(os.path.dirname(__file__)))

from horizon_oracle import TimeSeriesHorizonOracle

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "live_online_tuner_state_v3.json")

class LiveOnlineWeightTunerV3:
    """
    Adapts Horizon Oracle neural weights dynamically on live mainnet streams.
    """
    def __init__(self, learning_rate=0.01):
        self.oracle = TimeSeriesHorizonOracle()
        self.alpha = learning_rate
        self.update_count = 0
        self.total_mse_loss = 0.0
        self.load_state()

    def update_weights_on_live_block(self, spread_history_5: list, actual_next_spread: float) -> dict:
        """
        Performs online gradient descent step on live block observation.
        """
        if len(spread_history_5) < 5:
            return {"updated": False}

        pred_spread = self.oracle.predict_future_spread(spread_history_5)
        error = actual_next_spread - pred_spread

        # Gradient update on rolling weights w
        history_arr = np.array(spread_history_5[-5:], dtype=np.float32)
        grad_w = error * history_arr
        self.oracle.weights += self.alpha * grad_w
        self.oracle.bias += self.alpha * error

        # Clip weights to positive bounds for stability
        self.oracle.weights = np.clip(self.oracle.weights, 0.01, 1.0)

        self.update_count += 1
        self.total_mse_loss += error ** 2
        avg_mse = self.total_mse_loss / max(self.update_count, 1)

        if self.update_count % 50 == 0:
            self.save_state()

        return {
            "updated": True,
            "pred_spread": round(float(pred_spread), 4),
            "actual_spread": round(float(actual_next_spread), 4),
            "error": round(float(error), 4),
            "avg_mse_loss": round(float(avg_mse), 6),
            "update_count": self.update_count
        }

    def save_state(self):
        try:
            state = {
                "weights": [round(float(w), 4) for w in self.oracle.weights],
                "bias": round(float(self.oracle.bias), 4),
                "update_count": self.update_count,
                "avg_mse_loss": round(float(self.total_mse_loss / max(self.update_count, 1)), 6),
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving tuner state: {e}")

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    if "weights" in state:
                        self.oracle.weights = np.array(state["weights"], dtype=np.float32)
                    if "bias" in state:
                        self.oracle.bias = float(state["bias"])
                    self.update_count = state.get("update_count", 0)
                    print(f"🔄 [Live Online Tuner v3] Loaded online state (Updates: {self.update_count:,} | MSE: {state.get('avg_mse_loss', 0):.6f})")
            except Exception as e:
                print(f"⚠️ Error loading tuner state: {e}")

if __name__ == "__main__":
    tuner = LiveOnlineWeightTunerV3()
    print("🧠 Live Real-Time Online Weight Tuner v3 Initialized")
    sample_hist = [0.12, 0.14, 0.15, 0.18, 0.22]
    res = tuner.update_weights_on_live_block(sample_hist, 0.25)
    print(f"Tuner Result: {res}")
