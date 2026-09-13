import json
import os
import numpy as np
from datetime import datetime

v2_path = r'c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter\v2_v3_engine\v2\live_scan_metrics_v2.jsonl'
v3_path = r'c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter\v2_v3_engine\v3\logs\live_scan_metrics_v3.jsonl'

def analyze(path, name):
    if not os.path.exists(path):
        print(f"=== {name} Metrics === File Missing!")
        return
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    lines.append(json.loads(line))
                except Exception:
                    pass
    print(f"=== {name} Metrics ===")
    print(f"Total Accumulated Scan Records: {len(lines):,}")
    if lines:
        print(f"First Scan Timestamp: {lines[0].get('timestamp')}")
        print(f"Latest Scan Timestamp: {lines[-1].get('timestamp')}")
        recent = lines[-500:]
        spreads = [m.get('spread_pct', m.get('effective_spread_pct', 0.0)) for m in recent]
        execs = [m for m in recent if m.get('decision') == 'EXECUTE']
        pnls = [m.get('net_pnl_usd', m.get('expected_net_pnl_usd', 0.0)) for m in execs]
        loans = [m.get('optimal_loan_usd', 0.0) for m in recent if m.get('optimal_loan_usd', 0.0) > 0]
        
        print(f"Last 500 Scans Analytics:")
        print(f"  - Avg Spread: {np.mean(spreads):.4f}% | Min Spread: {np.min(spreads):.4f}% | Max Spread: {np.max(spreads):.4f}%")
        print(f"  - AI Decisions Breakdown: EXECUTE={len(execs)}, WAIT/IGNORE={len(recent)-len(execs)}")
        print(f"  - Avg Dynamic Loan L*: ${np.mean(loans):,.2f} USD (Min: ${np.min(loans) if loans else 0:,.2f} | Max: ${np.max(loans) if loans else 0:,.2f})")
        print(f"  - Period Net Profit: ${sum(pnls):,.2f} USD")
    print()

analyze(v2_path, "V2 MVP Engine")
analyze(v3_path, "V3 Universal Engine")
