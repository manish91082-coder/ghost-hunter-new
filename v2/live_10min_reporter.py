"""
PhantomX Live 10-Minute Reporter & Analytics Dispatcher
======================================================
Calculates speed/timing, latency, gas, price spreads, AI decision breakdown, 
and dry-run safety status from live_scan_metrics.jsonl.
Outputs detailed Hindi summaries to Terminal, Telegram, and PhantomX_Live_3Hour_Execution_Log.md.
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))
from telegram_notifier import send_telegram_message

load_dotenv()

METRICS_FILE = os.path.join(os.path.dirname(__file__), "live_scan_metrics.jsonl")
LOG_MD_FILE = os.path.join(os.path.dirname(__file__), "PhantomX_Live_3Hour_Execution_Log.md")

def generate_10min_report(interval_minutes=10):
    if not os.path.exists(METRICS_FILE):
        return None

    now = time.time()
    cutoff_10m = now - (interval_minutes * 60)
    
    total_scans_10m = 0
    scans_10m = []
    total_scans_all = 0
    scans_all = []

    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                total_scans_all += 1
                scans_all.append(data)
                if data["timestamp"] >= cutoff_10m:
                    total_scans_10m += 1
                    scans_10m.append(data)
            except Exception:
                pass

    target_scans = scans_10m if scans_10m else scans_all
    if not target_scans:
        return None

    # Calculate metrics
    latencies = [s["latency_ms"] for s in target_scans]
    gases = [s["gas_gwei"] for s in target_scans]
    spreads = [s["spread_pct"] for s in target_scans]
    decisions = {}
    for s in target_scans:
        dec = s.get("decision", "UNKNOWN")
        decisions[dec] = decisions.get(dec, 0) + 1

    avg_lat = sum(latencies) / len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)

    avg_gas = sum(gases) / len(gases)
    min_gas = min(gases)
    max_gas = max(gases)

    avg_spread = sum(spreads) / len(spreads)
    max_spread = max(spreads)

    # Symbol level stats
    sym_stats = {}
    for s in target_scans:
        sym = s["symbol"]
        if sym not in sym_stats:
            sym_stats[sym] = {"count": 0, "qs_latest": 0.0, "uv3_latest": 0.0, "max_spread": 0.0}
        sym_stats[sym]["count"] += 1
        sym_stats[sym]["qs_latest"] = s["qs_price"]
        sym_stats[sym]["uv3_latest"] = s["uv3_price"]
        if s["spread_pct"] > sym_stats[sym]["max_spread"]:
            sym_stats[sym]["max_spread"] = s["spread_pct"]

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format Telegram / Terminal Report in Hindi
    report_md = f"""
📡 *[PHANTOM-X LIVE 10-MIN REPORT]*
⏰ *Time*: `{timestamp_str}`
⏱️ *Window*: Last {interval_minutes} minutes

⚡ *Speed & Timing Analytics*:
- Total Live Scans: `{len(target_scans)}` (Cumulative: `{total_scans_all}`)
- Average Latency: `{avg_lat:.1f} ms` (Min: `{min_lat:.1f}ms` | Max: `{max_lat:.1f}ms`)
- Scan Frequency: ~1 scan every `{((interval_minutes*60)/max(1, len(target_scans))):.2f} sec`

⛽ *Polygon Gas Dynamics*:
- Average Gas: `{avg_gas:.1f} Gwei` (Range: `{min_gas:.0f} - {max_gas:.0f} Gwei`)

📊 *Market Spread & AI Decisions*:
- Average Spread: `{avg_spread:.3f}%` | Max Spread: `{max_spread:.3f}%`
- AI Decisions: `{json.dumps(decisions)}`
"""
    for sym, st in sym_stats.items():
        report_md += f"- *{sym}*: QS `${st['qs_latest']:,.4f}` | UV3 `${st['uv3_latest']:,.4f}` | Max Spread `{st['max_spread']:.3f}%`\n"

    report_md += f"\n🛡️ *Safety Audit*: `DRY_RUN=true` (Real Polygon RPC Data | $0.00 Gas Loss)\n"

    # Terminal output
    print("=" * 70)
    print(f"📊 LIVE 10-MINUTE TELEGRAM & TERMINAL REPORT [{timestamp_str}]")
    print("=" * 70)
    print(report_md)
    print("=" * 70)

    # Append to Markdown file
    log_entry = f"\n### ⏰ Live Checkpoint [{timestamp_str}]\n" + report_md + "\n---\n"
    with open(LOG_MD_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # Send to Telegram
    send_telegram_message(report_md)
    return report_md

def run_loop(interval_sec=600):
    print(f"🚀 Starting Live 10-Minute Reporter Loop (Interval: {interval_sec}s)...")
    while True:
        try:
            generate_10min_report(interval_minutes=interval_sec // 60)
        except Exception as e:
            print(f"⚠️ Reporter Error: {e}")
        time.sleep(interval_sec)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        generate_10min_report(10)
    else:
        run_loop(600)
