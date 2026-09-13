@echo off
TITLE PhantomX v3 Universal Profit Engine - Single-Click Launcher
COLOR 0A

echo ======================================================================
echo 🚀 PHANTOM-X v3 UNIVERSAL PROFIT ENGINE - SINGLE-CLICK LAUNCHER
echo Owner: Manish
echo Target Ecosystem: Polygon Mainnet (Chain ID 137)
echo Mode: DRY_RUN=true ($0.00 Real Gas Spent | $0.00 Fund Risk)
echo ======================================================================
echo.

cd /d "%~dp0"

echo 1. Checking Python Environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo ✅ Python Environment Verified.
echo.
echo 2. Running Automated Verification Unit Test Suite...
python test_universal_engine.py
if errorlevel 1 (
    echo ❌ Unit tests failed! Check errors before launching.
    pause
    exit /b 1
)

echo ✅ 100% Tests Passed!
echo.
echo 3. Launching 24/7 Universal Harvester Daemon & Telemetry Reporter...
start "PhantomX v3 Harvester Daemon" python -u live_real_rpc_harvester_v3.py
start "PhantomX v3 Telemetry Reporter" python -u telemetry\universal_telemetry_reporter.py

echo.
echo ======================================================================
echo 🎉 PHANTOM-X v3 UNIVERSAL ENGINE SUCCESSFULLY LAUNCHED IN BACKGROUND!
echo Harvester Log: logs\universal_scan_metrics_v3.jsonl
echo Master Log Artifact: PhantomX_v3_Universal_Engine_Master_Log.md
echo ======================================================================
pause
