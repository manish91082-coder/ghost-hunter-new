"""
PhantomX 1-Click Duplicate Process Cleaner (kill_duplicates.py)
---------------------------------------------------------------
Scans and auto-terminates duplicate/orphan PhantomX python processes.
"""

import os
import sys
import logging

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.process_guard import kill_duplicate_processes, get_running_python_pids

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TARGET_SCRIPTS = [
    "phantomx_multiagent_swarm.py",
    "run_247_continuous_shadow_engine.py",
    "start_central_dual_engine.py",
    "live_onchain_hunter.py",
    "real_execution_loop.py"
]

def main():
    print("================================================================================")
    print("PHANTOMX 1-CLICK PROCESS CLEANER (ZERO DUPLICATION GUARD)...")
    print("================================================================================")


    current_pid = os.getpid()
    total_killed = 0

    for script in TARGET_SCRIPTS:
        print(f"Scanning for duplicate instances of '{script}'...")
        killed = kill_duplicate_processes(script, current_pid)
        total_killed += killed

    # Remove stale pid files if present
    for pid_file in ["phantomx_engine.pid", "prevent_sleep.lock"]:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                print(f"Cleaned stale file: {pid_file}")
            except Exception:
                pass

    print("--------------------------------------------------------------------------------")
    print(f"✅ CLEANUP COMPLETE: Terminated {total_killed} orphan/duplicate process(es).")
    print("================================================================================")

if __name__ == "__main__":
    main()
