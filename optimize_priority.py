import psutil
import os

print("⚡ Enforcing IDLE Priority Class on all Flash Loan Engine processes...")
count = 0
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        if 'python' in p.info['name'].lower() and ('v2_v3_engine' in cmd.lower() or 'flash loan ghost hunter' in cmd.lower()):
            p.nice(psutil.IDLE_PRIORITY_CLASS if os.name == 'nt' else 19)
            print(f"  [+] PID {p.info['pid']} priority set to IDLE.")
            count += 1
    except Exception as e:
        pass

print(f"✅ Priority optimization complete. Adjusted {count} processes.")
