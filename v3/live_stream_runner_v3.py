"""
PhantomX V3 Universal Engine Stream Runner (phantomx_v3_universal_engine/live_stream_runner_v3.py)
===============================================================================================
Subscribes to Central Live Block Stream (`data/central_live_block_stream.jsonl`)
Evaluates 5 Ensembled AI Brains + Real-Time Online Weight Tuner V3 without duplicate RPC calls.
Features:
  - Low-Priority Process Execution (Idle / Below Normal Priority)
  - Zero Redundant RPC Network Requests
  - Isolated V3 Metrics Output in `logs/live_scan_metrics_v3.jsonl`
  - Independent Checkpoint Persistence in `checkpoint_state_v3.json`
"""

import sys
import os
import time
import json
import psutil
import ctypes

sys.stdout.reconfigure(encoding="utf-8")

# Programmatically prevent Windows Sleep/Hibernate while training is active
def prevent_sleep():
    if os.name == 'nt':
        try:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
            print("⚡ [Power Management] Windows Sleep Prevention ACTIVE (ES_SYSTEM_REQUIRED)")
        except Exception as e:
            print(f"⚠️ Power management note: {e}")

prevent_sleep()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "ai_engines"))

from universal_ai_brain import UniversalAIBrainV3
from live_online_tuner_v3 import LiveOnlineWeightTunerV3

# Set Process Priority to Low (Idle Priority) for Zero PC Lag
try:
    p = psutil.Process(os.getpid())
    p.nice(psutil.IDLE_PRIORITY_CLASS if os.name == 'nt' else 10)
    print("⚡ [V3 Runner] Process priority set to LOW (Idle Priority) for Zero PC Lag!")
except Exception as e:
    print(f"⚠️ Priority note: {e}")

PROJECT_ROOT       = os.path.abspath(os.path.join(BASE_DIR, ".."))
COMMON_DATA_STREAM = os.path.join(PROJECT_ROOT, "common", "data", "central_live_block_stream.jsonl")
ROOT_DATA_STREAM   = os.path.join(PROJECT_ROOT, "data", "central_live_block_stream.jsonl")
CENTRAL_STREAM     = COMMON_DATA_STREAM if os.path.exists(COMMON_DATA_STREAM) else ROOT_DATA_STREAM

CHECKPOINT_FILE    = os.path.join(BASE_DIR, "checkpoint_state_v3.json")
LOG_DIR            = os.path.join(BASE_DIR, "logs")
METRICS_FILE       = os.path.join(LOG_DIR, "live_scan_metrics_v3.jsonl")

sys.path.append(os.path.join(PROJECT_ROOT, "common"))
from aviation_execution_guard import AviationExecutionGuard

# FIXED: min_profit_floor_usd=0.20 (project goal: >$0.20 net profit), safety_buffer_multiplier=3.0 (true 3x guard)
aviation_guard = AviationExecutionGuard(min_profit_floor_usd=0.20, safety_buffer_multiplier=3.0)

os.makedirs(LOG_DIR, exist_ok=True)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                print(f"🔄 [V3 Stream Checkpoint] Resuming | Cumulative Scans: {state.get('cumulative_scans', 0):,} | Net PnL: ${state.get('cumulative_pnl', 0):,.2f}")
                return state
        except Exception as e:
            print(f"⚠️ Error loading V3 checkpoint: {e}")
    return {"last_block": 0, "cumulative_scans": 0, "cumulative_pnl": 0.0, "weights_version": "v3"}

def save_checkpoint(state):
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving V3 checkpoint: {e}")

