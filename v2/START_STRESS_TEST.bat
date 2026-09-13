@echo off
chcp 65001 >nul
title PhantomX — Stress Test Launcher

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║       PHANTOM-X GAS-FREE LIVE STRESS TEST                   ║
echo ║  3 Hours ^| $0 Gas ^| Live Data ^| Telegram Alerts Har 10 Min  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ── Step 1: Python check ─────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found! Install Python 3.10+
    pause & exit /b 1
)
echo   OK: Python found.

REM ── Step 2: .env check ───────────────────────────────────────────
echo [2/6] Checking .env config...
if not exist ".env" (
    echo   ERROR: .env not found!
    pause & exit /b 1
)
echo   OK: .env found.

REM ── Step 3: Contract check ────────────────────────────────────────
echo [3/6] Checking deployed contract...
if not exist "deployed_contract.txt" (
    echo   ERROR: deployed_contract.txt not found!
    pause & exit /b 1
)
for /f %%i in (deployed_contract.txt) do set CONTRACT=%%i
echo   OK: Contract = %CONTRACT%

REM ── Step 4: Weights check ────────────────────────────────────────
echo [4/6] Checking AI weights...
if not exist "real_trained_ai_weights.json" (
    echo   WARNING: AI weights not found! Running retraining...
    python retrain_ai_live.py
    if errorlevel 1 (
        echo   ERROR: Retraining failed!
        pause & exit /b 1
    )
) else (
    python -c "import json; d=json.load(open('real_trained_ai_weights.json')); v=d.get('_metadata',{}).get('version','v1'); print(f'  OK: Weights loaded ({v})')"
)

REM ── Step 5: Run diagnostic ────────────────────────────────────────
echo [5/6] Running quick AI diagnostic...
python -c "from ai_brain import PhantomAIBrain; b=PhantomAIBrain(); d,l,p,_=b.analyze_scenario(2450,2475,100000,280); print(f'  OK: AI Brain working. Decision={d}, Profit=${p:.2f}')"
if errorlevel 1 (
    echo   ERROR: AI Brain not working!
    pause & exit /b 1
)

REM ── Step 6: Launch stress test + Telegram reporter ────────────────
echo [6/6] Launching stress test + Telegram reporter...
echo.
echo   ┌─────────────────────────────────────────────────────────┐
echo   │  Window 1: 3-hour stress test (this window)             │
echo   │  Window 2: Telegram reporter (separate window)          │
echo   │  Reports: Every 10 minutes on Telegram                  │
echo   │  Gas: $0.00                                              │
echo   │  Ctrl+C to stop early                                    │
echo   └─────────────────────────────────────────────────────────┘
echo.

REM Launch Telegram reporter in a separate window
start "PhantomX Telegram Reporter" python -u telegram_stress_reporter.py

REM Small delay so reporter starts first
timeout /t 3 /nobreak >nul

REM Launch main stress test (foreground)
python -u stress_test_harness.py --hours 3

echo.
echo   ── Test completed! Generating report... ──
python generate_report.py
echo.
echo   Open analysis_report.html in the stress_test_* folder.
pause
