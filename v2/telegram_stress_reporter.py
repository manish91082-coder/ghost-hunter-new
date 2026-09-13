"""
PhantomX Stress Test — Telegram Reporter
==========================================
Har 10 minute mein detailed status report Telegram pe bhejta hai.
Current stress test ke live data ko read karta hai aur analysis karta hai.

Features:
  - Live scan count aur rate
  - AI decision breakdown (EXECUTE/WAIT/IGNORE)
  - Spread statistics (avg, max, best token)
  - Gas economics
  - Volatility events
  - Contract simulation results
  - Key insights in Hindi
  - Test progress bar

Usage:
  python telegram_stress_reporter.py
  (stress_test_harness.py ke saath parallel chalao)
"""

import os, sys, json, glob, time, math
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))

load_dotenv()

REPORT_INTERVAL_SEC = 600   # 10 minutes
TEST_DURATION_SEC   = 3 * 3600  # 3 hours
POL_USD             = 0.50
GAS_UNITS           = 500_000
TOTAL_FEE_PCT       = 0.0044   # 0.44%


# ─── Telegram sender ──────────────────────────────────────────────────────────
def send_telegram(message: str) -> bool:
    import requests
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id   = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("[!] Telegram credentials missing")
        return False
    # Telegram 4096 char limit
    if len(message) > 4096:
        message = message[:4090] + "\n..."
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[!] Telegram error: {e}")
        return False


# ─── Find latest stress test folder ──────────────────────────────────────────
def find_test_dir():
    dirs = sorted(glob.glob("stress_test_*/"), reverse=True)
    return dirs[0].rstrip("/") if dirs else None


# ─── Load JSONL data ──────────────────────────────────────────────────────────
def load_jsonl(path, last_n=None):
    rows = []
    if not os.path.exists(path): return rows
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try: rows.append(json.loads(line))
                    except: pass
        if last_n: rows = rows[-last_n:]
    except: pass
    return rows


def load_jsonl_count(path):
    """Sirf count karo, memory efficient."""
    count = 0
    if not os.path.exists(path): return 0
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip(): count += 1
    except: pass
    return count


# ─── Progress bar ─────────────────────────────────────────────────────────────
def make_progress_bar(pct, length=20):
    filled = int(length * pct / 100)
    bar    = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {pct:.1f}%"


# ─── Analysis functions ───────────────────────────────────────────────────────
def analyze_scans(scans):
    """Price accuracy analysis."""
    by_sym = {}
    for row in scans:
        sym = row.get("sym", "?")
        sp  = row.get("spread_pct", 0)
        gas = row.get("gas_gwei", 0)
        if sym not in by_sym:
            by_sym[sym] = {"spreads": [], "gas": []}
        by_sym[sym]["spreads"].append(sp)
        by_sym[sym]["gas"].append(gas)

    result = {}
    all_gas = []
    for sym, data in by_sym.items():
        spreads = data["spreads"]
        if not spreads: continue
        result[sym] = {
            "count":     len(spreads),
            "avg_spread": round(sum(spreads)/len(spreads), 4),
            "max_spread": round(max(spreads), 4),
            "gt_05": sum(1 for s in spreads if s > 0.50),
            "gt_10": sum(1 for s in spreads if s > 1.00),
            "gt_20": sum(1 for s in spreads if s > 2.00),
        }
        all_gas.extend(data["gas"])

    avg_gas = round(sum(all_gas)/len(all_gas), 1) if all_gas else 0
    return result, avg_gas


def analyze_ai_decisions(ai_rows):
    """AI performance analysis."""
    decisions = {"EXECUTE": 0, "WAIT": 0, "IGNORE": 0}
    false_pos = 0
    correct   = 0
    for row in ai_rows:
        d = row.get("ai_decision", "IGNORE")
        decisions[d] = decisions.get(d, 0) + 1
        if row.get("ai_correct", False): correct += 1
        elif d == "EXECUTE" and not row.get("actually_profitable", False): false_pos += 1
    total = sum(decisions.values())
    acc   = round(correct / max(total, 1) * 100, 1)
    return decisions, false_pos, acc, total


