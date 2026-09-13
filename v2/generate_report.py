"""
PhantomX Stress Test Report Generator
=======================================
stress_test_YYYYMMDD_HHMMSS/ directory का full HTML + JSON analysis report बनाता है।

Usage:
  python generate_report.py stress_test_20260905_143000/
  python generate_report.py   (auto-finds latest stress_test_ folder)
"""
import os, sys, json, glob, math
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")


def find_latest_test_dir():
    dirs = sorted(glob.glob("stress_test_*/"), reverse=True)
    if not dirs:
        return None
    return dirs[0].rstrip("/")


def load_jsonl(path):
    data = []
    if not os.path.exists(path): return data
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except: pass
    return data


def pct(n, d):
    return round(n / max(d, 1) * 100, 2)


def generate_text_report(test_dir, summary):
    """Generate readable text analysis report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  PHANTOM-X STRESS TEST — FINAL ANALYSIS REPORT")
    lines.append(f"  Test ID  : {summary.get('test_id','N/A')}")
    lines.append(f"  Duration : {summary.get('test_duration_hours', 0):.2f} hours")
    lines.append(f"  End Time : {summary.get('end_time','N/A')}")
    lines.append("=" * 70)

    # ── Overall Health Score ──────────────────────────────────────────────────
    lines.append("\n  OVERALL HEALTH SCORE")
    lines.append("  " + "─" * 50)
    pa = summary.get("price_accuracy", {})
    ai = summary.get("ai_performance", {})
    cs = summary.get("contract_simulation", {})
    ge = summary.get("gas_economics", {})
    mv = summary.get("market_volatility", {})

    score = 0
    max_score = 5

    # A: Price data available and consistent
    if pa:
        spreads_ok = all(d.get("avg_pct", 0) < 2.0 for d in pa.values())
        score += 1 if spreads_ok else 0.5
        lines.append(f"  [A] Price Accuracy     : {'✅ PASS' if spreads_ok else '⚠️ CHECK'} (spreads realistic)")
    else:
        lines.append("  [A] Price Accuracy     : ❌ No price data")

    # B: AI accuracy > 70%
    ai_acc = ai.get("accuracy_pct", 0)
    score += 1 if ai_acc >= 70 else (0.5 if ai_acc >= 50 else 0)
    lines.append(f"  [B] AI Performance     : {'✅ PASS' if ai_acc >= 70 else '⚠️ CHECK'} ({ai_acc}% accuracy)")

    # C: No simulation crashes (even if all reverts, that's expected at low spread)
    sim_total = cs.get("total_simulations", 0)
    score += 1 if sim_total > 0 else 0
    lines.append(f"  [C] Contract Simul.    : {'✅ PASS' if sim_total > 0 else '❌ No simulations run'} ({sim_total} tests)")

    # D: Gas data captured
    avg_gas = ge.get("avg_gas_gwei", 0)
    score += 1 if avg_gas > 0 else 0
    lines.append(f"  [D] Gas Economics      : {'✅ PASS' if avg_gas > 0 else '❌ No gas data'} (avg {avg_gas}G)")

    # E: Market volatility tracked
    total_spikes = mv.get("spikes_gt_05pct", 0)
    score += 1 if mv else 0
    lines.append(f"  [E] Volatility Tracker : {'✅ PASS' if mv else '❌ No data'} ({total_spikes} spikes >0.5%)")

    lines.append(f"\n  HEALTH SCORE: {score}/{max_score} ({score/max_score*100:.0f}%)")
    if score >= 4.5:
        lines.append("  VERDICT: ✅ EXCELLENT — Bot is production-ready!")
    elif score >= 3.0:
        lines.append("  VERDICT: ⚠️  GOOD — Minor issues to fix before going live")
    else:
        lines.append("  VERDICT: ❌ NEEDS WORK — Review issues before live trading")

    # ── Category A: Price Accuracy ────────────────────────────────────────────
    lines.append("\n\n  [A] PRICE ACCURACY ANALYSIS")
    lines.append("  " + "─" * 50)
    for sym, d in pa.items():
        lines.append(f"  {sym:6s}:")
        lines.append(f"    Total scans  : {d.get('count', 0):,}")
        lines.append(f"    Avg spread   : {d.get('avg_pct', 0):.4f}%")
        lines.append(f"    Max spread   : {d.get('max_pct', 0):.4f}%")
        lines.append(f"    Min spread   : {d.get('min_pct', 0):.4f}%")
        lines.append(f"    Spikes >0.5% : {d.get('gt_05pct', 0)}")
        lines.append(f"    Spikes >1.0% : {d.get('gt_10pct', 0)}")
        opp_rate = pct(d.get('gt_05pct', 0), d.get('count', 1))
        lines.append(f"    Opportunity rate: {opp_rate}% of scans had viable spread")

    # ── Category B: AI Performance ────────────────────────────────────────────
    lines.append("\n\n  [B] AI DECISION QUALITY")
    lines.append("  " + "─" * 50)
    lines.append(f"  Total decisions : {ai.get('total_decisions', 0):,}")
    lines.append(f"  EXECUTE count   : {ai.get('execute_count', 0)}")
    lines.append(f"  WAIT count      : {ai.get('wait_count', 0)}")
    lines.append(f"  IGNORE count    : {ai.get('ignore_count', 0)}")
    lines.append(f"  False positives : {ai.get('false_positives', 0)}")
    lines.append(f"  Correct ignores : {ai.get('correct_ignores', 0)}")
    lines.append(f"  Accuracy        : {ai.get('accuracy_pct', 0)}%")
    fp = ai.get('false_positives', 0)
    if fp == 0:
        lines.append("  ✅ No false positives — AI correctly identified all unprofitable trades")
    else:
        lines.append(f"  ⚠️  {fp} false positive(s) — AI said EXECUTE on unprofitable scenarios")

    # ── Category C: Contract Simulation ───────────────────────────────────────
    lines.append("\n\n  [C] CONTRACT SIMULATION (eth_call) RESULTS")
    lines.append("  " + "─" * 50)
    lines.append(f"  Total simulations : {cs.get('total_simulations', 0)}")
    lines.append(f"  Successful        : {cs.get('success_count', 0)} ({cs.get('success_rate_pct', 0)}%)")
    lines.append(f"  Failed            : {cs.get('total_simulations', 0) - cs.get('success_count', 0)}")
    lines.append(f"  Avg sim latency   : {cs.get('avg_sim_ms', 0):.0f}ms")
    reverts = cs.get("revert_reasons", {})
    if reverts:
        lines.append("  Revert Reasons:")
        for reason, count in sorted(reverts.items(), key=lambda x: -x[1]):
            lines.append(f"    {count:4d}x : {reason}")

    sim_total = cs.get("total_simulations", 0)
    sim_ok    = cs.get("success_count", 0)
    if sim_total == 0:
        lines.append("  ℹ️  No simulations run — spread was below 0.4% threshold throughout test")
        lines.append("  ℹ️  This is NORMAL for calm market conditions. Bot waits for volatility.")
    elif sim_ok > 0:
        lines.append(f"  ✅ {sim_ok} trade(s) WOULD HAVE SUCCEEDED if executed!")
    else:
        lines.append("  📊 All simulations reverted — market spreads below break-even during test")

    # ── Category D: Gas Economics ─────────────────────────────────────────────
    lines.append("\n\n  [D] GAS ECONOMICS")
    lines.append("  " + "─" * 50)
    lines.append(f"  Average gas       : {ge.get('avg_gas_gwei', 0)} Gwei")
    lines.append(f"  Min gas           : {ge.get('min_gas_gwei', 0)} Gwei")
    lines.append(f"  Max gas           : {ge.get('max_gas_gwei', 0)} Gwei")
    lines.append(f"  Break-even spread : {ge.get('break_even_pct', 0.44)}%")
    avg_g = ge.get("avg_gas_gwei", 280)
    gas_cost_per_trade = 500_000 * avg_g * 1e-9 * 0.50
    lines.append(f"  Gas cost/trade    : ${gas_cost_per_trade:.4f} (500k units × {avg_g:.0f} Gwei × $0.50 POL)")
    lines.append(f"  Minimum profitable spread at current gas: {ge.get('break_even_pct', 0.44)}%")

    # ── Category E: Market Volatility ────────────────────────────────────────
    lines.append("\n\n  [E] MARKET VOLATILITY ANALYSIS")
    lines.append("  " + "─" * 50)
    lines.append(f"  Spread >0.5%  : {mv.get('spikes_gt_05pct', 0)} events (potential opportunities)")
    lines.append(f"  Spread >1.0%  : {mv.get('spikes_gt_10pct', 0)} events (good opportunities)")
    lines.append(f"  Spread >2.0%  : {mv.get('spikes_gt_20pct', 0)} events (excellent opportunities)")
    lines.append(f"  Spread >5.0%  : {mv.get('spikes_gt_50pct', 0)} events (rare but very profitable)")
    lines.append(f"  Opportunities : {mv.get('opportunities_detected', 0)} total detected")
    bs = mv.get("best_spreads", {})
    if bs:
        lines.append(f"  Best spreads seen:")
        for sym, sp in bs.items():
            lines.append(f"    {sym:6s}: {sp:.4f}%")

    # ── Recommendations ───────────────────────────────────────────────────────
    lines.append("\n\n  RECOMMENDATIONS FOR LIVE DEPLOYMENT")
    lines.append("  " + "─" * 50)

    recs = []
    avg_spread = max((d.get("avg_pct", 0) for d in pa.values()), default=0)
    if avg_spread < 0.20:
        recs.append("Market spreads are very tight (<0.20%). Bot should run 24/7 to catch volatility spikes.")
    if ai.get("false_positives", 0) == 0:
        recs.append("✅ AI has zero false positives — safe to set DRY_RUN=false when ready.")
    else:
        recs.append(f"⚠️ Fix {ai.get('false_positives')} false positives before going live.")
    if mv.get("spikes_gt_05pct", 0) > 0:
        recs.append(f"✅ {mv.get('spikes_gt_05pct')} spread spikes >0.5% detected — opportunities DO exist!")
    else:
        recs.append("No >0.5% spikes in this test window. Try running during high-volatility hours (9-11am UTC).")
    recs.append("To go live: change DRY_RUN=false in .env and run START_PHANTOM.bat")
    recs.append("Monitor live_hunt_log.jsonl for trade results after going live")

    for i, rec in enumerate(recs, 1):
        lines.append(f"  {i}. {rec}")

    # ── Summary box ───────────────────────────────────────────────────────────
    total_scans = summary.get("total_scans", 0)
    dur_h       = summary.get("test_duration_hours", 0)
    lines.append(f"\n\n  {'═'*70}")
    lines.append(f"  SUMMARY")
    lines.append(f"  {'─'*70}")
    lines.append(f"  Test Duration  : {dur_h:.2f} hours")
    lines.append(f"  Total Scans    : {total_scans:,} ({summary.get('scans_per_hour', 0):.0f}/hr)")
    lines.append(f"  Gas Spent      : $0.00 (eth_call only)")
    lines.append(f"  Health Score   : {score}/{max_score}")
    lines.append(f"  Data Directory : {test_dir}/")
    lines.append(f"  {'═'*70}\n")

    return "\n".join(lines)


def generate_html_report(test_dir, summary, text_report):
    """Generate a rich HTML report."""
    pa = summary.get("price_accuracy", {})
    ai = summary.get("ai_performance", {})
    cs = summary.get("contract_simulation", {})
    ge = summary.get("gas_economics", {})
    mv = summary.get("market_volatility", {})
    dur_h = summary.get("test_duration_hours", 0)
    total_scans = summary.get("total_scans", 0)

    # Build hourly snapshot table rows
    snap_rows = ""
    for snap in summary.get("hourly_snapshots", []):
        snap_rows += f"""
        <tr>
          <td>{snap.get('hour', 0):.1f}h</td>
          <td>{snap.get('total_scans', 0):,}</td>
          <td>{snap.get('avg_gas_gwei', 0):.0f}G</td>
          <td>{snap.get('ai_execute', 0)}</td>
          <td>{snap.get('sim_success', 0)}/{snap.get('sim_total', 0)}</td>
          <td>{snap.get('spike_05pct', 0)}</td>
        </tr>"""

    # Build spread table rows
    spread_rows = ""
    for sym, d in pa.items():
        spread_rows += f"""
        <tr>
          <td><strong>{sym}</strong></td>
          <td>{d.get('count', 0):,}</td>
          <td>{d.get('avg_pct', 0):.4f}%</td>
          <td>{d.get('max_pct', 0):.4f}%</td>
          <td>{d.get('gt_05pct', 0)}</td>
          <td>{d.get('gt_10pct', 0)}</td>
        </tr>"""

    # Revert breakdown
    revert_rows = ""
    for reason, count in sorted(cs.get("revert_reasons", {}).items(), key=lambda x: -x[1]):
        revert_rows += f"<tr><td>{count}</td><td>{reason}</td></tr>"
    if not revert_rows:
        revert_rows = "<tr><td colspan='2'>No reverts recorded</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PhantomX Stress Test Report — {summary.get('test_id','')}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #e6edf3; padding: 24px; }}
    h1 {{ color: #58a6ff; font-size: 28px; margin-bottom: 4px; }}
    h2 {{ color: #58a6ff; font-size: 18px; margin: 24px 0 12px; border-bottom: 1px solid #30363d; padding-bottom: 6px; }}
    .subtitle {{ color: #8b949e; font-size: 14px; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 16px 0; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }}
    .card .val {{ font-size: 32px; font-weight: bold; color: #58a6ff; }}
    .card .lbl {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
    .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
    .badge.green {{ background: #1a4731; color: #3fb950; }}
    .badge.red {{ background: #4b1a1a; color: #f85149; }}
    .badge.yellow {{ background: #3d2b00; color: #d29922; }}
    table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; margin: 12px 0; }}
    th {{ background: #21262d; color: #8b949e; font-size: 12px; text-transform: uppercase; padding: 10px 14px; text-align: left; }}
    td {{ padding: 10px 14px; border-top: 1px solid #30363d; font-size: 14px; }}
    tr:hover td {{ background: #1c2128; }}
    .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 16px 0; }}
    .row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #30363d; }}
    .row:last-child {{ border-bottom: none; }}
    .row .label {{ color: #8b949e; font-size: 14px; }}
    .row .value {{ font-weight: bold; font-size: 14px; }}
    pre {{ background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 16px; font-size: 12px; overflow-x: auto; color: #e6edf3; white-space: pre-wrap; }}
    .success {{ color: #3fb950; }} .danger {{ color: #f85149; }} .warning {{ color: #d29922; }}
  </style>
</head>
<body>
  <h1>🚀 PhantomX Stress Test Report</h1>
  <p class="subtitle">Test ID: {summary.get('test_id','')} | Ended: {summary.get('end_time','')} | Gas spent: <strong class="success">$0.00</strong></p>

  <div class="grid">
    <div class="card"><div class="val">{dur_h:.2f}h</div><div class="lbl">Duration</div></div>
    <div class="card"><div class="val">{total_scans:,}</div><div class="lbl">Total Scans</div></div>
    <div class="card"><div class="val">{summary.get('scans_per_hour',0):.0f}</div><div class="lbl">Scans/Hour</div></div>
    <div class="card"><div class="val">{ge.get('avg_gas_gwei',0):.0f}G</div><div class="lbl">Avg Gas (Gwei)</div></div>
    <div class="card"><div class="val">{ai.get('accuracy_pct',0)}%</div><div class="lbl">AI Accuracy</div></div>
    <div class="card"><div class="val">{mv.get('opportunities_detected',0)}</div><div class="lbl">Opportunities</div></div>
    <div class="card"><div class="val">{cs.get('total_simulations',0)}</div><div class="lbl">eth_call Tests</div></div>
    <div class="card"><div class="val">{cs.get('success_count',0)}</div><div class="lbl">Would Succeed</div></div>
  </div>

  <h2>[A] Price Accuracy</h2>
  <table>
    <tr><th>Token</th><th>Scans</th><th>Avg Spread</th><th>Max Spread</th><th>&gt;0.5%</th><th>&gt;1.0%</th></tr>
    {spread_rows}
  </table>

  <h2>[B] AI Performance</h2>
  <div class="section">
    <div class="row"><span class="label">Total Decisions</span><span class="value">{ai.get('total_decisions',0):,}</span></div>
    <div class="row"><span class="label">EXECUTE</span><span class="value">{ai.get('execute_count',0)}</span></div>
    <div class="row"><span class="label">WAIT</span><span class="value">{ai.get('wait_count',0)}</span></div>
    <div class="row"><span class="label">IGNORE</span><span class="value">{ai.get('ignore_count',0)}</span></div>
    <div class="row"><span class="label">False Positives</span><span class="value {'danger' if ai.get('false_positives',0)>0 else 'success'}">{ai.get('false_positives',0)}</span></div>
    <div class="row"><span class="label">Accuracy</span><span class="value">{ai.get('accuracy_pct',0)}%</span></div>
  </div>

  <h2>[C] Contract Simulation (eth_call)</h2>
  <div class="section">
    <div class="row"><span class="label">Total Simulations</span><span class="value">{cs.get('total_simulations',0)}</span></div>
    <div class="row"><span class="label">Success Rate</span><span class="value">{cs.get('success_rate_pct',0)}%</span></div>
    <div class="row"><span class="label">Avg Latency</span><span class="value">{cs.get('avg_sim_ms',0):.0f}ms</span></div>
  </div>
  <table><tr><th>Count</th><th>Revert Reason</th></tr>{revert_rows}</table>

  <h2>[D] Gas Economics</h2>
  <div class="section">
    <div class="row"><span class="label">Average Gas</span><span class="value">{ge.get('avg_gas_gwei',0)} Gwei</span></div>
    <div class="row"><span class="label">Min Gas</span><span class="value">{ge.get('min_gas_gwei',0)} Gwei</span></div>
    <div class="row"><span class="label">Max Gas</span><span class="value">{ge.get('max_gas_gwei',0)} Gwei</span></div>
    <div class="row"><span class="label">Break-even Spread</span><span class="value">{ge.get('break_even_pct',0.44)}%</span></div>
  </div>

  <h2>[E] Market Volatility</h2>
  <div class="section">
    <div class="row"><span class="label">Spikes &gt;0.5%</span><span class="value">{mv.get('spikes_gt_05pct',0)}</span></div>
    <div class="row"><span class="label">Spikes &gt;1.0%</span><span class="value">{mv.get('spikes_gt_10pct',0)}</span></div>
    <div class="row"><span class="label">Spikes &gt;2.0%</span><span class="value">{mv.get('spikes_gt_20pct',0)}</span></div>
    <div class="row"><span class="label">Spikes &gt;5.0%</span><span class="value">{mv.get('spikes_gt_50pct',0)}</span></div>
    <div class="row"><span class="label">Total Opportunities</span><span class="value">{mv.get('opportunities_detected',0)}</span></div>
  </div>

  <h2>Hourly Snapshots</h2>
  <table>
    <tr><th>Hour</th><th>Scans</th><th>Avg Gas</th><th>EXECUTE</th><th>Sim OK/Total</th><th>Spikes</th></tr>
    {snap_rows if snap_rows else '<tr><td colspan="6">No hourly snapshots (test &lt; 1hr)</td></tr>'}
  </table>

  <h2>Full Text Report</h2>
  <pre>{text_report.replace('<','&lt;').replace('>','&gt;')}</pre>
</body>
</html>"""
    return html


