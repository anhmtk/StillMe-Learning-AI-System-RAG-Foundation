#!/usr/bin/env pwsh
# Detect Server Port - Windows PowerShell
# Tìm port mà server đang chạy từ logs

$logFile = "logs\server_error.log"
if (Test-Path $logFile) {
    $logContent = Get-Content $logFile -Raw
    if ($logContent -match "Uvicorn running on http://0\.0\.0\.0:(\d+)") {
        $port = $matches[1]
        Write-Output $port
        exit 0
    }
}

# Fallback: tìm process python sử dụng port
try {
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -eq "0.0.0.0" }
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($process -and $process.ProcessName -eq "python") {
            Write-Output $conn.LocalPort
            exit 0
        }
    }
} catch {
    # Không tìm thấy
}

Write-Output "8000"
exit 0
