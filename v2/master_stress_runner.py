"""
PhantomX Master Stress Test Runner
=====================================
Ye script stress test ko automatically chalata hai aur:
  - Har 10 MINUTE mein Telegram pe Hindi report bhejta hai
  - Telegram mein deep insights deta hai
  - Complete stress test ko manage karta hai

Usage:
  python master_stress_runner.py

Note: Yahi script stress_test_harness.py ko background mein chalata hai
      aur telegram_stress_reporter.py ki jagah improved reporting karta hai.
"""

import os, sys, json, time, glob, subprocess, threading
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

# ── Configuration ──────────────────────────────────────────────────────────────
TEST_HOURS          = 3.0
TELEGRAM_INTERVAL   = 600   # 10 minute = 600 seconds
POL_USD             = 0.50
GAS_UNITS           = 500_000
TOTAL_FEE_PCT       = 0.0044   # 0.44% break-even

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ── Telegram ───────────────────────────────────────────────────────────────────
def send_telegram(message: str) -> bool:
    import requests
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id   = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("[!] Telegram credentials missing in .env")
        return False
    # Use last values if duplicate keys exist
    if isinstance(chat_id, str) and "\n" in chat_id:
        chat_id = chat_id.strip().split("\n")[-1]
    message = message[:4090] + "\n..." if len(message) > 4096 else message
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=15
        )
        if resp.status_code == 200:
            return True
        else:
            print(f"[!] Telegram HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[!] Telegram error: {e}")
        return False


# ── Data loading ───────────────────────────────────────────────────────────────
def find_latest_test_dir():
    dirs = sorted(glob.glob("stress_test_*/"), reverse=True)
    return dirs[0].rstrip("/") if dirs else None


def load_jsonl(path):
    rows = []
    if not os.path.exists(path): return rows
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try: rows.append(json.loads(line))
                    except: pass
    except: pass
    return rows


def load_jsonl_count(path):
    count = 0
    if not os.path.exists(path): return 0
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip(): count += 1
    except: pass
    return count


# ── Analysis functions ─────────────────────────────────────────────────────────
def analyze_all_data(test_dir):
    scans    = load_jsonl(f"{test_dir}/raw_scans.jsonl")
    ai_rows  = load_jsonl(f"{test_dir}/ai_decisions.jsonl")
    sim_rows = load_jsonl(f"{test_dir}/eth_call_results.jsonl")
    opp_rows = load_jsonl(f"{test_dir}/opportunities.jsonl")

    # Price analysis
    by_sym = {}
    all_gas = []
    for row in scans:
        sym = row.get("sym", "?")
        sp  = row.get("spread_pct", 0)
        gas = row.get("gas_gwei", 0)
        if sym not in by_sym:
            by_sym[sym] = {"spreads": [], "gas": []}
        by_sym[sym]["spreads"].append(sp)
        by_sym[sym]["gas"].append(gas)
        all_gas.append(gas)

    price_stats = {}
    for sym, data in by_sym.items():
        spreads = data["spreads"]
        if not spreads: continue
        price_stats[sym] = {
            "count":      len(spreads),
            "avg_spread": round(sum(spreads)/len(spreads), 4),
            "max_spread": round(max(spreads), 4),
            "min_spread": round(min(spreads), 4),
            "gt_05":  sum(1 for s in spreads if s > 0.50),
            "gt_10":  sum(1 for s in spreads if s > 1.00),
            "gt_20":  sum(1 for s in spreads if s > 2.00),
            "gt_50":  sum(1 for s in spreads if s > 5.00),
        }

    avg_gas = round(sum(all_gas)/len(all_gas), 1) if all_gas else 0
    min_gas = round(min(all_gas), 1) if all_gas else 0
    max_gas = round(max(all_gas), 1) if all_gas else 0

    # AI analysis
    decisions = {"EXECUTE": 0, "WAIT": 0, "IGNORE": 0}
    false_pos = 0
    correct   = 0
    for row in ai_rows:
        d = row.get("ai_decision", "IGNORE")
        decisions[d] = decisions.get(d, 0) + 1
        if row.get("ai_correct", False): correct += 1
        elif d == "EXECUTE" and not row.get("actually_profitable", False): false_pos += 1
    total_dec = sum(decisions.values())
    acc = round(correct / max(total_dec, 1) * 100, 1)

    # Simulation analysis
    sim_total   = len(sim_rows)
    sim_success = sum(1 for r in sim_rows if r.get("success", False))
    reverts = {}
    for r in sim_rows:
        if not r.get("success") and r.get("revert_reason"):
            rr = r["revert_reason"][:40]
            reverts[rr] = reverts.get(rr, 0) + 1
    sim_rate = round(sim_success / max(sim_total, 1) * 100, 1)

    # Best opportunities
    best_opps = sorted(opp_rows, key=lambda x: x.get("spread_pct", 0), reverse=True)[:5]

    # Gas cost per trade
    gas_cost_usd = GAS_UNITS * avg_gas * 1e-9 * POL_USD

    return {
        "scans":        scans,
        "price_stats":  price_stats,
        "avg_gas":      avg_gas,
        "min_gas":      min_gas,
        "max_gas":      max_gas,
        "decisions":    decisions,
        "false_pos":    false_pos,
        "accuracy":     acc,
        "total_dec":    total_dec,
        "sim_total":    sim_total,
        "sim_success":  sim_success,
        "sim_rate":     sim_rate,
        "reverts":      reverts,
        "opportunities": opp_rows,
        "best_opps":    best_opps,
        "gas_cost_usd": gas_cost_usd,
        "total_scans":  len(scans),
        "ai_rows":      ai_rows,
    }


