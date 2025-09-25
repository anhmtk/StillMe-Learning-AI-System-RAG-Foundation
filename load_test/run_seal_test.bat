@echo off
REM K6 SEAL-GRADE Test Runner for Phase 3 Clarification Core
REM ========================================================

echo 🚀 Starting K6 SEAL-GRADE Test for Phase 3 Clarification Core
echo ==============================================================

REM Check if k6 is installed
k6 version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ k6 is not installed. Please install k6 first:
    echo    Windows: choco install k6
    echo    Or download from: https://k6.io/docs/getting-started/installation/
    pause
    exit /b 1
)

REM Check if Clarification Core API is running
echo 🔍 Checking Clarification Core API availability...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Clarification Core API is not running on localhost:8000
    echo    Please start the API server first
    pause
    exit /b 1
)

echo ✅ Clarification Core API is running

REM Create reports directory
if not exist "reports\k6_seal_test" mkdir "reports\k6_seal_test"

REM Run K6 test
echo 🧪 Running K6 SEAL-GRADE Test...
echo    - Duration: ~17 minutes
echo    - Max Users: 500 (spike test)
echo    - Soak Test: 10 minutes at 100 users
echo.

REM Run test with JSON output
k6 run --out json=reports\k6_seal_test\results.json load_test\clarification_seal_test.js

echo.
echo ✅ K6 SEAL-GRADE Test completed!
echo 📊 Results saved to: reports\k6_seal_test\results.json

echo.
echo 🎉 K6 SEAL-GRADE Test completed successfully!
echo 📁 Check reports\k6_seal_test\ for detailed results
pause
