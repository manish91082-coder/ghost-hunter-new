"""
PhantomX 3-Hour Stress Test Harness
=====================================
Automated, comprehensive live testing engine.
- Duration: 3 hours (configurable)
- Scan interval: 3 seconds
- Gas cost: $0 (eth_call simulation only)
- Full logging: raw_scans, ai_decisions, simulations, opportunities

5 Test Categories:
  A. Price Accuracy      — QS vs UV3 price distribution
  B. AI Decision Quality — EXECUTE/WAIT/IGNORE accuracy
  C. Contract Simulation — eth_call success/revert analysis
  D. Gas Economics       — profitability at current gas prices
  E. Market Volatility   — spread spike tracking

Output directory: stress_test_YYYYMMDD_HHMMSS/
  ├── raw_scans.jsonl
  ├── ai_decisions.jsonl
  ├── eth_call_results.jsonl
  ├── opportunities.jsonl
  ├── summary_hourly.json
  └── final_summary.json

Usage: python stress_test_harness.py [--hours 3]
"""

import os, sys, json, time, asyncio, aiohttp, argparse
from datetime import datetime, timezone
from web3 import Web3
from eth_abi import decode
from eth_account import Account
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))
from ai_brain import PhantomAIBrain
from live_ethcall_simulator import (
    discover_pools, fetch_prices, simulate_arb_ethcall,
    decode_uv3_price, MULTICALL3, PHANTOM_ABI
)

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
DEFAULT_HOURS      = 3
SCAN_INTERVAL_SEC  = 3
MIN_SPREAD_SIM_PCT = 0.40   # Simulate eth_call when spread > this (% threshold for contract test)
OPPORTUNITY_THRESH = 0.50   # Log as "opportunity" when spread > this%
POL_USD            = 0.50
GAS_UNITS          = 500_000
AAVE_FEE           = 0.0009
QS_FEE             = 0.003
UV3_FEE            = 0.0005
TOTAL_FEE_PCT      = AAVE_FEE + QS_FEE + UV3_FEE

PUBLIC_RPCS = [
    "https://polygon-bor.publicnode.com",
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
]

USDC = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")