def make_progress_bar(pct, length=20):
    filled = int(length * pct / 100)
    bar    = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {pct:.1f}%"


# ── Deep Insights Generator ────────────────────────────────────────────────────
def generate_deep_insights(data, elapsed_sec, total_sec):
    """Har 10 minute ke liye Hindi mein deep analysis insights."""
    insights = []
    price_stats = data["price_stats"]
    decisions   = data["decisions"]
    false_pos   = data["false_pos"]
    accuracy    = data["accuracy"]
    avg_gas     = data["avg_gas"]
    sim_total   = data["sim_total"]
    sim_success = data["sim_success"]
    sim_rate    = data["sim_rate"]
    opportunities = data["opportunities"]
    best_opps   = data["best_opps"]
    gas_cost    = data["gas_cost_usd"]
    total_scans = data["total_scans"]

    # 1. AI Performance Analysis
    if false_pos == 0 and decisions.get("EXECUTE", 0) > 0:
        insights.append("🧠 *AI बिल्कुल सटीक है!* — अब तक शून्य false positives। यह LIVE deployment के लिए तैयार है।")
    elif false_pos == 0:
        insights.append("🧠 *AI सावधान है* — EXECUTE signal नहीं दिया अभी तक। Market tight conditions में है।")
    elif false_pos > 5:
        insights.append(f"⚠️ *AI threshold tune करो!* — {false_pos} false positives मिले। MIN_SPREAD_PCT बढ़ाओ।")
    else:
        insights.append(f"🧠 *AI {accuracy}% accurate* — {false_pos} minor false positives। Normal range में है।")

    # 2. Market Spread Analysis
    all_max_spreads = [d.get("max_spread", 0) for d in price_stats.values()]
    overall_max = max(all_max_spreads) if all_max_spreads else 0
    best_token = max(price_stats.items(), key=lambda x: x[1].get("max_spread", 0), default=("N/A", {}))[0]

    if overall_max >= 2.0:
        insights.append(f"🔥 *Market बहुत volatile है!* — {best_token} में {overall_max:.4f}% spread देखा! यह बड़ा opportunity window था!")
    elif overall_max >= 0.5:
        insights.append(f"🎯 *Arbitrage window था!* — {best_token} में max {overall_max:.4f}% spread। Break-even (0.44%) से ऊपर!")
    elif overall_max >= 0.2:
        insights.append(f"📊 *Market calm है* — Max spread {overall_max:.4f}%। Break-even (0.44%) से नीचे। Volatility का इंतज़ार करो।")
    else:
        insights.append(f"😴 *Market flat है* — Max spread सिर्फ {overall_max:.4f}%। Very stable conditions। Bot सही WAIT कर रहा है।")

    # 3. Gas Economics
    break_even_spread = TOTAL_FEE_PCT * 100  # 0.44%
    if avg_gas > 500:
        gas_impact = avg_gas * GAS_UNITS * 1e-9 * POL_USD
        insights.append(f"⛽ *Gas बहुत high है!* — {avg_gas:.0f} Gwei → प्रति trade ${gas_cost:.4f}। Profitability पर बड़ा असर।")
    elif avg_gas > 200:
        insights.append(f"⛽ *Gas moderate है* — {avg_gas:.0f} Gwei → per trade ${gas_cost:.4f}। {break_even_spread:.2f}% spread चाहिए break-even के लिए।")
    else:
        insights.append(f"⛽ *Gas excellent है!* — सिर्फ {avg_gas:.0f} Gwei → per trade ${gas_cost:.4f}। कम spread में भी profit possible!")

    # 4. Contract Simulation Analysis
    if sim_success > 0:
        insights.append(f"🚀 *{sim_success} trades WOULD HAVE PROFITED!* — eth_call simulation success! LIVE mode में ये पैसे होते!")
    elif sim_total > 0:
        insights.append(f"📉 *{sim_total} simulations, सब unprofitable निकले* — fees cover नहीं हो रही अभी। Market wait कर रहा है।")
    else:
        insights.append(f"🔬 *eth_call simulation नहीं चला अभी* — spread threshold (0.40%) से नीचे। यह expected behavior है।")

    # 5. Scan Rate Health
    scan_rate_per_min = total_scans / max(elapsed_sec / 60, 1)
    expected_rate = 60 / 3  # 3 second interval = 20 scans/min per token
    if scan_rate_per_min > 10:
        insights.append(f"⚡ *Scan rate healthy है!* — {scan_rate_per_min:.1f} scans/min। RPC connection stable है।")
    else:
        insights.append(f"⚠️ *Scan rate slow है* — {scan_rate_per_min:.1f}/min। RPC slow हो सकता है।")

    # 6. Opportunity Pattern
    if len(opportunities) > 20:
        insights.append(f"📈 *{len(opportunities)} opportunities detected!* — Market अच्छी opportunities दे रहा है। LIVE mode में profit possible था!")
    elif len(opportunities) > 5:
        insights.append(f"📊 *{len(opportunities)} opportunities मिले* — कुछ windows थे। Strategy sahi kaam kar rahi hai.")
    else:
        insights.append(f"🔎 *{len(opportunities)} opportunities अभी तक* — Market tight conditions में है। Bot correctly WAIT कर रहा है।")

    # 7. Time-based insight
    progress_pct = min(elapsed_sec / total_sec * 100, 100)
    remaining_h = max(total_sec - elapsed_sec, 0) / 3600
    if progress_pct < 25:
        insights.append(f"⏱️ *Test अभी शुरू हुआ है* — {remaining_h:.1f} घंटे बाकी हैं। Data accumulate हो रहा है।")
    elif progress_pct < 50:
        insights.append(f"⏱️ *Test आधे रास्ते पर है* — {remaining_h:.1f} घंटे बाकी। Pattern clear हो रहे हैं।")
    elif progress_pct < 75:
        insights.append(f"⏱️ *Test 3/4 complete* — {remaining_h:.1f} घंटे बाकी। Final data collect हो रहा है।")
    else:
        insights.append(f"⏱️ *Test लगभग खत्म!* — सिर्फ {remaining_h:.2f} घंटे बाकी! Final results आने वाले हैं।")

    return insights


