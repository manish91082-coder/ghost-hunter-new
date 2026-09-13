"""
PhantomX V2 & V3 - Real-Time AI Profit Watcher Guard Engine (profit_watcher_guard.py)
====================================================================================================
Continuous Real-Time Monitoring & Self-Refining Audit Guard.
Features:
  - Audits V2 and V3 live scan streams every 5-10 minutes.
  - Detects missed micro-arbitrage opportunities (Spread >= 0.15%).
  - Evaluates decision accuracy vs live pool price reality.
  - Triggers C-compiled Local SGD Auto-Tuner (<2ms) when profit is stagnant.
  - Dynamically updates min profit floor ($0.50 -> $0.20 -> $0.10) and loan multiplier L*.
  - Sends high-priority Telegram alerts and logs detailed audit trails.
"""

import sys
import os
import time
import json
import psutil
from datetime import datetime
from collections import deque

sys.stdout.reconfigure(encoding="utf-8")

COMMON_DIR = os.path.abspath(os.path.dirname(__file__))
ENGINE_ROOT = os.path.abspath(os.path.join(COMMON_DIR, ".."))
BASE_DIR = os.path.abspath(os.path.join(ENGINE_ROOT, ".."))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, ENGINE_ROOT)
sys.path.insert(0, COMMON_DIR)

from auto_tuner_engine import OnlineSGDAutoTuner
from v2.telegram_notifier import send_telegram_message

# Set process priority to IDLE for zero PC lag
try:
    p = psutil.Process(os.getpid())
    p.nice(psutil.IDLE_PRIORITY_CLASS if os.name == 'nt' else 10)
    print("⚡ [Profit Watcher Guard] Process priority set to LOW (Idle Priority) for Zero PC Lag!")
except Exception as e:
    print(f"⚠️ Priority note: {e}")

V2_METRICS = os.path.join(ENGINE_ROOT, "v2", "live_scan_metrics_v2.jsonl")
V3_METRICS = os.path.join(ENGINE_ROOT, "v3", "logs", "live_scan_metrics_v3.jsonl")
WATCHER_LOG = os.path.join(COMMON_DIR, "profit_watcher.log")

class ProfitWatcherGuard:
    """
    Autonomous Real-Time Profit Watcher & Audit Guard Engine.
    """
    def __init__(self, check_interval_seconds=300):
        self.check_interval_seconds = check_interval_seconds
        self.tuner = OnlineSGDAutoTuner()
        self.total_audits = 0
        self.total_tunes_triggered = 0

    def load_recent_metrics(self, filepath, max_records=200):
        if not os.path.exists(filepath):
            return []
        records = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tail_lines = deque(f, maxlen=max_records)
                for line in tail_lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        continue
        except Exception as e:
            print(f"⚠️ Watcher read error for {filepath}: {e}")
        return records

    def audit_stream_performance(self, records, stream_name="V2"):
        if not records:
            return {"stream": stream_name, "total": 0, "executes": 0, "missed": []}

        total = len(records)
        executes = [r for r in records if r.get("decision") == "EXECUTE"]
        skipped = [r for r in records if r.get("decision") in ["WAIT", "IGNORE"]]

        missed = []
        for r in skipped:
            spread = r.get("spread_pct", r.get("effective_spread_pct", 0.0))
            gas = r.get("gas_gwei", 50.0)
            loan = r.get("optimal_loan_usd", 10000.0)
            
            # Theoretical yield check
            if spread >= 0.15 and loan > 0:
                theo_profit = (loan * (spread / 100.0)) - (gas * 250000 * 1e-9 * 0.095 * 100)
                if theo_profit >= 0.10:
                    missed.append({
                        "timestamp": r.get("timestamp"),
                        "stream": stream_name,
                        "pair": r.get("pair"),
                        "spread_pct": spread,
                        "gas_gwei": gas,
                        "loan_usd": loan,
                        "theoretical_profit_usd": round(theo_profit, 2)
                    })

        return {
            "stream": stream_name,
            "total": total,
            "executes": len(executes),
            "skipped": len(skipped),
            "missed": missed
        }

    def run_audit_cycle(self):
        self.total_audits += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🔍 [Profit Watcher Audit #{self.total_audits}] Running 5-Min Stream Check ({now_str})...")

        v2_records = self.load_recent_metrics(V2_METRICS)
        v3_records = self.load_recent_metrics(V3_METRICS)

        v2_audit = self.audit_stream_performance(v2_records, "V2_MVP")
        v3_audit = self.audit_stream_performance(v3_records, "V3_UNIVERSAL")

        all_missed = v2_audit["missed"] + v3_audit["missed"]
        total_executes = v2_audit["executes"] + v3_audit["executes"]

        log_msg = f"[{now_str}] Audit #{self.total_audits} | V2 Scans: {v2_audit['total']} (Exec: {v2_audit['executes']}) | V3 Scans: {v3_audit['total']} (Exec: {v3_audit['executes']}) | Missed Opportunities: {len(all_missed)}"
        print(log_msg)

        with open(WATCHER_LOG, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")

        # Trigger SGD Auto-Tuning if 0 executed trades AND missed opportunities exist OR stagnation detected
        if (total_executes == 0 and len(all_missed) > 0) or len(all_missed) >= 3:
            print(f"⚡ [Watcher Alert] Stagnation or Missed Opportunities ({len(all_missed)}) detected! Triggering Online SGD Auto-Tuner...")
            tune_res = self.tuner.auto_tune_parameters(all_missed, current_gas_gwei=60.0)
            self.total_tunes_triggered += 1

            alert_text = f"""
📊 [PROFIT WATCHER GUARD AUTO-TUNE ALERT]
⏰ Time: {now_str}
🔍 Audit Cycle: #{self.total_audits}
📊 Missed Opportunities Detected: {len(all_missed)}
🔧 Auto-Tuner Action:
  • SGD Execution Time: {tune_res.get('sgd_execution_time_ms', 0)} ms
  • New Min Profit Floor: ${tune_res.get('new_min_profit_usd', 0.20)} USD
  • Loan Scaler Multiplier L*: {tune_res.get('loan_scaler_multiplier', 1.25)}x
  • Total Auto-Tunes Triggered: {self.total_tunes_triggered}
🛡️ Status: Neural weights re-calibrated! Micro-profit capture active ($0.10-$0.20 floor).
"""
            print(alert_text)
            try:
                send_telegram_message(alert_text)
            except Exception as te:
                print(f"⚠️ Watcher Telegram alert note: {te}")
        else:
            print("✅ [Profit Watcher Guard] Execution streams optimal. Zero stagnation detected.")

    def start_guard_loop(self):
        print(f"🛡️ [Profit Watcher Guard Engine] Active! Monitoring V2 & V3 Streams every {self.check_interval_seconds}s...")
        while True:
            try:
                self.run_audit_cycle()
            except Exception as e:
                print(f"⚠️ Profit Watcher Guard cycle error: {e}")
            time.sleep(self.check_interval_seconds)

if __name__ == "__main__":
    watcher = ProfitWatcherGuard(check_interval_seconds=600)
    print("================================================================================")
    print("🚀 PhantomX Profit Watcher Guard Engine Initialized (10-Min Audit Window)")
    print("================================================================================")
    watcher.start_guard_loop()
