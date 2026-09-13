"""
PhantomX Master Dual Engine Orchestrator (start_central_dual_engine.py)
==========================================================================
Launches Central RPC Harvester + V2 Stream Runner + V3 Stream Runner as parallel subprocesses.
Ensures zero duplicate RPC calls, zero PC lag, and complete isolation of V2 and V3 engines.
"""

import sys
import os
import time
import subprocess
import signal
import psutil

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENGINE_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
CENTRAL_HARVESTER_SCRIPT = os.path.join(BASE_DIR, "central_rpc_harvester.py")
V2_RUNNER_SCRIPT         = os.path.join(ENGINE_ROOT, "v2", "live_stream_runner_v2.py")
V3_RUNNER_SCRIPT         = os.path.join(ENGINE_ROOT, "v3", "live_stream_runner_v3.py")
V2_REPORTER_SCRIPT       = os.path.join(ENGINE_ROOT, "v2", "live_10min_reporter_v2.py")
V3_REPORTER_SCRIPT       = os.path.join(ENGINE_ROOT, "v3", "telemetry", "live_10min_reporter_v3.py")

processes = []

def set_low_priority(pid):
    try:
        p = psutil.Process(pid)
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 10)
    except Exception:
        pass

def cleanup_subprocesses(signum=None, frame=None):
    print("\n🛑 [Master Orchestrator] Stopping all dual engine subprocesses...")
    for p, name in processes:
        if p.poll() is None:
            print(f"   Terminating {name} (PID: {p.pid})...")
            p.terminate()
    time.sleep(1)
    for p, name in processes:
        if p.poll() is None:
            p.kill()
    print("✅ All processes stopped gracefully.")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, cleanup_subprocesses)
    signal.signal(signal.SIGTERM, cleanup_subprocesses)

    print("================================================================================")
    print("🚀 PhantomX Central Stream Master Dual Engine Orchestrator")
    print("================================================================================")
    print(f"1. Central RPC Ingestor: {CENTRAL_HARVESTER_SCRIPT}")
    print(f"2. V2 Stream AI Runner:  {V2_RUNNER_SCRIPT}")
    print(f"3. V3 Universal Engine:  {V3_RUNNER_SCRIPT}")
    print(f"4. V2 Telemetry Reporter: {V2_REPORTER_SCRIPT}")
    print(f"5. V3 Telemetry Reporter: {V3_REPORTER_SCRIPT}")
    print("--------------------------------------------------------------------------------")
    print("⚡ Process Priorities: BELOW_NORMAL / IDLE (Zero PC Lag Guarantee)")
    print("📡 RPC Network Calls: 1 Shared Multicall3 Stream (Zero Duplicate Calls)")
    print("================================================================================")

    # 1. Start Central Ingestor
    print("\n[1/5] Launching Central RPC Harvester...")
    p1 = subprocess.Popen([sys.executable, CENTRAL_HARVESTER_SCRIPT], cwd=BASE_DIR)
    set_low_priority(p1.pid)
    processes.append((p1, "Central Harvester", CENTRAL_HARVESTER_SCRIPT, BASE_DIR))
    time.sleep(2)

    # 2. Start V2 Stream Runner
    print("[2/5] Launching V2 Stream Runner...")
    v2_cwd = os.path.join(ENGINE_ROOT, "v2")
    p2 = subprocess.Popen([sys.executable, V2_RUNNER_SCRIPT], cwd=v2_cwd)
    set_low_priority(p2.pid)
    processes.append((p2, "V2 Runner", V2_RUNNER_SCRIPT, v2_cwd))
    time.sleep(1)

    # 3. Start V3 Stream Runner
    print("[3/5] Launching V3 Universal Engine Stream Runner...")
    v3_cwd = os.path.join(ENGINE_ROOT, "v3")
    p3 = subprocess.Popen([sys.executable, V3_RUNNER_SCRIPT], cwd=v3_cwd)
    set_low_priority(p3.pid)
    processes.append((p3, "V3 Runner", V3_RUNNER_SCRIPT, v3_cwd))
    time.sleep(1)

    # 4. Start V2 Reporter
    print("[4/5] Launching V2 Telemetry & Telegram Reporter...")
    p4 = subprocess.Popen([sys.executable, V2_REPORTER_SCRIPT], cwd=v2_cwd)
    set_low_priority(p4.pid)
    processes.append((p4, "V2 Reporter", V2_REPORTER_SCRIPT, v2_cwd))
    time.sleep(1)

    # 5. Start V3 Reporter
    print("[5/6] Launching V3 Telemetry & Telegram Reporter...")
    v3_telemetry_cwd = os.path.join(ENGINE_ROOT, "v3", "telemetry")
    p5 = subprocess.Popen([sys.executable, V3_REPORTER_SCRIPT], cwd=v3_telemetry_cwd)
    set_low_priority(p5.pid)
    processes.append((p5, "V3 Reporter", V3_REPORTER_SCRIPT, v3_telemetry_cwd))
    time.sleep(1)

    # 6. Start Profit Watcher Guard Engine
    WATCHER_SCRIPT = os.path.join(BASE_DIR, "profit_watcher_guard.py")
    print("[6/6] Launching Profit Watcher Guard & Real-Time SGD Auto-Tuner...")
    p6 = subprocess.Popen([sys.executable, WATCHER_SCRIPT], cwd=BASE_DIR)
    set_low_priority(p6.pid)
    processes.append((p6, "Profit Watcher Guard", WATCHER_SCRIPT, BASE_DIR))

    print("\n✅ All 6 parallel processes running (including Profit Watcher Guard)! Press Ctrl+C to terminate all.\n")

    while True:
        for p, name, script, cwd in list(processes):
            if p.poll() is not None:
                print(f"⚠️ Process {name} (PID {p.pid}) exited with code {p.returncode}. Restarting...")
                new_p = subprocess.Popen([sys.executable, script], cwd=cwd)
                set_low_priority(new_p.pid)
                processes.remove((p, name, script, cwd))
                processes.append((new_p, name, script, cwd))
        time.sleep(5)

if __name__ == "__main__":
    main()