# ── Telegram Report Builder ────────────────────────────────────────────────────
def build_telegram_report(test_dir, report_num, elapsed_sec, total_sec):
    data = analyze_all_data(test_dir)
    price_stats = data["price_stats"]
    decisions   = data["decisions"]
    false_pos   = data["false_pos"]
    accuracy    = data["accuracy"]
    avg_gas     = data["avg_gas"]
    sim_total   = data["sim_total"]
    sim_success = data["sim_success"]
    sim_rate    = data["sim_rate"]
    reverts     = data["reverts"]
    best_opps   = data["best_opps"]
    gas_cost    = data["gas_cost_usd"]
    total_scans = data["total_scans"]

    pct      = min(elapsed_sec / total_sec * 100, 100)
    elapsed_h = elapsed_sec / 3600
    rem_h    = max(total_sec - elapsed_sec, 0) / 3600
    prog_bar = make_progress_bar(pct)

    tokens = len(price_stats)
    scan_per_token = total_scans // max(tokens, 1)
    scan_rate = round(scan_per_token / max(elapsed_sec / 60, 1), 1)

    now = datetime.now().strftime("%d/%m %H:%M IST")

    # Deep insights
    insights = generate_deep_insights(data, elapsed_sec, total_sec)

    msg = f"""🤖 *PHANTOM\\-X STRESS TEST — REPORT \\#{report_num}*
📅 {now} \\| Report हर *10 मिनट* में

⏱ *प्रगति:*
{prog_bar}
{elapsed_h:.2f}hr पूरे \\| {rem_h:.2f}hr बाकी
कुल scans: *{total_scans:,}* \\({scan_rate:.1f}/min\\) \\| Gas cost: *$0*

━━━━━━━━━━━━━━━━━━━━━━
📊 *\\[A\\] PRICE DATA \\(Live\\):*"""

    for sym, d in price_stats.items():
        line = f"\n`{sym:6}`: avg {d['avg_spread']:.4f}% \\| max *{d['max_spread']:.4f}%* \\| {d['count']:,} scans"
        if d['gt_05'] > 0:
            line += f" \\| 🔥*{d['gt_05']}x>0\\.5%*"
        if d['gt_10'] > 0:
            line += f" \\| ⚡*{d['gt_10']}x>1%*"
        if d['gt_20'] > 0:
            line += f" \\| 💥*{d['gt_20']}x>2%*"
        msg += line

    msg += f"""

━━━━━━━━━━━━━━━━━━━━━━
🧠 *\\[B\\] AI PERFORMANCE:*
EXECUTE: `{decisions.get('EXECUTE',0)}` \\| WAIT: `{decisions.get('WAIT',0)}` \\| IGNORE: `{decisions.get('IGNORE',0)}`
Accuracy: *{accuracy}%* \\| False positives: *{false_pos}*
कुल decisions: {data['total_dec']:,}

━━━━━━━━━━━━━━━━━━━━━━
🔬 *\\[C\\] eth\\_call SIM \\($0 gas\\):*
Tests: *{sim_total}* \\| Success होते: *{sim_success}* \\({sim_rate}%\\)"""

    if reverts:
        top_rev = list(reverts.items())[:2]
        msg += "\nRevert reasons:"
        for reason, count in top_rev:
            msg += f"\n  `{count}x` — {reason[:35]}"
    else:
        msg += "\nकोई simulation नहीं \\(spread threshold से नीचे\\)"

    msg += f"""

━━━━━━━━━━━━━━━━━━━━━━
⛽ *\\[D\\] GAS ECONOMICS:*
Average: *{avg_gas:.1f} Gwei* \\| Min: {data['min_gas']} \\| Max: {data['max_gas']}
Per trade cost: *${gas_cost:.4f}*
Break\\-even spread: *0\\.44%*"""

    if best_opps:
        msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎯 *\\[E\\] BEST OPPORTUNITIES:*"
        for opp in best_opps[:3]:
            sym_o  = opp.get('sym', '?')
            sp_o   = opp.get('spread_pct', 0)
            dec_o  = opp.get('ai_decision', '?')
            gas_o  = opp.get('gas_gwei', 0)
            msg += f"\n`{sym_o}` spread *{sp_o:.4f}%* \\| AI: {dec_o} \\| Gas: {gas_o:.0f}G"

    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n💡 *DEEP INSIGHTS \\(Hindi\\):*"
    for ins in insights:
        # Escape special MarkdownV2 chars but keep existing escaped ones
        safe_ins = ins.replace("!", "\\!")
        msg += f"\n{safe_ins}"

    msg += f"\n\n_अगला report {TELEGRAM_INTERVAL//60} मिनट में आएगा..._"
    return msg


