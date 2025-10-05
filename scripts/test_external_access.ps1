#!/usr/bin/env pwsh
# Test External Access - Windows PowerShell
# Test server accessibility từ thiết bị khác

param(
    [string]$BaseUrl = ""
)

if (-not $BaseUrl) {
    if (Test-Path "config\runtime_base_url.txt") {
        $BaseUrl = Get-Content "config\runtime_base_url.txt" -Raw
    } else {
        Write-Error "Không tìm thấy BaseUrl. Chạy compute_base_url.ps1 trước."
        exit 1
    }
}

Write-Host "🌐 Testing External Access to: $BaseUrl"
Write-Host "=" * 50

# Test /livez
Write-Host "🔍 Testing Liveness (/livez)..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/livez" -Method GET -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Liveness: $($response.StatusCode) OK"
    } else {
        Write-Host "❌ Liveness: $($response.StatusCode)"
        exit 1
    }
} catch {
    Write-Host "❌ Liveness: $($_.Exception.Message)"
    exit 1
}

# Test /readyz
Write-Host "🔍 Testing Readiness (/readyz)..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/readyz" -Method GET -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Readiness: $($response.StatusCode) OK"
    } else {
        Write-Host "❌ Readiness: $($response.StatusCode)"
        exit 1
    }
} catch {
    Write-Host "❌ Readiness: $($_.Exception.Message)"
    exit 1
}

# Test /version
Write-Host "🔍 Testing Version (/version)..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/version" -Method GET -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        Write-Host "✅ Version: $($response.StatusCode) OK"
        Write-Host "   Name: $($json.name)"
        Write-Host "   Version: $($json.version)"
    } else {
        Write-Host "❌ Version: $($response.StatusCode)"
        exit 1
    }
} catch {
    Write-Host "❌ Version: $($_.Exception.Message)"
    exit 1
}

# Test /health
Write-Host "🔍 Testing Health (/health)..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health: $($response.StatusCode) OK"
    } else {
        Write-Host "❌ Health: $($response.StatusCode)"
        exit 1
    }
} catch {
    Write-Host "❌ Health: $($_.Exception.Message)"
    exit 1
}

Write-Host "=" * 50
Write-Host "🎉 Server is accessible from external devices!"
Write-Host "📱 Desktop/Mobile apps can connect to: $BaseUrl"

# Ghi kết quả vào file
$reportFile = "reports\external_access_test.txt"
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$reportContent = "=== EXTERNAL ACCESS TEST REPORT ===`n"
$reportContent += "Timestamp: $timestamp`n"
$reportContent += "Base URL: $BaseUrl`n"
$reportContent += "Overall Status: PASS`n`n"
$reportContent += "Test Results:`n"
$reportContent += "- Liveness: PASS`n"
$reportContent += "- Readiness: PASS`n"
$reportContent += "- Version: PASS`n"
$reportContent += "- Health: PASS`n`n"
$reportContent += "Server is accessible from external devices!`n"
$reportContent += "Desktop/Mobile apps can connect to: $BaseUrl"

$reportContent | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "Report saved: $reportFile"

exit 0