# ─── Stats Tracker ────────────────────────────────────────────────────────────
class StressTestStats:
    def __init__(self):
        self.start_time   = time.time()
        self.total_scans  = 0
        self.scan_errors  = 0

        # Category A: Price Accuracy
        self.price_data   = {}   # {sym: [spread_pct, ...]}

        # Category B: AI Decisions
        self.ai_decisions = {"EXECUTE": 0, "WAIT": 0, "IGNORE": 0}
        self.ai_false_pos = 0    # EXECUTE when unprofitable
        self.ai_correct   = 0

        # Category C: eth_call Simulations
        self.sim_total    = 0
        self.sim_success  = 0
        self.sim_reverts  = {}   # {reason: count}
        self.sim_times_ms = []

        # Category D: Gas Economics
        self.gas_readings = []
        self.profitable_at_gas = []  # gas readings when net_profit > 0

        # Category E: Volatility
        self.spike_05_pct  = 0   # spread > 0.5%
        self.spike_10_pct  = 0   # spread > 1.0%
        self.spike_20_pct  = 0   # spread > 2.0%
        self.spike_50_pct  = 0   # spread > 5.0%
        self.best_spread   = {}  # {sym: max_spread}
        self.opportunities = []  # all opportunities > 0.5%

        self.hourly_snapshots = []
        self.last_hour_snap   = time.time()

    def record_price(self, sym, qs_price, uv3_price, gas_gwei):
        spread_pct = abs(qs_price - uv3_price) / max(qs_price, 1) * 100
        if sym not in self.price_data:
            self.price_data[sym] = []
            self.best_spread[sym] = 0
        self.price_data[sym].append(spread_pct)
        if spread_pct > self.best_spread[sym]:
            self.best_spread[sym] = spread_pct

        self.gas_readings.append(gas_gwei)

        # Volatility tracking
        if spread_pct > 0.50: self.spike_05_pct += 1
        if spread_pct > 1.00: self.spike_10_pct += 1
        if spread_pct > 2.00: self.spike_20_pct += 1
        if spread_pct > 5.00: self.spike_50_pct += 1

    def record_ai(self, decision, is_correct):
        self.ai_decisions[decision] = self.ai_decisions.get(decision, 0) + 1
        if is_correct: self.ai_correct += 1
        else: self.ai_false_pos += 1 if decision == "EXECUTE" else 0

    def record_sim(self, success, revert_reason, time_ms):
        self.sim_total += 1
        if success: self.sim_success += 1
        else:
            r = revert_reason or "unknown"
            self.sim_reverts[r] = self.sim_reverts.get(r, 0) + 1
        self.sim_times_ms.append(time_ms)

    def snapshot_hourly(self):
        elapsed_h = (time.time() - self.start_time) / 3600
        snap = {
            "hour":          elapsed_h,
            "total_scans":   self.total_scans,
            "avg_gas_gwei":  sum(self.gas_readings[-200:]) / max(len(self.gas_readings[-200:]),1),
            "ai_execute":    self.ai_decisions.get("EXECUTE",0),
            "sim_success":   self.sim_success,
            "sim_total":     self.sim_total,
            "spike_05pct":   self.spike_05_pct,
            "spike_10pct":   self.spike_10_pct,
            "best_spreads":  dict(self.best_spread),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
        }
        self.hourly_snapshots.append(snap)
        return snap

    def to_final_summary(self, elapsed_sec):
        avg_gas = sum(self.gas_readings) / max(len(self.gas_readings), 1)
        total_decisions = sum(self.ai_decisions.values())
        ai_acc = (self.ai_correct / max(total_decisions, 1)) * 100

        sim_rate = (self.sim_success / max(self.sim_total, 1)) * 100
        avg_sim_ms = sum(self.sim_times_ms) / max(len(self.sim_times_ms), 1)

        spread_summaries = {}
        for sym, spreads in self.price_data.items():
            if spreads:
                spread_summaries[sym] = {
                    "count":    len(spreads),
                    "avg_pct":  round(sum(spreads)/len(spreads), 4),
                    "max_pct":  round(max(spreads), 4),
                    "min_pct":  round(min(spreads), 4),
                    "gt_05pct": sum(1 for s in spreads if s > 0.5),
                    "gt_10pct": sum(1 for s in spreads if s > 1.0),
                }

        return {
            "test_duration_hours":    elapsed_sec / 3600,
            "total_scans":            self.total_scans,
            "scan_errors":            self.scan_errors,
            "scans_per_hour":         self.total_scans / max(elapsed_sec/3600, 0.001),

            # Category A
            "price_accuracy": spread_summaries,

            # Category B
            "ai_performance": {
                "total_decisions":  total_decisions,
                "execute_count":    self.ai_decisions.get("EXECUTE", 0),
                "wait_count":       self.ai_decisions.get("WAIT", 0),
                "ignore_count":     self.ai_decisions.get("IGNORE", 0),
                "false_positives":  self.ai_false_pos,
                "correct_ignores":  self.ai_correct,
                "accuracy_pct":     round(ai_acc, 2),
            },

            # Category C
            "contract_simulation": {
                "total_simulations": self.sim_total,
                "success_count":    self.sim_success,
                "success_rate_pct": round(sim_rate, 2),
                "revert_reasons":   dict(sorted(self.sim_reverts.items(), key=lambda x:-x[1])),
                "avg_sim_ms":       round(avg_sim_ms, 2),
            },

            # Category D
            "gas_economics": {
                "avg_gas_gwei":    round(avg_gas, 1),
                "min_gas_gwei":    round(min(self.gas_readings, default=0), 1),
                "max_gas_gwei":    round(max(self.gas_readings, default=0), 1),
                "break_even_pct":  round(TOTAL_FEE_PCT * 100, 3),
            },

            # Category E
            "market_volatility": {
                "spikes_gt_05pct":  self.spike_05_pct,
                "spikes_gt_10pct":  self.spike_10_pct,
                "spikes_gt_20pct":  self.spike_20_pct,
                "spikes_gt_50pct":  self.spike_50_pct,
                "opportunities_detected": len(self.opportunities),
                "best_spreads":     dict(self.best_spread),
            },

            "hourly_snapshots":    self.hourly_snapshots,
        }