def analyze_simulations(sim_rows):
    """eth_call simulation results."""
    total   = len(sim_rows)
    success = sum(1 for r in sim_rows if r.get("success", False))
    reverts = {}
    for r in sim_rows:
        if not r.get("success") and r.get("revert_reason"):
            rr = r["revert_reason"][:40]
            reverts[rr] = reverts.get(rr, 0) + 1
    return total, success, reverts


def analyze_opportunities(opp_rows):
    """Best opportunities found."""
    if not opp_rows: return []
    # Sort by spread descending
    best = sorted(opp_rows, key=lambda x: x.get("spread_pct", 0), reverse=True)
    return best[:5]  # top 5


# ─── Message builder ──────────────────────────────────────────────────────────
def build_report_message(test_dir, report_num, elapsed_sec, total_sec):
    scans    = load_jsonl(f"{test_dir}/raw_scans.jsonl")
    ai_rows  = load_jsonl(f"{test_dir}/ai_decisions.jsonl")
    sim_rows = load_jsonl(f"{test_dir}/eth_call_results.jsonl")
    opp_rows = load_jsonl(f"{test_dir}/opportunities.jsonl")

    scan_price, avg_gas   = analyze_scans(scans)
    decisions, fp, acc, total_dec = analyze_ai_decisions(ai_rows)
    sim_total, sim_ok, reverts    = analyze_simulations(sim_rows)
    best_opps                      = analyze_opportunities(opp_rows)

    # Progress
    pct      = min(elapsed_sec / total_sec * 100, 100)
    elapsed_h = elapsed_sec / 3600
    remaining = max(total_sec - elapsed_sec, 0)
    rem_h    = remaining / 3600
    prog_bar = make_progress_bar(pct)

    # Scans per minute
    total_scans = len(scans) // max(len(scan_price), 1)  # per token
    scan_rate   = round(total_scans / max(elapsed_sec / 60, 1), 1)

    # Best token (highest max spread)
    best_token = max(scan_price.items(), key=lambda x: x[1]["max_spread"], default=(None, {}))

    # Gas cost per trade
    gas_cost = GAS_UNITS * avg_gas * 1e-9 * POL_USD

    # Insights
    insights = []
    if fp == 0:
        insights.append("✅ AI ke zero false positives — sab EXECUTE decisions sahi hain")
    else:
        insights.append(f"⚠️ AI ke {fp} false positive(s) milein — threshold check karo")

    if any(d.get("max_spread", 0) > 0.5 for d in scan_price.values()):
        best_sp = max((d.get("max_spread", 0) for d in scan_price.values()), default=0)
        insights.append(f"🎯 Best spread dekha: {best_sp:.4f}% — opportunity window existed!")
    else:
        insights.append("📊 Abhi tak spread <0.5% — market calm hai, volatility ka wait karo")

    if avg_gas > 300:
        insights.append(f"⛽ Gas high hai ({avg_gas:.0f} Gwei) — profitability window tight hai")
    elif avg_gas > 200:
        insights.append(f"⛽ Gas moderate ({avg_gas:.0f} Gwei) — decent execution window")
    else:
        insights.append(f"⛽ Gas low ({avg_gas:.0f} Gwei) — excellent conditions!")

    if sim_ok > 0:
        insights.append(f"🚀 {sim_ok} trade(s) WOULD HAVE SUCCEEDED agar execute karte!")
    elif sim_total > 0:
        insights.append(f"📉 {sim_total} simulations — saari unprofitable nikli abhi")
    else:
        insights.append("🔬 eth_call simulations: spread threshold se neeche (normal hai)")

    # ── Build message ─────────────────────────────────────────────────────────
    now = datetime.now().strftime("%d/%m %H:%M IST")

    msg = f"""
🤖 *PHANTOM-X STRESS TEST — REPORT #{report_num}*
📅 {now}

⏱ *Progress:*
{prog_bar}
{elapsed_h:.2f}hr elapsed | {rem_h:.2f}hr remaining
Total scans: *{len(scans):,}* ({scan_rate:.1f}/min) | Gas: *$0*

━━━━━━━━━━━━━━━━━━━━━━━━
📊 *[A] PRICE DATA (Live):*
""".strip()

    for sym, d in scan_price.items():
        msg += f"\n`{sym:6}`: avg {d['avg_spread']:.4f}% | max *{d['max_spread']:.4f}%* | scans {d['count']:,}"
        if d['gt_05'] > 0:
            msg += f" | 🔥 *{d['gt_05']}x >0.5%*"
        if d['gt_10'] > 0:
            msg += f" | ⚡ *{d['gt_10']}x >1%*"

    msg += f"""

━━━━━━━━━━━━━━━━━━━━━━━━
🧠 *[B] AI PERFORMANCE:*
EXECUTE: `{decisions.get('EXECUTE',0)}` | WAIT: `{decisions.get('WAIT',0)}` | IGNORE: `{decisions.get('IGNORE',0)}`
Accuracy: *{acc}%* | False positives: *{fp}*
Total decisions: {total_dec:,}

━━━━━━━━━━━━━━━━━━━━━━━━
🔬 *[C] eth\\_call SIM (0 gas):*
Tests: *{sim_total}* | Succeed hote: *{sim_ok}*"""

    if reverts:
        top_rev = list(reverts.items())[:2]
        msg += "\nRevert reasons:"
        for reason, count in top_rev:
            msg += f"\n  `{count}x` — {reason}"
    else:
        msg += "\nNo simulations yet (spread below threshold)"

    msg += f"""

━━━━━━━━━━━━━━━━━━━━━━━━
⛽ *[D] GAS ECONOMICS:*
Avg gas: *{avg_gas:.1f} Gwei*
Gas cost/trade: *${gas_cost:.4f}*
Break-even spread: *0.44%*"""

    if best_opps:
        msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n🎯 *[E] BEST OPPORTUNITIES:*"
        for opp in best_opps[:3]:
            msg += (f"\n`{opp.get('sym','?')}` spread *{opp.get('spread_pct',0):.4f}%*"
                    f" | AI: {opp.get('ai_decision','?')}"
                    f" | Gas: {opp.get('gas_gwei',0):.0f}G")

    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n💡 *KEY INSIGHTS (Hindi):*"
    for ins in insights:
        msg += f"\n{ins}"

    msg += f"\n\n_Agla report {REPORT_INTERVAL_SEC//60} min mein..._"

    return msg