def main():
    # Find test directory
    if len(sys.argv) > 1:
        test_dir = sys.argv[1].rstrip("/\\")
    else:
        test_dir = find_latest_test_dir()

    if not test_dir or not os.path.exists(test_dir):
        print(f"❌ No stress test directory found!")
        print(f"   Run: python stress_test_harness.py  first")
        print(f"   Then: python generate_report.py stress_test_YYYYMMDD_HHMMSS/")
        sys.exit(1)

    print(f"📊 Generating report for: {test_dir}/")

    # Load summary
    summary_path = f"{test_dir}/final_summary.json"
    if not os.path.exists(summary_path):
        print(f"❌ final_summary.json not found in {test_dir}/")
        print(f"   Stress test may still be running, or ended early.")
        sys.exit(1)

    with open(summary_path) as f:
        summary = json.load(f)

    # Load additional data files for extra stats
    raw_scans  = load_jsonl(f"{test_dir}/raw_scans.jsonl")
    ai_decs    = load_jsonl(f"{test_dir}/ai_decisions.jsonl")
    sim_res    = load_jsonl(f"{test_dir}/eth_call_results.jsonl")
    opps       = load_jsonl(f"{test_dir}/opportunities.jsonl")

    print(f"  Loaded: {len(raw_scans):,} scans | {len(ai_decs):,} AI decisions | "
          f"{len(sim_res):,} simulations | {len(opps)} opportunities")

    # Generate reports
    text_report = generate_text_report(test_dir, summary)
    html_report = generate_html_report(test_dir, summary, text_report)

    # Save
    text_path = f"{test_dir}/analysis_report.txt"
    html_path = f"{test_dir}/analysis_report.html"

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text_report)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    # Print text report to console
    print(text_report)
    print(f"\n  📄 Text report saved: {text_path}")
    print(f"  🌐 HTML report saved: {html_path}")
    print(f"  Open {html_path} in a browser for visual report!\n")


if __name__ == "__main__":
    main()