def build_final_telegram_report(test_dir, elapsed_sec):
    """Test khatam hone par final comprehensive Hindi report."""
    data = analyze_all_data(test_dir)
    price_stats = data["price_stats"]
    decisions   = data["decisions"]
    false_pos   = data["false_pos"]
    accuracy    = data["accuracy"]
    avg_gas     = data["avg_gas"]
    sim_total   = data["sim_total"]
    sim_success = data["sim_success"]
    opportunities = data["opportunities"]

    elapsed_h = elapsed_sec / 3600

    best_spread = max((d.get("max_spread", 0) for d in price_stats.values()), default=0)
    best_sym = max(price_stats.items(), key=lambda x: x[1].get("max_spread", 0), default=("?", {}))[0]

    # Health score
    score = 0
    if accuracy >= 80: score += 2
    elif accuracy >= 60: score += 1
    if best_spread >= 0.5: score += 1
    if sim_success > 0: score += 1
    if false_pos == 0: score += 1
    max_score = 5
    grade = "🏆 EXCELLENT" if score >= 4 else ("✅ GOOD" if score >= 3 else "⚠️ NEEDS WORK")

    now = datetime.now().strftime("%d/%m/%Y %H:%M IST")

    msg = f"""🎉 *PHANTOM\\-X STRESS TEST — FINAL REPORT*
📅 {now}
⏱ Duration: *{elapsed_h:.2f} hours* \\| Gas खर्च: *$0\\.00*

━━━━━━━━━━━━━━━━━━━━━━
🏅 *HEALTH SCORE: {score}/{max_score} — {grade}*
━━━━━━━━━━━━━━━━━━━━━━

📊 *कुल STATISTICS:*
Total scans: *{data['total_scans']:,}*
AI decisions: *{data['total_dec']:,}*
Simulations: *{sim_total}*
Opportunities: *{len(opportunities)}*

🧠 *AI PERFORMANCE:*
Accuracy: *{accuracy}%*
False positives: *{false_pos}*
EXECUTE: {decisions.get('EXECUTE',0)} \\| WAIT: {decisions.get('WAIT',0)} \\| IGNORE: {decisions.get('IGNORE',0)}

📈 *MARKET DATA:*
Best spread: *{best_spread:.4f}%* \\({best_sym}\\)
Average gas: *{avg_gas:.1f} Gwei*"""

    for sym, d in price_stats.items():
        msg += f"\n`{sym}`: max {d['max_spread']:.4f}% \\| opp>0\\.5%: {d['gt_05']}x"

    msg += "\n\n💡 *FINAL ANALYSIS \\(Hindi\\):*"
    if false_pos == 0:
        msg += "\n✅ AI zero false positives — LIVE deployment के लिए *READY\\!*"
    else:
        msg += f"\n⚠️ AI में {false_pos} false positive\\(s\\) — threshold review करो"
    if sim_success > 0:
        msg += f"\n🚀 {sim_success} actual trade\\(s\\) PROFITABLE होते\\!"
    if best_spread >= 0.5:
        msg += f"\n🎯 {best_spread:.4f}% max spread — opportunities exist करती हैं\\!"
    else:
        msg += "\n📊 Market calm रहा — bot ने सही WAIT किया"

    msg += "\n\n🚀 *NEXT STEP:*"
    if score >= 4:
        msg += "\n\\.env में DRY\\_RUN=false करो → START\\_PHANTOM\\.bat चलाओ → LIVE\\!"
    else:
        msg += "\nHTML report review करो → thresholds tune करो → stress test दोबारा"

    return msg