def main():
    print("🚀 [V3 Stream Runner] Initializing Universal AGI Brain V3 & Online Tuner...")
    brain = UniversalAIBrainV3()
    tuner = LiveOnlineWeightTunerV3()

    checkpoint = load_checkpoint()
    scans_count = checkpoint.get("cumulative_scans", 0)
    cumulative_pnl = checkpoint.get("cumulative_pnl", 0.0)

    print(f"📡 [V3 Stream Runner] Subscribing to Central Stream: {CENTRAL_STREAM}")
    print("Press Ctrl+C to pause.\n")

    processed_snapshot_ids = set()
    file_position = 0
    # FIXED: live_pol_usd is NO LONGER hardcoded. It is updated live from the WMATIC price
    # in the central block stream on every scan. Default=None until first WMATIC snapshot arrives.
    live_pol_usd = None
    spread_histories = {"WETH": [], "WMATIC": [], "WBTC": [], "USDT": []}

    while True:
        try:
            if not os.path.exists(CENTRAL_STREAM):
                print(f"⏳ Waiting for Central Stream file to be created: {CENTRAL_STREAM}")
                time.sleep(2)
                continue

            with open(CENTRAL_STREAM, "r", encoding="utf-8") as f:
                f.seek(file_position)
                lines = f.readlines()
                file_position = f.tell()

            if not lines:
                time.sleep(0.5)
                continue

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    snapshot = json.loads(line)
                except Exception:
                    continue

                snap_id = snapshot.get("snapshot_id")
                if snap_id in processed_snapshot_ids:
                    continue
                processed_snapshot_ids.add(snap_id)
                if len(processed_snapshot_ids) > 10000:
                    processed_snapshot_ids.clear()

                sym         = snapshot.get("pair")
                qs_price    = snapshot.get("qs_price", 0.0)
                uv3_price   = snapshot.get("uv3_price", 0.0)
                qs_usdc_res = snapshot.get("usdc_reserves", 0.0)
                gas_gwei    = snapshot.get("gas_gwei", 275.0)
                block_num   = snapshot.get("block", 0)
                ts          = snapshot.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
                latency_ms  = snapshot.get("latency_ms", 0.0)

                if qs_price == 0 or uv3_price == 0:
                    continue

                # FIXED: Only update live_pol_usd when we have a valid WMATIC price snapshot
                if sym == "WMATIC" and qs_price > 0:
                    live_pol_usd = qs_price

                # Skip this scan if we do not yet have a live POL price
                # (cannot calculate gas cost without knowing POL/USD value)
                if live_pol_usd is None:
                    continue

                # Triangular Price Simulation
                triangular_price = max(qs_price, uv3_price) * 1.0020 if sym == "WMATIC" else 0.0

                # Analyze AGI Opportunity via 5 AI Brains
                res = brain.analyze_block_opportunity(
                    pair_symbol=sym,
                    qs_price=qs_price,
                    uv3_price=uv3_price,
                    pool_usdc_reserve=qs_usdc_res,
                    gas_fee_gwei=gas_gwei,
                    triangular_price=triangular_price,
                    pol_usd=live_pol_usd
                )

                # Aviation-Grade 5-Lock Surgical Gate Verification
                gross_profit = res.get("optimal_loan_usd", 10000.0) * (res.get("effective_spread_pct", 0.0) / 100.0)
                aviation_eval = aviation_guard.evaluate_all_locks(
                    gross_profit_usd=gross_profit,
                    current_gas_gwei=gas_gwei,
                    live_reserve_usd=qs_usdc_res,
                    live_pol_usd=live_pol_usd  # FIXED: pass live POL price for dynamic gas calc
                )

                # If Aviation Locks fail, override decision to WAIT/GATED to prevent zero-profit execution
                if res["decision"] == "EXECUTE" and not aviation_eval["allow_broadcast"]:
                    res["decision"] = "WAIT"
                    res["gated_reason"] = aviation_eval["reason"]

                scans_count += 1
                if res["decision"] == "EXECUTE":
                    cumulative_pnl += res["expected_net_pnl_usd"]

                # Perform Real-Time Online Weight Tuning V3
                sh = spread_histories[sym]
                sh.append(res["effective_spread_pct"])
                if len(sh) > 5:
                    sh.pop(0)
                spread_histories[sym] = sh

                tuner_res = tuner.update_weights_on_live_block(sh, res["effective_spread_pct"])

                metric = {
                    "timestamp": ts,
                    "block": block_num,
                    "scan_id": scans_count,
                    "pair": sym,
                    "qs_price": round(qs_price, 4),
                    "uv3_price": round(uv3_price, 4),
                    "direct_spread_pct": res["direct_spread_pct"],
                    "triangular_spread_pct": res["triangular_spread_pct"],
                    "effective_spread_pct": res["effective_spread_pct"],
                    "gas_gwei": round(gas_gwei, 1),
                    "latency_ms": round(latency_ms, 1),
                    "decision": res["decision"],
                    "best_route_name": res["best_route_name"],
                    "optimal_loan_usd": res["optimal_loan_usd"],
                    "expected_net_pnl_usd": res["expected_net_pnl_usd"],
                    "online_tuner_mse": tuner_res.get("avg_mse_loss", 0.0),
                    "aviation_locks_passed": aviation_eval["allow_broadcast"]
                }

                # Append V3 Metric Log
                with open(METRICS_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(metric) + "\n")

                # Save V3 Checkpoint State
                checkpoint["last_block"] = block_num
                checkpoint["cumulative_scans"] = scans_count
                checkpoint["cumulative_pnl"] = round(cumulative_pnl, 2)
                checkpoint["last_timestamp"] = ts
                save_checkpoint(checkpoint)

                print(f"[{ts}] Block #{block_num} | {sym} | Eff.Spread {metric['effective_spread_pct']:.4f}% | V3 Decision: {metric['decision']} | Route: {metric['best_route_name']} | Loan: ${metric['optimal_loan_usd']:,}")

        except Exception as e:
            print(f"⚠️ [V3 Runner] Exception: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
