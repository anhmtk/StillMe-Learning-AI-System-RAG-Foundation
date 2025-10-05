#!/usr/bin/env pwsh
# Stop StillMe Server - Windows PowerShell
# Dừng server process

Write-Host "🛑 Đang dừng StillMe server..."

# Đọc PID từ file nếu có
$pidFile = "logs\server.pid"
if (Test-Path $pidFile) {
    $serverPid = Get-Content $pidFile -Raw
    if ($serverPid -match '^\d+$') {
        try {
            $process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $serverPid -Force
                Write-Host "✅ Đã dừng server với PID: $serverPid"
            }
        } catch {
            # Process không tồn tại
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

# Tìm và dừng process python chạy server script
$serverProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*stable_ai_server.py*" -or 
    $_.CommandLine -like "*framework.py*"
}

foreach ($process in $serverProcesses) {
    try {
        Stop-Process -Id $process.Id -Force
        Write-Host "✅ Đã dừng server process PID: $($process.Id)"
    } catch {
        Write-Warning "Không thể dừng process PID: $($process.Id)"
    }
}

# Tìm process sử dụng port 8000
try {
    $portProcesses = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    foreach ($portPid in $portProcesses) {
        try {
            $process = Get-Process -Id $portPid -ErrorAction SilentlyContinue
            if ($process -and $process.ProcessName -eq "python") {
                Stop-Process -Id $portPid -Force
                Write-Host "✅ Đã dừng process sử dụng port 8000, PID: $portPid"
            }
        } catch {
            # Process không tồn tại
        }
    }
} catch {
    # Không tìm thấy process nào sử dụng port 8000
}

Write-Host "🏁 Hoàn thành dừng server"