# ── Hourly Console Report ──────────────────────────────────────────────────────
def print_hourly_report_here(test_dir, elapsed_sec, total_sec, hour_num):
    """Har 1 ghante mein detailed console report."""
    data = analyze_all_data(test_dir)
    price_stats = data["price_stats"]
    decisions   = data["decisions"]
    false_pos   = data["false_pos"]
    accuracy    = data["accuracy"]
    avg_gas     = data["avg_gas"]
    sim_total   = data["sim_total"]
    sim_success = data["sim_success"]
    sim_rate    = data["sim_rate"]
    reverts     = data["reverts"]
    opportunities = data["opportunities"]
    best_opps   = data["best_opps"]
    total_scans = data["total_scans"]
    gas_cost    = data["gas_cost_usd"]

    elapsed_h = elapsed_sec / 3600
    rem_h = max(total_sec - elapsed_sec, 0) / 3600
    pct = min(elapsed_sec / total_sec * 100, 100)
    prog_bar = make_progress_bar(pct)

    best_spread = max((d.get("max_spread", 0) for d in price_stats.values()), default=0)
    best_sym = max(price_stats.items(), key=lambda x: x[1].get("max_spread", 0), default=("N/A", {}))[0]

    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S IST")

    report = f"""
╔══════════════════════════════════════════════════════════════════╗
║          🕐 PHANTOM-X HOURLY REPORT — HOUR #{hour_num}                   ║
║          समय: {now}                  ║
╠══════════════════════════════════════════════════════════════════╣

  📊 प्रगति: {prog_bar}
     {elapsed_h:.2f} घंटे पूरे | {rem_h:.2f} घंटे बाकी | {pct:.1f}% complete

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📡 [A] PRICE ACCURACY (कुल {total_scans:,} scans):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    for sym, d in price_stats.items():
        opp_flag = " ← 🔥 OPPORTUNITY!" if d['gt_05'] > 0 else ""
        report += f"""
    {sym:6}: avg={d['avg_spread']:.4f}% | max={d['max_spread']:.4f}% | min={d['min_spread']:.4f}%
           scans: {d['count']:,} | >0.5%: {d['gt_05']}x | >1%: {d['gt_10']}x | >2%: {d['gt_20']}x{opp_flag}"""

    report += f"""

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🧠 [B] AI PERFORMANCE:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    EXECUTE: {decisions.get('EXECUTE',0):5} | WAIT: {decisions.get('WAIT',0):5} | IGNORE: {decisions.get('IGNORE',0):5}
    Accuracy: {accuracy}% | False Positives: {false_pos}
    कुल decisions: {data['total_dec']:,}
    {'✅ AI बिल्कुल सटीक है!' if false_pos == 0 else f'⚠️ {false_pos} false positives देखे गए'}

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔬 [C] CONTRACT SIMULATION:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    कुल simulations: {sim_total} | Success: {sim_success} ({sim_rate}%)
    {'🚀 ' + str(sim_success) + ' trades PROFITABLE होते!' if sim_success > 0 else '📊 कोई profitable simulation नहीं अभी तक'}"""

    if reverts:
        report += "\n    Revert reasons:"
        for r, c in list(reverts.items())[:3]:
            report += f"\n      {c}x — {r}"

    report += f"""

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⛽ [D] GAS ECONOMICS:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Average gas: {avg_gas:.1f} Gwei | Min: {data['min_gas']} | Max: {data['max_gas']}
    Per trade cost: ${gas_cost:.4f} | Break-even spread: 0.44%

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎯 [E] MARKET VOLATILITY:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Best spread देखा: {best_spread:.4f}% ({best_sym})
    कुल opportunities (>0.5%): {len(opportunities)}"""

    if best_opps:
        report += "\n    Top opportunities:"
        for opp in best_opps[:3]:
            report += f"\n      {opp.get('sym','?')} — {opp.get('spread_pct',0):.4f}% spread | AI: {opp.get('ai_decision','?')}"

    # Deep insights
    insights = generate_deep_insights(data, elapsed_sec, total_sec)
    report += "\n\n  💡 DEEP INSIGHTS:\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for ins in insights:
        report += f"\n    {ins}"

    report += f"\n\n╚══════════════════════════════════════════════════════════════════╝\n"
    return report


# ── Stress Test Process Manager ────────────────────────────────────────────────
stress_proc = None

def launch_stress_test():
    global stress_proc
    print("\n  🚀 stress_test_harness.py को launch कर रहे हैं...")
    stress_proc = subprocess.Popen(
        [sys.executable, "-u", "stress_test_harness.py", "--hours", str(TEST_HOURS)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
        bufsize=1
    )
    print(f"  ✅ Stress test started (PID: {stress_proc.pid})")
    return stress_proc


def stream_stress_output(proc):
    """Stress test output को console पर दिखाओ।"""
    try:
        for line in proc.stdout:
            print(f"  [HARNESS] {line}", end="")
    except Exception as e:
        print(f"  [!] Output stream error: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  🤖 PHANTOM-X MASTER STRESS TEST RUNNER")
    print("  📊 Telegram Reports: हर 10 मिनट में")
    print("  📋 Console Reports:  हर 1 घंटे में यहाँ")
    print("=" * 70)

    # Check prerequisites
    if not os.path.exists("deployed_contract.txt"):
        print("❌ deployed_contract.txt नहीं मिला! Contract deploy करो पहले।")
        sys.exit(1)
    if not os.path.exists("real_trained_ai_weights.json"):
        print("⚠️ AI weights नहीं मिले। Retraining...")
        os.system(f"{sys.executable} retrain_ai_live.py")

    # Launch stress test
    proc = launch_stress_test()

    # Give it 5 seconds to start and create the directory
    time.sleep(5)

    # Find test dir
    test_dir = find_latest_test_dir()
    if not test_dir:
        print("⚠️ stress_test_* folder नहीं मिला, 10 sec में retry...")
        time.sleep(10)
        test_dir = find_latest_test_dir()

    if not test_dir:
        print("❌ Stress test start नहीं हो सका! Exiting.")
        proc.terminate()
        sys.exit(1)

    print(f"\n  📁 Monitoring: {test_dir}/")

    # Stream output in background thread
    output_thread = threading.Thread(target=stream_stress_output, args=(proc,), daemon=True)
    output_thread.start()

    total_sec   = TEST_HOURS * 3600
    start_time  = time.time()
    report_num  = 0
    hour_num    = 0
    last_telegram_time = start_time
    last_hourly_time   = start_time

    # Send START notification to Telegram
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M IST")
    start_msg = f"""🚀 *PHANTOM\\-X STRESS TEST RESTART*
