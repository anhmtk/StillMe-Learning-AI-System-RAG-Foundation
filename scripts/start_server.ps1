#!/usr/bin/env pwsh
# Start StillMe Server - Windows PowerShell
# Khởi động server detached với logging

# Tạo thư mục logs nếu chưa có
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Xác định server script
$SERVER_SCRIPT = "stable_ai_server.py"
if (-not (Test-Path $SERVER_SCRIPT)) {
    $SERVER_SCRIPT = "framework.py"
}

if (-not (Test-Path $SERVER_SCRIPT)) {
    Write-Error "Không tìm thấy server script: $SERVER_SCRIPT"
    exit 1
}

# Dừng server cũ nếu có
& "$PSScriptRoot\stop_server.ps1" 2>$null

# Khởi động server detached
Write-Host "🚀 Khởi động StillMe server detached..."
$process = Start-Process -FilePath "python.exe" -ArgumentList "-u", $SERVER_SCRIPT -RedirectStandardOutput "logs\server.log" -RedirectStandardError "logs\server_error.log" -NoNewWindow -PassThru

if ($process) {
    Write-Host "✅ Server đã khởi động với PID: $($process.Id)"
    Write-Host "📝 Logs được ghi vào: logs\server.log"
    
    # Lưu PID để dễ dừng sau này
    $process.Id | Out-File -FilePath "logs\server.pid" -Encoding UTF8 -NoNewline
} else {
    Write-Error "❌ Không thể khởi động server"
    exit 1
}
