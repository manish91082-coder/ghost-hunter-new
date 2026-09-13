import os
import sys
import psutil

engine_v2_dir = os.path.join(os.path.dirname(__file__), "v2")
sys.path.append(engine_v2_dir)
from telegram_notifier import send_telegram_message

print("Testing Telegram Notification...")
res = send_telegram_message("🚀 *PhantomX Live System Initializing...*\nMaster Orchestrator starting live processes and 10-min Telegram reports.")
print("Telegram test result:", res)

current_pid = os.getpid()
print("Scanning for old python processes to terminate...")
killed = 0
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['pid'] == current_pid:
            continue
        cmdline = ' '.join(proc.info['cmdline'] or [])
        if 'python' in proc.info['name'].lower() and ('flash loan ghost hunter' in cmdline.lower() or 'start_central_dual_engine' in cmdline.lower() or 'live_stream' in cmdline.lower() or 'reporter' in cmdline.lower()):
            print(f"Terminating process {proc.info['pid']}: {cmdline[:70]}...")
            proc.kill()
            killed += 1
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
print(f"Done. Killed {killed} old background processes.")