# ─── Main Harness ─────────────────────────────────────────────────────────────
async def run_stress_test(hours: float):
    test_id   = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir   = f"stress_test_{test_id}"
    os.makedirs(out_dir, exist_ok=True)

    # Log files
    fscans   = open(f"{out_dir}/raw_scans.jsonl",       "a", encoding="utf-8")
    fai      = open(f"{out_dir}/ai_decisions.jsonl",    "a", encoding="utf-8")
    fsim     = open(f"{out_dir}/eth_call_results.jsonl","a", encoding="utf-8")
    fopp     = open(f"{out_dir}/opportunities.jsonl",   "a", encoding="utf-8")

    def logj(fh, obj):
        fh.write(json.dumps(obj) + "\n")
        fh.flush()

    stats = StressTestStats()
    brain = PhantomAIBrain()

    print("=" * 65)
    print(f"  🚀 PHANTOM-X STRESS TEST — {hours}hr | $0 Gas | Live Data")
    print(f"  Output: {out_dir}/")
    print("=" * 65)

    # Setup wallet + contract
    pk = os.getenv("GHOSTHUNTER_DEV_PRIVATE_KEY")
    account  = Account.from_key(pk)
    contract_addr = open("deployed_contract.txt").read().strip()
    print(f"\n  🔑 Wallet  : {account.address}")
    print(f"  📄 Contract: {contract_addr}")

    # Connect RPC
    w3 = None
    for rpc in PUBLIC_RPCS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                print(f"  ✅ RPC    : {rpc}")
                break
        except: pass
    if not w3 or not w3.is_connected():
        sys.exit("❌ All RPCs failed")

    pools = discover_pools(w3)
    syms  = list(pools.keys())
    print(f"  📡 Pools  : {syms}")

    # Write test config
    config = {
        "test_id":       test_id,
        "hours":         hours,
        "scan_interval": SCAN_INTERVAL_SEC,
        "contract":      contract_addr,
        "wallet":        account.address,
        "pools":         syms,
        "start_time":    datetime.now(timezone.utc).isoformat(),
        "categories":    ["A_price_accuracy","B_ai_quality","C_eth_call_sim","D_gas_economics","E_volatility"],
    }
    with open(f"{out_dir}/test_config.json", "w") as f:
        json.dump(config, f, indent=2)

    end_time      = time.time() + hours * 3600
    scan_num      = 0
    last_hour_log = time.time()
    HOUR_INTERVAL = 3600

    print(f"\n  ⏱️  Running until: {datetime.fromtimestamp(end_time).strftime('%H:%M:%S')}")
    print(f"  📊 Logging to: {out_dir}/")
    print(f"\n  {'─'*65}")
    print(f"  {'Scan':>5} {'Time':>8} {'Token':>6} {'QS Price':>12} {'UV3 Price':>12} {'Spread':>7} {'Gas':>5} {'AI':>8} {'Sim':>12}")
    print(f"  {'─'*65}")

    async with aiohttp.ClientSession() as session:
        while time.time() < end_time:
            scan_ts = time.time()
            scan_num += 1
            stats.total_scans += 1

            # ── Fetch live gas ──────────────────────────────────────────────
            try:
                gas_gwei = float(w3.from_wei(w3.eth.gas_price, "gwei"))
            except:
                gas_gwei = 280.0

            # ── Fetch live prices ───────────────────────────────────────────
            try:
                prices = fetch_prices(w3, pools)
            except Exception as e:
                stats.scan_errors += 1
                await asyncio.sleep(SCAN_INTERVAL_SEC)
                continue

            # ── Process each token ──────────────────────────────────────────
            for sym in syms:
                if sym not in prices: continue
                info      = prices[sym]
                qs_price  = info["qs_price"]
                uv3_price = info["uv3_price"]
                res       = info["qs_usdc_reserves"]
                tok_dec   = info["tok_dec"]
                tok_addr  = info["tok_addr"]

                if qs_price == 0 or uv3_price == 0: continue

                spread_pct   = abs(qs_price - uv3_price) / max(qs_price, 1) * 100
                start_on_qs  = qs_price < uv3_price

                # Category A: Record spread
                stats.record_price(sym, qs_price, uv3_price, gas_gwei)

                # Category B: AI Decision
                decision, loan, est_profit, bribe = brain.analyze_scenario(
                    qs_price, uv3_price, res, gas_gwei
                )
                # Ground truth profitability
                max_loan    = res * 0.01
                gross       = max_loan * (spread_pct/100)
                fees_cost   = max_loan * TOTAL_FEE_PCT
                gas_cost    = GAS_UNITS * gas_gwei * 1e-9 * POL_USD
                actual_prof = gross - fees_cost - gas_cost
                actually_ok = actual_prof > 0

                is_correct = (decision == "EXECUTE" and actually_ok) or \
                             (decision != "EXECUTE" and not actually_ok)
                stats.record_ai(decision, is_correct)

                # Log AI decision
                ai_rec = {
                    "ts": scan_ts, "sym": sym, "scan": scan_num,
                    "qs_price": round(qs_price, 4), "uv3_price": round(uv3_price, 4),
                    "spread_pct": round(spread_pct, 4), "gas_gwei": round(gas_gwei, 1),
                    "qs_usdc_reserves": round(res, 2),
                    "ai_decision": decision, "ai_loan_usd": round(loan, 2),
                    "ai_est_profit": round(est_profit, 4),
                    "actual_profit_if_max_loan": round(actual_prof, 4),
                    "actually_profitable": actually_ok,
                    "ai_correct": is_correct,
                }
                logj(fai, ai_rec)

                # Log raw scan
                scan_rec = {
                    "ts": scan_ts, "sym": sym, "scan": scan_num,
                    "qs": round(qs_price, 4), "uv3": round(uv3_price, 4),
                    "spread_pct": round(spread_pct, 4), "gas_gwei": round(gas_gwei, 1),
                    "res_usd": round(res, 0),
                }
                logj(fscans, scan_rec)

                # Category E: Opportunity detection
                if spread_pct >= OPPORTUNITY_THRESH:
                    opp = {**ai_rec, "opportunity_score": round((spread_pct - TOTAL_FEE_PCT*100) * loan, 2)}
                    logj(fopp, opp)
                    stats.opportunities.append(opp)

                # Category C: eth_call simulation
                # Simulate whenever spread > threshold OR AI says EXECUTE
                should_sim = (spread_pct >= MIN_SPREAD_SIM_PCT) or (decision == "EXECUTE")
                sim_result = None
                sim_label  = ""

                if should_sim and loan > 10:
                    sim = simulate_arb_ethcall(
                        w3, contract_addr, account.address,
                        tok_addr, loan, start_on_qs,
                        qs_price, uv3_price, tok_dec, gas_gwei
                    )
                    stats.record_sim(sim["success"], sim.get("revert_reason"), sim["eth_call_time_ms"])

                    sim_rec = {
                        "ts": scan_ts, "sym": sym, "scan": scan_num,
                        "spread_pct": round(spread_pct, 4),
                        "loan_usd": round(loan, 2),
                        "success": sim["success"],
                        "revert_reason": sim.get("revert_reason"),
                        "gas_estimate": sim.get("gas_estimate"),
                        "gas_cost_usd": round(sim.get("gas_cost_usd", 0), 4),
                        "eth_call_ms": round(sim["eth_call_time_ms"], 1),
                    }
                    logj(fsim, sim_rec)
                    sim_label = "✅SIM" if sim["success"] else f"❌{(sim.get('revert_reason') or 'err')[:8]}"
                else:
                    sim_label = "—"

                # ── Console output ──────────────────────────────────────────
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(time.time() - stats.start_time))
                print(f"  {scan_num:5d} {elapsed_str:>8} {sym:>6} ${qs_price:>11,.4f} ${uv3_price:>11,.4f} "
                      f"{spread_pct:>6.3f}% {gas_gwei:>5.0f} {decision:>8} {sim_label:>12}")

            # ── Hourly snapshot ─────────────────────────────────────────────
            if time.time() - last_hour_log >= HOUR_INTERVAL:
                snap = stats.snapshot_hourly()
                with open(f"{out_dir}/summary_hourly.json", "w") as f:
                    json.dump(stats.hourly_snapshots, f, indent=2)
                last_hour_log = time.time()
                elapsed_h = (time.time() - stats.start_time) / 3600
                remaining_h = hours - elapsed_h
                print(f"\n  {'━'*65}")
                print(f"  ⏱️  HOURLY SNAPSHOT — Hour {elapsed_h:.1f} | Remaining: {remaining_h:.1f}h")
                print(f"  Scans: {stats.total_scans} | Exec: {snap['ai_execute']} | "
                      f"Sim OK: {snap['sim_success']}/{snap['sim_total']} | "
                      f"Gas: {snap['avg_gas_gwei']:.0f}G")
                print(f"  Best spreads: " + " | ".join(f"{k}:{v:.3f}%" for k,v in snap['best_spreads'].items()))
                print(f"  {'━'*65}\n")

            # ── Sleep until next scan ───────────────────────────────────────
            elapsed_scan = time.time() - scan_ts
            sleep_time   = max(0, SCAN_INTERVAL_SEC - elapsed_scan)
            await asyncio.sleep(sleep_time)

    # ── Test complete ──────────────────────────────────────────────────────
    fscans.close(); fai.close(); fsim.close(); fopp.close()

    elapsed_sec = time.time() - stats.start_time
    summary     = stats.to_final_summary(elapsed_sec)
    summary["test_id"]   = test_id
    summary["end_time"]  = datetime.now(timezone.utc).isoformat()
    summary["out_dir"]   = out_dir

    with open(f"{out_dir}/final_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # ── Print final summary ────────────────────────────────────────────────
    print(f"\n\n  {'═'*65}")
    print(f"  🎉 STRESS TEST COMPLETE — {elapsed_sec/3600:.2f} hours")
    print(f"  {'═'*65}")
    print(f"  Total Scans       : {stats.total_scans}")
    print(f"  Scan Errors       : {stats.scan_errors}")
    print(f"\n  [A] Price Accuracy:")
    for sym, d in summary["price_accuracy"].items():
        print(f"    {sym:6s}: avg={d['avg_pct']:.4f}% | max={d['max_pct']:.4f}% | >0.5%: {d['gt_05pct']} times")
    print(f"\n  [B] AI Performance:")
    ai = summary["ai_performance"]
    print(f"    EXECUTE:{ai['execute_count']} | WAIT:{ai['wait_count']} | IGNORE:{ai['ignore_count']}")
    print(f"    False Positives: {ai['false_positives']} | Accuracy: {ai['accuracy_pct']}%")
    print(f"\n  [C] Contract Simulation:")
    cs = summary["contract_simulation"]
    print(f"    Total: {cs['total_simulations']} | Success: {cs['success_count']} ({cs['success_rate_pct']}%)")
    if cs["revert_reasons"]:
        print(f"    Revert reasons: {cs['revert_reasons']}")
    print(f"    Avg sim time: {cs['avg_sim_ms']:.0f}ms")
    print(f"\n  [D] Gas Economics:")
    ge = summary["gas_economics"]
    print(f"    Avg: {ge['avg_gas_gwei']}G | Min: {ge['min_gas_gwei']}G | Max: {ge['max_gas_gwei']}G")
    print(f"    Break-even spread: {ge['break_even_pct']}%")
    print(f"\n  [E] Market Volatility:")
    mv = summary["market_volatility"]
    print(f"    >0.5%: {mv['spikes_gt_05pct']} | >1%: {mv['spikes_gt_10pct']} | "
          f">2%: {mv['spikes_gt_20pct']} | >5%: {mv['spikes_gt_50pct']}")
    print(f"    Opportunities detected: {mv['opportunities_detected']}")
    print(f"    Best spreads: {mv['best_spreads']}")
    print(f"\n  💾 All data saved in: {out_dir}/")
    print(f"  Run: python generate_report.py {out_dir}/  for detailed analysis")
    print(f"  {'═'*65}\n")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=DEFAULT_HOURS,
                        help="Test duration in hours (default: 3)")
    args = parser.parse_args()

    print(f"\n  ⚡ Stress test starting: {args.hours} hours")
    print(f"  💡 Gas cost: $0 (eth_call only)")
    print(f"  💡 Press Ctrl+C to stop early and save partial results\n")

    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(run_stress_test(args.hours))
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Test interrupted by user. Partial data saved.")
