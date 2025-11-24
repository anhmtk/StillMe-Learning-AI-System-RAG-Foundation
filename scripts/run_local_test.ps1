# Quick script to run tests against local backend (PowerShell)
# Usage: .\scripts\run_local_test.ps1

# Set port (default: 8000, can be overridden)
$port = if ($env:STILLME_PORT) { $env:STILLME_PORT } else { "8000" }
$env:STILLME_API_BASE = "http://localhost:$port"
$env:STILLME_PORT = $port

Write-Host "Testing against local backend on port $port"
Write-Host "   Make sure backend is running: python start_backend.py"
Write-Host ""

python scripts\test_transparency_and_evidence.py
