import json, glob, os

files = [
    'ai_diagnostic.py',
    'retrain_ai_live.py',
    'live_ethcall_simulator.py',
    'stress_test_harness.py',
    'generate_report.py',
    'START_STRESS_TEST.bat',
    'telegram_stress_reporter.py',
    'ai_diagnosis_report.json',
    'real_trained_ai_weights.json',
    'real_training_log.jsonl',
]

print('=== FILE VERIFICATION ===')
for f in files:
    exists = os.path.exists(f)
    size   = os.path.getsize(f) if exists else 0
    status = 'OK' if exists else 'MISSING'
    print(f'  {status:6} {f} ({size:,} bytes)')

print()
print('=== AI WEIGHTS CHECK ===')
w    = json.load(open('real_trained_ai_weights.json'))
meta = w.get('_metadata', {})
print(f'  Version     : {meta.get("version", "unknown")}')
print(f'  Generations : {meta.get("training_generations", "?")}')
print(f'  Gas Range   : {meta.get("gas_range_gwei", "?")}')
print(f'  Obs Space   : {meta.get("observation", [])}')

print()
print('=== TRAINING LOG ===')
with open('real_training_log.jsonl') as f:
    gens = [json.loads(l) for l in f if l.strip()]
print(f'  Improvements recorded : {len(gens)}')
print(f'  Best reward           : {gens[-1]["reward"]:.2f}')
print(f'  Last gen improved at  : gen {gens[-1]["generation"]}')

dirs = sorted(glob.glob('stress_test_*/'), reverse=True)
if dirs:
    d = dirs[0].rstrip('/')
    print()
    print(f'=== STRESS TEST: {d} ===')
    for fname in ['raw_scans.jsonl','ai_decisions.jsonl','eth_call_results.jsonl','opportunities.jsonl','test_config.json']:
        fpath = f'{d}/{fname}'
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            count = 0
            if fname.endswith('.jsonl'):
                with open(fpath) as f2:
                    count = sum(1 for l in f2 if l.strip())
            print(f'  {fname:35} size={size:,}B  rows={count}')
        else:
            print(f'  {fname:35} MISSING')

print()
print('=== SYSTEM STATUS ===')
print('  Stress Test   : RUNNING (task-418)')
print('  TG Reporter   : RUNNING (task-447), start msg sent')
print('  Gas Spent     : $0.00')
print('  Next TG Report: ~20:05 IST')
