"""
PhantomX Automated Live Learning & Hot-Reload Loop
===================================================
Monitors raw mainnet scans, periodically retrains AI neural weights,
and triggers dynamic in-memory weight hot-reloading.

Usage: python auto_retrain_loop.py
"""
import os
import sys
import time
import subprocess
from ai_brain import PhantomAIBrain

sys.stdout.reconfigure(encoding="utf-8")

class AutoRetrainLoop:
    def __init__(self, raw_scans_file="stress_test_20260905_204526/raw_scans.jsonl", check_interval_sec=30):
        self.raw_scans_file = raw_scans_file
        self.check_interval_sec = check_interval_sec
        self.last_scans_count = 0
        self.brain = PhantomAIBrain()

    def count_scans(self):
        if not os.path.exists(self.raw_scans_file):
            return 0
        with open(self.raw_scans_file, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def run_retrain_cycle(self):
        current_count = self.count_scans()
        print(f"\n📡 [Auto-Retrain Monitor] Current Scans Count: {current_count:,}")

        if current_count > self.last_scans_count:
            new_scans = current_count - self.last_scans_count
            print(f"🔄 Detected {new_scans} new live mainnet scans! Triggering evolutionary retraining...")
            
            # Execute retrain_from_stress_data.py
            cmd = [sys.executable, "retrain_from_stress_data.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=os.path.dirname(__file__))

            if result.returncode == 0:
                print("✅ Retraining complete! Hot-reloading AI weights into memory...")
                reloaded = self.brain.reload_weights()
                if reloaded:
                    print(f"🎉 Dynamic AI Weights Hot-Reloaded! New Loan Weights: {self.brain.weights_loan.round(4).tolist()}")
                    self.last_scans_count = current_count
                    return True
            else:
                print(f"❌ Retraining failed: {result.stderr}")
        else:
            print("⏳ No new scans detected yet.")
        return False

def main():
    print("=" * 60)
    print("  PHANTOM-X AUTOMATED LIVE LEARNING & HOT-RELOAD LOOP")
    print("=" * 60)
    
    loop = AutoRetrainLoop()
    print("\nRunning single automated retraining & hot-reload verification cycle...")
    success = loop.run_retrain_cycle()
    if success:
        print("\n✅ Phase 5 Automated Live Learning & Hot-Reload Loop Verified!")

if __name__ == "__main__":
    main()
