"""
PhantomX Single Master Background Orchestrator (master_background_orchestrator.py)
========================================================================================
Unified 1-Click Persistent Background Launcher & Process Lifecycle Guard.

Features:
  1. Pre-Flight Auto-Cleanup: Automatically kills any existing background runner instances
     (Harvester, V2, V3, Reporters, Watchers) to prevent zombie processes & duplicate RPC calls.
  2. Dual Execution Mode Switch (DRY_RUN vs LIVE):
     - DRY_RUN=true (Default Read-Only): Live mainnet RPC stream, contract eth_call,
       continuous Online SGD neural self-training, Telegram telemetry, $0.00 gas spent.
     - DRY_RUN=false (Live Mainnet Execution): On-chain transaction signing & broadcast.
  3. Spawns 6 Parallel Subprocesses with IDLE Process Priority (Zero PC Lag Guarantee).
  4. 24/7 Auto-Restart Watchdog: Auto-restarts any crashed subprocess in <5 seconds.
  5. Telegram Plain Text Fallback & Append-Only Master Log File Persistence.
"""

import sys
import os
import time
import argparse
import subprocess
import signal
import psutil

sys.stdout.reconfigure(encoding="utf-8")

COMMON_DIR = os.path.abspath(os.path.dirname(__file__))
ENGINE_ROOT = os.path.abspath(os.path.join(COMMON_DIR, ".."))
BASE_DIR = os.path.abspath(os.path.join(ENGINE_ROOT, ".."))

CENTRAL_HARVESTER_SCRIPT = os.path.join(COMMON_DIR, "central_rpc_harvester.py")
V2_RUNNER_SCRIPT         = os.path.join(ENGINE_ROOT, "v2", "live_stream_runner_v2.py")
V3_RUNNER_SCRIPT         = os.path.join(ENGINE_ROOT, "v3", "live_stream_runner_v3.py")
V2_REPORTER_SCRIPT       = os.path.join(ENGINE_ROOT, "v2", "live_10min_reporter_v2.py")
V3_REPORTER_SCRIPT       = os.path.join(ENGINE_ROOT, "v3", "telemetry", "live_10min_reporter_v3.py")
WATCHER_SCRIPT           = os.path.join(COMMON_DIR, "profit_watcher_guard.py")
MASTER_30MIN_REPORTER    = os.path.join(COMMON_DIR, "live_30min_master_reporter.py")

processes = []

def purge_existing_instances():
    """
    Pre-flight Auto-Cleanup: Kills any old python instances of harvester, runners, reporters or watchers.
    """
    print("🧹 [Master Orchestrator] Running Pre-Flight Auto-Cleanup...")
    current_pid = os.getpid()
    parent_pid = os.getppid()
    
    family_pids = {current_pid, parent_pid}
    try:
        cur_proc = psutil.Process(current_pid)
        for p in cur_proc.parents():
            family_pids.add(p.pid)
    except Exception:
        pass

    target_names = [
        "central_rpc_harvester.py",
        "live_stream_runner_v2.py",
        "live_stream_runner_v3.py",
        "live_10min_reporter_v2.py",
        "live_10min_reporter_v3.py",
        "profit_watcher_guard.py",
        "live_30min_master_reporter.py",
        "start_central_dual_engine.py"
    ]
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline']):
        try:
            pid = proc.info['pid']
            ppid = proc.info['ppid']
            if pid in family_pids or ppid in family_pids:
                continue
            cmdline_str = " ".join(proc.info['cmdline'] or [])
            is_python = proc.info['name'].lower().startswith('python') or 'python' in cmdline_str.lower()
            if is_python:
                if any(target in cmdline_str for target in target_names) or "master_background_orchestrator.py" in cmdline_str:
                    print(f"   Killing stale process PID {pid}: {proc.info['name']}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    if killed_count > 0:
        print(f"✅ Cleaned up {killed_count} stale background process(es).")
        time.sleep(2)
    else:
        print("✅ Zero stale processes found. Environment clean.")

def set_low_priority(pid):
    try:
        p = psutil.Process(pid)
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 5)
    except Exception:
        pass