def build_final_report(test_dir, elapsed_sec):
    """Test khatam hone par final comprehensive report."""
    scans    = load_jsonl(f"{test_dir}/raw_scans.jsonl")
    ai_rows  = load_jsonl(f"{test_dir}/ai_decisions.jsonl")
    sim_rows = load_jsonl(f"{test_dir}/eth_call_results.jsonl")
    opp_rows = load_jsonl(f"{test_dir}/opportunities.jsonl")

    scan_price, avg_gas   = analyze_scans(scans)
    decisions, fp, acc, total_dec = analyze_ai_decisions(ai_rows)
    sim_total, sim_ok, reverts    = analyze_simulations(sim_rows)

    elapsed_h = elapsed_sec / 3600
    total_scan_rows = len(scans)

    # Best overall spread
    best_spread = max((d.get("max_spread", 0) for d in scan_price.values()), default=0)
    best_sym    = max(scan_price.items(), key=lambda x: x[1]["max_spread"], default=("?",{}))[0]

    # Health score
    score = 0
    if acc >= 80:  score += 2
    elif acc >= 60: score += 1
    if best_spread >= 0.5: score += 1
    if sim_ok > 0: score += 1
    if fp == 0:    score += 1
    max_score = 5
    grade = "🏆 EXCELLENT" if score >= 4 else ("✅ GOOD" if score >= 3 else "⚠️ NEEDS WORK")

    msg = f"""
🎉 *PHANTOM-X STRESS TEST — FINAL REPORT*
⏱ Duration: *{elapsed_h:.2f} hours* | Gas spent: *$0.00*

━━━━━━━━━━━━━━━━━━━━━━━━
🏅 *HEALTH SCORE: {score}/{max_score} — {grade}*
━━━━━━━━━━━━━━━━━━━━━━━━

📊 *TOTAL STATS:*
Total scans: *{total_scan_rows:,}*
AI decisions: *{total_dec:,}*
Simulations: *{sim_total}*
Opportunities: *{len(opp_rows)}*

🧠 *AI PERFORMANCE:*
Accuracy: *{acc}%*
False positives: *{fp}*
EXECUTE: {decisions.get('EXECUTE',0)} | IGNORE: {decisions.get('IGNORE',0)}

📈 *MARKET DATA:*
Best spread: *{best_spread:.4f}%* ({best_sym})
Avg gas: *{avg_gas:.1f} Gwei*
""".strip()

    # Category summaries
    for sym, d in scan_price.items():
        msg += f"\n`{sym}`: max {d['max_spread']:.4f}% | opp >0.5%: {d['gt_05']}x"

    msg += "\n\n💡 *FINAL INSIGHTS:*"
    if fp == 0:
        msg += "\n✅ AI zero false positives — live deploy ke liye READY!"
    else:
        msg += f"\n⚠️ AI mein {fp} false positive(s) — review karo"
    if sim_ok > 0:
        msg += f"\n🚀 {sim_ok} actual trade(s) would have PROFITED!"
    if best_spread >= 0.5:
        msg += f"\n🎯 {best_spread:.4f}% max spread detected — opportunities exist!"
    else:
        msg += "\n📊 Market calm tha — bot sahi wait karta raha"

    msg += "\n\n🚀 *NEXT STEP:*"
    if score >= 4:
        msg += "\n.env mein DRY\\_RUN=false karo → START\\_PHANTOM.bat chalao → LIVE!"
    else:
        msg += "\nReview the HTML report → tune thresholds → re-run stress test"

    msg += f"\n\n_Report saved: {test_dir}/analysis\\_report.html_"
    return msg


