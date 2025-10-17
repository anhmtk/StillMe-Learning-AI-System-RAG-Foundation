# StillMe Auto-Start Learning System
# PowerShell script for Windows

Write-Host "Starting StillMe Auto-Start Learning System..." -ForegroundColor Green
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# Create logs directory
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
}

# Start the learning system
python start_learning_system.py

Write-Host "StillMe Learning System started." -ForegroundColor Green
Read-Host "Press Enter to continue"