📅 {now_str}

📋 *Test Parameters:*
• Duration: *{TEST_HOURS:.0f} hours*
• Scan interval: *3 seconds*
• Gas cost: *$0\\.00* \\(eth\\_call only\\)
• Tokens: WETH, WMATIC, WBTC
• Test folder: `{test_dir}/`

🎯 *Test Categories:*
• \\[A\\] Live QS vs UV3 spread tracking
• \\[B\\] AI decision accuracy
• \\[C\\] Contract simulation via eth\\_call
• \\[D\\] Gas economics & profitability
• \\[E\\] Market volatility events

📊 Reports:
• Telegram: हर *10 मिनट* में
• Console: हर *1 घंटे* में

_Stress test background में चल रही है\\.\\.\\._"""

    ok = send_telegram(start_msg)
    print(f"\n  {'✅' if ok else '❌'} Telegram start notification {'भेजा' if ok else 'नहीं भेजा'}")

    # Main reporting loop
    while True:
        time.sleep(30)  # Check every 30 seconds

        # Check if stress test is still running
        proc_status = proc.poll()

        elapsed_sec = time.time() - start_time
        now_time    = time.time()

        # Check if final summary exists (test completed)
        final_done = os.path.exists(f"{test_dir}/final_summary.json")

        # ── Telegram report (every 10 min) ──────────────────────────────────
        if now_time - last_telegram_time >= TELEGRAM_INTERVAL:
            report_num += 1
            last_telegram_time = now_time
            print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] 📱 Telegram report #{report_num} भेज रहे हैं...")
            try:
                msg = build_telegram_report(test_dir, report_num, elapsed_sec, total_sec)
                ok  = send_telegram(msg)
                print(f"  {'✅' if ok else '❌'} Report #{report_num} {'sent' if ok else 'failed'} | Elapsed: {elapsed_sec/3600:.2f}h")
            except Exception as e:
                print(f"  ❌ Report build error: {e}")
                import traceback
                traceback.print_exc()

        # ── Hourly console report (every 1 hour) ────────────────────────────
        if now_time - last_hourly_time >= 3600:
            hour_num += 1
            last_hourly_time = now_time
            print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] 🕐 Hourly report #{hour_num} generate कर रहे हैं...")
            try:
                report = print_hourly_report_here(test_dir, elapsed_sec, total_sec, hour_num)
                print(report)
            except Exception as e:
                print(f"  ❌ Hourly report error: {e}")

        # ── Test completion check ────────────────────────────────────────────
        if final_done or (proc_status is not None and elapsed_sec >= total_sec * 0.95):
            print(f"\n  🎉 Stress test पूरी हो गई!")

            # Final Telegram report
            try:
                final_msg = build_final_telegram_report(test_dir, elapsed_sec)
                ok = send_telegram(final_msg)
                print(f"  {'✅' if ok else '❌'} Final Telegram report {'भेजा' if ok else 'failed'}")
            except Exception as e:
                print(f"  ❌ Final Telegram report error: {e}")

            # Final console report
            try:
                final_console = print_hourly_report_here(test_dir, elapsed_sec, total_sec, hour_num + 1)
                print("\n  📋 FINAL CONSOLE REPORT:")
                print(final_console)
            except Exception as e:
                print(f"  ❌ Final console report error: {e}")

            # Generate HTML report
            try:
                print("\n  📄 HTML report generate कर रहे हैं...")
                result = subprocess.run(
                    [sys.executable, "generate_report.py", test_dir + "/"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    send_telegram(f"📄 *HTML Report Ready\\!*\n`{test_dir}/analysis\\_report.html`\n\nBrowser में खोलो detailed analysis के लिए\\!")
                    print(f"  ✅ HTML report: {test_dir}/analysis_report.html")
                else:
                    print(f"  ⚠️ HTML report error: {result.stderr[:200]}")
            except Exception as e:
                print(f"  ⚠️ HTML report: {e}")

            break

        # ── Process died unexpectedly ────────────────────────────────────────
        if proc_status is not None and elapsed_sec < total_sec * 0.95:
            print(f"\n  ⚠️ Stress test process ended unexpectedly (code: {proc_status})")
            send_telegram(f"⚠️ *Stress test unexpected exit*\nProcess code: {proc_status}\nElapsed: {elapsed_sec/3600:.2f}h")
            break

    print("\n  ✅ Master runner complete.")


if __name__ == "__main__":
    if os.name == "nt":
        import asyncio
        # No asyncio needed here, just run
    main()
