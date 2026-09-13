import json, os
from datetime import datetime, timezone

test_dir = 'stress_test_20260905_204526'

def count_jsonl(path):
    if not os.path.exists(path): return 0
    with open(path, encoding='utf-8') as f:
        return sum(1 for l in f if l.strip())

scan_count = count_jsonl(f'{test_dir}/raw_scans.jsonl')
ai_count   = count_jsonl(f'{test_dir}/ai_decisions.jsonl')
opp_count  = count_jsonl(f'{test_dir}/opportunities.jsonl')
sim_count  = count_jsonl(f'{test_dir}/eth_call_results.jsonl')

print(f"scan_rows={scan_count}")
print(f"ai_rows={ai_count}")
print(f"opp_rows={opp_count}")
print(f"sim_rows={sim_count}")

# Analyze raw scans
scans = []
with open(f'{test_dir}/raw_scans.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try: scans.append(json.loads(line))
            except: pass

by_sym = {}
for row in scans:
    sym = row.get('sym','?')
    sp  = row.get('spread_pct', 0)
    gas = row.get('gas_gwei', 0)
    if sym not in by_sym:
        by_sym[sym] = {'spreads':[], 'gas':[]}
    by_sym[sym]['spreads'].append(sp)
    by_sym[sym]['gas'].append(gas)

all_gas = []
for sym, data in by_sym.items():
    spreads = data['spreads']
    gas_list = data['gas']
    all_gas.extend(gas_list)
    avg_sp = sum(spreads)/len(spreads) if spreads else 0
    max_sp = max(spreads) if spreads else 0
    gt05   = sum(1 for s in spreads if s > 0.50)
    gt10   = sum(1 for s in spreads if s > 1.00)
    gt20   = sum(1 for s in spreads if s > 2.00)
    print(f"SYM={sym}|cnt={len(spreads)}|avg={avg_sp:.4f}|max={max_sp:.4f}|gt05={gt05}|gt10={gt10}|gt20={gt20}")

avg_gas = sum(all_gas)/len(all_gas) if all_gas else 0
min_gas = min(all_gas) if all_gas else 0
max_gas = max(all_gas) if all_gas else 0
print(f"GAS|avg={avg_gas:.1f}|min={min_gas:.1f}|max={max_gas:.1f}")

# AI decisions
ai_rows = []
with open(f'{test_dir}/ai_decisions.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try: ai_rows.append(json.loads(line))
            except: pass

decisions = {'EXECUTE':0, 'WAIT':0, 'IGNORE':0}
false_pos = 0
correct   = 0
for row in ai_rows:
    d = row.get('ai_decision','IGNORE')
    decisions[d] = decisions.get(d,0)+1
    if row.get('ai_correct',False): correct += 1
    elif d=='EXECUTE' and not row.get('actually_profitable',False): false_pos += 1

total = sum(decisions.values())
acc = round(correct/max(total,1)*100,1)
exec_c  = decisions.get('EXECUTE',0)
wait_c  = decisions.get('WAIT',0)
ign_c   = decisions.get('IGNORE',0)
print(f"AI|exec={exec_c}|wait={wait_c}|ignore={ign_c}|fp={false_pos}|acc={acc}|total={total}")

# Config
with open(f'{test_dir}/test_config.json') as f:
    cfg = json.load(f)
print(f"CFG|hours={cfg['hours']}")
print(f"CFG|start={cfg['start_time']}")

# Time
start = datetime.fromisoformat(cfg['start_time'])
now   = datetime.now(timezone.utc)
elapsed = (now - start).total_seconds()
remaining = cfg['hours']*3600 - elapsed
pct = min(elapsed/(cfg['hours']*3600)*100, 100)
print(f"TIME|elapsed={elapsed:.0f}|remaining={remaining:.0f}|pct={pct:.1f}")

# Hourly snapshot
if os.path.exists(f'{test_dir}/summary_hourly.json'):
    with open(f'{test_dir}/summary_hourly.json') as f:
        snaps = json.load(f)
    for snap in snaps:
        h = snap.get('hour',0)
        ts = snap.get('total_scans',0)
        gas = snap.get('avg_gas_gwei',0)
        exec_n = snap.get('ai_execute',0)
        print(f"SNAP|hr={h:.2f}|scans={ts}|gas={gas:.0f}|exec={exec_n}")

print("DONE")
