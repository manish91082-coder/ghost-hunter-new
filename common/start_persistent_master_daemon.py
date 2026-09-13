"""
PhantomX Detached Daemon Launcher (start_persistent_master_daemon.py)
====================================================================
Launches master_background_orchestrator.py as an autonomous, detached process.
Guarantees 24/7 background execution on Windows without process group termination.
"""

import sys
import os
import subprocess
import time

sys.stdout.reconfigure(encoding="utf-8")

COMMON_DIR = os.path.abspath(os.path.dirname(__file__))
ORCHESTRATOR_SCRIPT = os.path.join(COMMON_DIR, "master_background_orchestrator.py")
ENGINE_ROOT = os.path.abspath(os.path.join(COMMON_DIR, ".."))
BASE_DIR = os.path.abspath(os.path.join(ENGINE_ROOT, ".."))

def launch_detached_orchestrator():
    print("🚀 [Daemon Launcher] Spawning Master Background Orchestrator in Detached Mode...")
    
    creation_flags = 0
    if os.name == 'nt':
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        [sys.executable, ORCHESTRATOR_SCRIPT, "--mode", "dry_run"],
        cwd=BASE_DIR,
        creationflags=creation_flags,
        close_fds=True
    )
    
    print(f"✅ Master Orchestrator spawned as persistent detached PID: {proc.pid}")
    return proc.pid

if __name__ == "__main__":
    launch_detached_orchestrator()
