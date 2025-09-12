#!/usr/bin/env pwsh
# Wait for Server Ready - Windows PowerShell
# Chờ server sẵn sàng với health check

param(
    [string]$BaseUrl = "",
    [int]$MaxAttempts = 60,
    [int]$DelayMs = 500
)

if (-not $BaseUrl) {
    if (Test-Path "config\runtime_base_url.txt") {
        $BaseUrl = Get-Content "config\runtime_base_url.txt" -Raw
    } else {
        Write-Error "Không tìm thấy BaseUrl. Chạy compute_base_url.ps1 trước."
        exit 1
    }
}

Write-Host "⏳ Chờ server sẵn sàng tại: $BaseUrl"
Write-Host "🔄 Tối đa $MaxAttempts lần thử, mỗi lần cách nhau $DelayMs ms"

for ($i = 1; $i -le $MaxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/readyz" -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Server đã sẵn sàng! (lần thử $i/$MaxAttempts)"
            exit 0
        }
    } catch {
        # Server chưa sẵn sàng, tiếp tục chờ
    }
    
    if ($i -lt $MaxAttempts) {
        Start-Sleep -Milliseconds $DelayMs
        Write-Host "⏳ Lần thử $i/$MaxAttempts - Server chưa sẵn sàng..."
    }
}

Write-Error "❌ Server không sẵn sàng sau $MaxAttempts lần thử"
Write-Host "📝 Kiểm tra logs: Get-Content logs\server.log -Tail 20"
exit 1