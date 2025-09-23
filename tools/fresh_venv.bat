@echo off
REM Fresh virtual environment setup for testing on Windows

echo 🧹 Creating fresh virtual environment...

REM Remove old venv if exists
if exist .venv (
    echo Removing old .venv...
    rmdir /s /q .venv
)

REM Create new venv
echo Creating new .venv...
python -m venv .venv

REM Activate venv
echo Activating .venv...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install test dependencies
echo Installing test dependencies...
pip install -r requirements-test.txt

REM Check encoding
echo Checking Python encoding...
python -c "import sys; print(f'Default encoding: {sys.getdefaultencoding()}')"

echo ✅ Fresh virtual environment ready!
echo To activate: .venv\Scripts\activate.bat
