@echo off
echo Starting StillMe Auto-Start Learning System...
cd /d "%~dp0"

REM Create logs directory
if not exist "logs" mkdir logs

REM Start the learning system
python start_learning_system.py

echo StillMe Learning System started.
pause