@echo off
REM Clean test artifacts and cache files for Windows

echo 🧹 Cleaning test artifacts...

REM Remove pytest cache
if exist .pytest_cache rmdir /s /q .pytest_cache

REM Remove Python cache
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"

REM Remove coverage reports
if exist reports\coverage rmdir /s /q reports\coverage
if exist coverage rmdir /s /q coverage
if exist htmlcov rmdir /s /q htmlcov

REM Remove test reports
if exist reports\test_report.html del reports\test_report.html
if exist reports\junit.xml del reports\junit.xml

echo ✅ Test artifacts cleaned!
