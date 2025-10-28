@echo off
REM AgentDev Development Script for Windows
REM SEAL-grade test infrastructure commands

if "%1"=="help" goto help
if "%1"=="test.quick" goto test_quick
if "%1"=="test.seal" goto test_seal
if "%1"=="up.test" goto up_test
if "%1"=="down.test" goto down_test
if "%1"=="load.baseline" goto load_baseline
if "%1"=="load.egress" goto load_egress
if "%1"=="clean" goto clean
if "%1"=="install" goto install
if "%1"=="lint" goto lint
if "%1"=="status" goto status
goto help

:help
echo AgentDev Development Commands
echo =============================
echo.
echo Available commands:
echo   dev.bat help          - Show this help
echo   dev.bat install       - Install dependencies
echo   dev.bat test.quick    - Run quick tests
echo   dev.bat test.seal     - Run SEAL-grade tests
echo   dev.bat up.test       - Start test infrastructure
echo   dev.bat down.test     - Stop test infrastructure
echo   dev.bat load.baseline - Run baseline load test
echo   dev.bat load.egress   - Run egress guard load test
echo   dev.bat lint          - Run linting
echo   dev.bat clean         - Clean temporary files
echo   dev.bat status        - Show system status
echo.
goto end

:install
echo Installing dependencies...
pip install -r requirements.txt
pip install pytest pytest-cov pytest-html flake8 mypy mutmut hypothesis
if exist package.json npm install
echo ✅ Dependencies installed
goto end

:test_quick
echo Running quick tests...
python -m pytest -q -m "not seal and not slow" --tb=short
goto end

:test_seal
echo Running SEAL-grade tests...
python -m pytest -q -m "seal" --tb=short
goto end

:up_test
echo Starting test infrastructure...
docker-compose -f docker-compose.test.yml up -d redis otel-collector prometheus
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul
echo ✅ Test infrastructure is ready
echo Prometheus: http://localhost:9090
echo OTEL Collector: http://localhost:8888/metrics
goto end

:down_test
echo Stopping test infrastructure...
docker-compose -f docker-compose.test.yml down -v
echo ✅ Test infrastructure stopped
goto end

:load_baseline
echo Running baseline load test...
k6 run load_test/baseline.js
goto end

:load_egress
echo Running egress guard load test...
k6 run load_test/with_egress_guard.js
goto end

:lint
echo Running linting...
flake8 agentdev/ tests/ --max-line-length=120 --ignore=E203,W503
mypy agentdev/ --ignore-missing-imports --no-strict-optional
if exist package.json npm run lint
goto end

:clean
echo Cleaning temporary files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .coverage del .coverage
if exist htmlcov rmdir /s /q htmlcov
if exist mutmut.html del mutmut.html
echo ✅ Cleanup completed
goto end

:status
echo System Status
echo =============
python --version
if exist node.exe node --version
docker --version
if exist k6.exe k6 version
echo.
echo Test infrastructure:
docker-compose -f docker-compose.test.yml ps
echo.
echo Recent test results:
if exist reports dir reports
goto end

:end
