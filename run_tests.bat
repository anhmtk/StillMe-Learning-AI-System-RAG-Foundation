@echo off
REM Windows batch script to run NicheRadar v1.5 tests
REM Usage: run_tests.bat [unit|integration|e2e|all|quick]

echo 🧪 NicheRadar v1.5 Test Runner
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if pytest is available
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pytest is not installed. Installing...
    pip install -r requirements-test.txt
    if errorlevel 1 (
        echo ❌ Failed to install test dependencies
        pause
        exit /b 1
    )
)

REM Check if Node.js is available (for Playwright)
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Playwright is installed
npx playwright --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Playwright is not installed. Installing...
    npm install
    npx playwright install
    if errorlevel 1 (
        echo ❌ Failed to install Playwright
        pause
        exit /b 1
    )
)

REM Create reports directory
if not exist "reports" mkdir reports
if not exist "logs" mkdir logs

REM Parse command line arguments
set "test_type=%1"
if "%test_type%"=="" set "test_type=all"

REM Run tests based on type
if "%test_type%"=="unit" (
    echo 🚀 Running unit tests...
    python scripts/run_tests.py --unit
) else if "%test_type%"=="integration" (
    echo 🚀 Running integration tests...
    python scripts/run_tests.py --integration
) else if "%test_type%"=="e2e" (
    echo 🚀 Running E2E tests...
    python scripts/run_tests.py --e2e
) else if "%test_type%"=="quick" (
    echo 🚀 Running quick tests (unit + integration)...
    python scripts/run_tests.py --quick
) else (
    echo 🚀 Running all tests with reports...
    python scripts/run_tests.py --all
)

if errorlevel 1 (
    echo ❌ Tests failed
    pause
    exit /b 1
) else (
    echo ✅ Tests completed successfully
    echo 📊 Reports available in reports/ directory
    echo 📋 Test summary: reports/test_summary.json
)

pause