# ─── Main reporter loop ───────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  PHANTOM-X TELEGRAM REPORTER")
    print(f"  Sending status every {REPORT_INTERVAL_SEC//60} minutes")
    print("=" * 60)

    # Find stress test dir
    test_dir = find_test_dir()
    if not test_dir:
        print("❌ No stress_test_* folder found!")
        print("   Run stress_test_harness.py first, then this script")
        sys.exit(1)

    print(f"  📁 Monitoring: {test_dir}/")

    # Read config for start time
    config_path = f"{test_dir}/test_config.json"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        total_hours = config.get("hours", 3)
        total_sec   = total_hours * 3600
        print(f"  ⏱  Total duration: {total_hours} hours")
    else:
        total_sec = TEST_DURATION_SEC

    start_time  = time.time()
    report_num  = 0

    # Send START message
    now = datetime.now().strftime("%d/%m/%Y %H:%M IST")
    start_msg = f"""
🚀 *PHANTOM-X STRESS TEST STARTED!*
📅 {now}

📋 *Test Parameters:*
• Duration: *{total_sec//3600} hours*
• Scan interval: *3 seconds*
• Gas cost: *$0.00* (eth\\_call only)
• Tokens: WETH, WMATIC, WBTC
• Test dir: `{test_dir}/`

🎯 *What's Being Tested:*
• Live QS vs UV3 spread tracking
• AI decision accuracy (EXECUTE/WAIT/IGNORE)
• Contract simulation via eth\\_call
• Gas economics & profitability windows
• Market volatility events

📊 Reports har *10 minute* mein aayenge!
_Stress test chal rahi hai background mein..._
""".strip()

    send_telegram(start_msg)
    print(f"  ✅ Start notification sent")

    # Reporter loop
    while True:
        time.sleep(REPORT_INTERVAL_SEC)
        elapsed_sec = time.time() - start_time
        report_num += 1

        print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] Sending report #{report_num}...")

        # Check if test is done
        final_summary_path = f"{test_dir}/final_summary.json"
        test_done = os.path.exists(final_summary_path)

        if test_done or elapsed_sec >= total_sec * 1.05:
            # Final report
            msg = build_final_report(test_dir, elapsed_sec)
            ok  = send_telegram(msg)
            print(f"  {'✅' if ok else '❌'} Final report sent (report #{report_num})")

            # Also run generate_report.py for HTML
            try:
                import subprocess
                subprocess.run(["python", "generate_report.py", test_dir + "/"], check=True)
                send_telegram(f"📄 *HTML Report Ready!*\n`{test_dir}/analysis_report.html`\n\nBrowser mein kholo detailed analysis ke liye!")
            except Exception as e:
                print(f"  ⚠️ generate_report.py error: {e}")
            break
        else:
            # Periodic report
            msg = build_report_message(test_dir, report_num, elapsed_sec, total_sec)
            ok  = send_telegram(msg)
            print(f"  {'✅' if ok else '❌'} Report #{report_num} sent | Elapsed: {elapsed_sec/3600:.2f}h")


if __name__ == "__main__":
    main()
