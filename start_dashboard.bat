@echo off
echo Starting StillMe IPC Learning Dashboard...
cd /d "%~dp0"
cd dashboards\streamlit
start "StillMe Dashboard" cmd /k "streamlit run integrated_dashboard.py --server.port 8529"
echo Dashboard started at http://localhost:8529
echo Press any key to continue...
pause >nul
