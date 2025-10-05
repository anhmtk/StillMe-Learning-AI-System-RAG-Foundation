#!/usr/bin/env pwsh
# Smoke Test - Windows PowerShell
# Chạy smoke test end-to-end

param(
    [string]$BaseUrl = ""
)

# Tạo thư mục reports nếu chưa có
if (-not (Test-Path "reports")) {
    New-Item -ItemType Directory -Path "reports" -Force | Out-Null
}

# Lấy BASE_URL
if (-not $BaseUrl) {
    if (Test-Path "config\runtime_base_url.txt") {
        $BaseUrl = Get-Content "config\runtime_base_url.txt" -Raw
    } else {
        Write-Error "Không tìm thấy BaseUrl. Chạy compute_base_url.ps1 trước."
        exit 1
    }
}

Write-Host "🧪 Chạy Smoke Test cho: $BaseUrl"

$results = @{
    "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "base_url" = $BaseUrl
    "tests" = @{}
    "overall_status" = "PASS"
}

# Test /livez
Write-Host "🔍 Testing /livez..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/livez" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $results.tests.livez = "PASS"
        Write-Host "✅ /livez: $($response.StatusCode)"
    } else {
        $results.tests.livez = "FAIL"
        $results.overall_status = "FAIL"
        Write-Host "❌ /livez: $($response.StatusCode)"
    }
} catch {
    $results.tests.livez = "FAIL"
    $results.overall_status = "FAIL"
    Write-Host "❌ /livez: $($_.Exception.Message)"
}

# Test /readyz
Write-Host "🔍 Testing /readyz..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/readyz" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $results.tests.readyz = "PASS"
        Write-Host "✅ /readyz: $($response.StatusCode)"
    } else {
        $results.tests.readyz = "FAIL"
        $results.overall_status = "FAIL"
        Write-Host "❌ /readyz: $($response.StatusCode)"
    }
} catch {
    $results.tests.readyz = "FAIL"
    $results.overall_status = "FAIL"
    Write-Host "❌ /readyz: $($_.Exception.Message)"
}

# Test /version
Write-Host "🔍 Testing /version..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/version" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        $results.tests.version = "PASS"
        $results.version_info = $json
        Write-Host "✅ /version: $($response.StatusCode)"
        Write-Host "   Name: $($json.name)"
        Write-Host "   Version: $($json.version)"
    } else {
        $results.tests.version = "FAIL"
        $results.overall_status = "FAIL"
        Write-Host "❌ /version: $($response.StatusCode)"
    }
} catch {
    $results.tests.version = "FAIL"
    $results.overall_status = "FAIL"
    Write-Host "❌ /version: $($_.Exception.Message)"
}

# Test /health (optional)
Write-Host "🔍 Testing /health..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $results.tests.health = "PASS"
        Write-Host "✅ /health: $($response.StatusCode)"
    } else {
        $results.tests.health = "FAIL"
        Write-Host "❌ /health: $($response.StatusCode)"
    }
} catch {
    $results.tests.health = "FAIL"
    Write-Host "❌ /health: $($_.Exception.Message)"
}

# Ghi kết quả vào file
$reportFile = "reports\tailscale_smoke.txt"
$reportContent = @"
=== STILLME TAILSCALE SMOKE TEST REPORT ===
Timestamp: $($results.timestamp)
Base URL: $($results.base_url)
Overall Status: $($results.overall_status)

Test Results:
- /livez: $($results.tests.livez)
- /readyz: $($results.tests.readyz)
- /version: $($results.tests.version)
- /health: $($results.tests.health)

Version Info:
$($results.version_info | ConvertTo-Json -Depth 2)

Server Logs (last 20 lines):
$(if (Test-Path "logs\server.log") { Get-Content "logs\server.log" -Tail 20 } else { "No server log found" })
"@

$reportContent | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host "📊 Kết quả tổng thể: $($results.overall_status)"
Write-Host "📝 Báo cáo đã lưu: $reportFile"

if ($results.overall_status -eq "FAIL") {
    Write-Host "📝 Server logs:"
    if (Test-Path "logs\server.log") {
        Get-Content "logs\server.log" -Tail 20
    }
    exit 1
} else {
    exit 0
}
