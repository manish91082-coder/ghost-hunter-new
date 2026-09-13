@echo off
chcp 65001 >nul
title PhantomX - Production Launcher

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║         PHANTOM-X Flash Loan Arbitrage Bot               ║
echo ║         Production Launcher v1.0                         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ── STEP 1: Check Python ──────────────────────────────────────
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found! Install Python 3.10+ and try again.
    pause
    exit /b 1
)
echo   OK: Python found.

REM ── STEP 2: Check .env ────────────────────────────────────────
echo [2/6] Checking environment config...
if not exist ".env" (
    echo   ERROR: .env file not found!
    echo   Create .env with GHOSTHUNTER_DEV_PRIVATE_KEY=0x...
    pause
    exit /b 1
)
echo   OK: .env found.

REM ── STEP 3: Check deployed contract ───────────────────────────
echo [3/6] Checking deployed contract...
if not exist "deployed_contract.txt" (
    echo   WARNING: deployed_contract.txt not found!
    echo   Run: python live_mainnet_deployer.py
    pause
    exit /b 1
)
for /f %%i in (deployed_contract.txt) do set CONTRACT=%%i
echo   OK: Contract = %CONTRACT%

REM ── STEP 4: Run test suite ────────────────────────────────────
echo [4/6] Running test suite...
python test_phantomx.py >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Tests failed! Run 'python test_phantomx.py' to see details.
    pause
    exit /b 1
)
echo   OK: All tests passed.

REM ── STEP 5: Check DRY_RUN setting ────────────────────────────
echo [5/6] Checking DRY_RUN mode...
findstr /i "DRY_RUN=true" .env >nul 2>&1
if not errorlevel 1 (
    echo.
    echo   ============================================================
    echo   SAFE MODE: DRY_RUN=true
    echo   Bot will SCAN but NOT send any transactions.
    echo   To go live: change DRY_RUN=false in .env
    echo   ============================================================
    echo.
) else (
    echo.
    echo   ============================================================
    echo   WARNING: DRY_RUN=false — LIVE EXECUTION MODE!
    echo   Real transactions will be sent. Real gas will be spent.
    echo   ============================================================
    echo.
    set /p CONFIRM="Type YES to confirm live execution: "
    if /i not "%CONFIRM%"=="YES" (
        echo   Aborted. Set DRY_RUN=true in .env for safe mode.
        pause
        exit /b 0
    )
)

REM ── STEP 6: Launch bot with persistent file logging ──────────
echo [6/6] Launching PhantomX...
echo.
if not exist "logs" mkdir logs
echo   Logging output to logs\live_production.log
echo   Press Ctrl+C to stop the bot at any time.
echo.
powershell -Command "python -u live_production_runner.py | Tee-Object -FilePath logs\live_production.log"
pause