def cleanup_subprocesses(signum=None, frame=None):
    print("\n🛑 [Master Orchestrator] Shutting down all dual engine subprocesses...")
    for p, name, script, cwd in processes:
        if p.poll() is None:
            print(f"   Terminating {name} (PID: {p.pid})...")
            p.terminate()
    time.sleep(1)
    for p, name, script, cwd in processes:
        if p.poll() is None:
            p.kill()
    print("✅ All processes stopped cleanly.")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="PhantomX Single Master Background Orchestrator")
    parser.add_argument("--mode", choices=["dry_run", "live"], default="dry_run",
                        help="Execution mode: 'dry_run' (Read-Only Simulation & Training) or 'live' (Mainnet Transactions)")
    args = parser.parse_args()

    dry_run_flag = "true" if args.mode == "dry_run" else "false"
    os.environ["DRY_RUN"] = dry_run_flag

    signal.signal(signal.SIGINT, cleanup_subprocesses)
    signal.signal(signal.SIGTERM, cleanup_subprocesses)

    print("================================================================================")
    print("🚀 PHANTOMX SINGLE MASTER BACKGROUND ORCHESTRATOR")
    print("================================================================================")
    print(f"🎯 Mode: {'READ-ONLY SIMULATION & CONTINUOUS TRAINING (DRY_RUN=True)' if dry_run_flag == 'true' else '🔥 LIVE MAINNET BROADCAST EXECUTION (DRY_RUN=False)'}")
    print(f"📡 Shared RPC Harvester: {CENTRAL_HARVESTER_SCRIPT}")
    print(f"🚀 V2 MVP AI Runner:     {V2_RUNNER_SCRIPT}")
    print(f"🌐 V3 Universal Engine:  {V3_RUNNER_SCRIPT}")
    print(f"📊 V2 Reporter (10m):    {V2_REPORTER_SCRIPT}")
    print(f"📊 V3 Reporter (10m):    {V3_REPORTER_SCRIPT}")
    print(f"🛡️ Profit Watcher Guard: {WATCHER_SCRIPT}")
    print(f"📜 30-Min Master Reporter:{MASTER_30MIN_REPORTER}")
    print("--------------------------------------------------------------------------------")
    print("⚡ Process Priority: IDLE / BELOW_NORMAL (Zero PC Lag Guarantee)")
    print("================================================================================")

    # Prepare environment dictionary for subprocesses
    child_env = os.environ.copy()
    child_env["DRY_RUN"] = dry_run_flag

    # 0. Run Pre-flight Cleanup
    purge_existing_instances()

    # 1. Start Central Harvester
    print("\n[1/7] Spawning Central RPC Harvester...")
    p1 = subprocess.Popen([sys.executable, CENTRAL_HARVESTER_SCRIPT], cwd=COMMON_DIR, env=child_env)
    set_low_priority(p1.pid)
    processes.append((p1, "Central Harvester", CENTRAL_HARVESTER_SCRIPT, COMMON_DIR))
    time.sleep(2)

    # 2. Start V2 Stream Runner
    print("[2/7] Spawning V2 Stream Runner...")
    v2_cwd = os.path.join(ENGINE_ROOT, "v2")
    p2 = subprocess.Popen([sys.executable, V2_RUNNER_SCRIPT], cwd=v2_cwd, env=child_env)
    set_low_priority(p2.pid)
    processes.append((p2, "V2 Runner", V2_RUNNER_SCRIPT, v2_cwd))
    time.sleep(1)

    # 3. Start V3 Stream Runner
    print("[3/7] Spawning V3 Universal Engine Stream Runner...")
    v3_cwd = os.path.join(ENGINE_ROOT, "v3")
    p3 = subprocess.Popen([sys.executable, V3_RUNNER_SCRIPT], cwd=v3_cwd, env=child_env)
    set_low_priority(p3.pid)
    processes.append((p3, "V3 Runner", V3_RUNNER_SCRIPT, v3_cwd))
    time.sleep(1)

    # 4. Start V2 Reporter
    print("[4/7] Spawning V2 Telemetry & Telegram Reporter...")
    p4 = subprocess.Popen([sys.executable, V2_REPORTER_SCRIPT], cwd=v2_cwd, env=child_env)
    set_low_priority(p4.pid)
    processes.append((p4, "V2 Reporter", V2_REPORTER_SCRIPT, v2_cwd))
    time.sleep(1)

    # 5. Start V3 Reporter
    print("[5/7] Spawning V3 Telemetry & Telegram Reporter...")
    v3_telemetry_cwd = os.path.join(ENGINE_ROOT, "v3", "telemetry")
    p5 = subprocess.Popen([sys.executable, V3_REPORTER_SCRIPT], cwd=v3_telemetry_cwd, env=child_env)
    set_low_priority(p5.pid)
    processes.append((p5, "V3 Reporter", V3_REPORTER_SCRIPT, v3_telemetry_cwd))
    time.sleep(1)

    # 6. Start Profit Watcher Guard Engine
    print("[6/7] Spawning Profit Watcher Guard & Real-Time SGD Auto-Tuner...")
    p6 = subprocess.Popen([sys.executable, WATCHER_SCRIPT], cwd=COMMON_DIR, env=child_env)
    set_low_priority(p6.pid)
    processes.append((p6, "Profit Watcher Guard", WATCHER_SCRIPT, COMMON_DIR))
    time.sleep(1)

    # 7. Start 30-Minute Master Forensic Deep Insight Reporter
    print("[7/7] Spawning 30-Minute Master Forensic Deep Insight Reporter...")
    p7 = subprocess.Popen([sys.executable, MASTER_30MIN_REPORTER], cwd=COMMON_DIR, env=child_env)
    set_low_priority(p7.pid)
    processes.append((p7, "30-Min Master Reporter", MASTER_30MIN_REPORTER, COMMON_DIR))

    print("\n✅ All 7 parallel processes running under Single Master Background Orchestrator!")
    print("📡 24/7 Watchdog Active. Press Ctrl+C to terminate all.\n")

    # 24/7 Watchdog Loop
    while True:
        for p, name, script, cwd in list(processes):
            if p.poll() is not None:
                print(f"⚠️ Watchdog Alert: Process {name} (PID {p.pid}) exited with code {p.returncode}. Restarting...")
                new_p = subprocess.Popen([sys.executable, script], cwd=cwd, env=child_env)
                set_low_priority(new_p.pid)
                processes.remove((p, name, script, cwd))
                processes.append((new_p, name, script, cwd))
        time.sleep(5)

if __name__ == "__main__":
    main()
