@echo off
setlocal enabledelayedexpansion
if "%CLARIFICATION_API_URL%"=="" set CLARIFICATION_API_URL=http://localhost:8000/chat
if not exist reports\k6_seal_test mkdir reports\k6_seal_test

echo 🚀 Starting K6 SEAL-GRADE Test for Phase 3 Clarification Core
echo API URL: %CLARIFICATION_API_URL%

k6 run ^
  --summary-export="reports\k6_seal_test\summary.json" ^
  --out json="reports\k6_seal_test\results.json" ^
  load_test\clarification_seal_test.js

echo ✅ K6 test completed