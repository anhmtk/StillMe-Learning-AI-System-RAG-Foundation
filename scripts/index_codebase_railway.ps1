# PowerShell script to index StillMe codebase on Railway via API
# Usage: .\scripts\index_codebase_railway.ps1 -BackendUrl "https://stillme-backend-production.up.railway.app" -ApiKey "YOUR_API_KEY"

param(
    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = "https://stillme-backend-production.up.railway.app",
    
    [Parameter(Mandatory=$false)]
    [string]$ApiKey = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

# Ensure UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=" -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "📚 StillMe Codebase Indexing for Railway" -ForegroundColor Cyan
Write-Host "=" -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if API key is provided
if ([string]::IsNullOrEmpty($ApiKey)) {
    $ApiKey = $env:STILLME_API_KEY
    if ([string]::IsNullOrEmpty($ApiKey)) {
        Write-Host "⚠️  API Key not provided!" -ForegroundColor Yellow
        Write-Host "   Please provide API key via:" -ForegroundColor Yellow
        Write-Host "   1. -ApiKey parameter" -ForegroundColor Yellow
        Write-Host "   2. STILLME_API_KEY environment variable" -ForegroundColor Yellow
        Write-Host ""
        $ApiKey = Read-Host "Enter your STILLME_API_KEY (or press Enter to skip authentication)"
    }
}

# Build request headers
$headers = @{
    "Content-Type" = "application/json"
}

if (-not [string]::IsNullOrEmpty($ApiKey)) {
    $headers["X-API-Key"] = $ApiKey
    Write-Host "✅ Using API key for authentication" -ForegroundColor Green
} else {
    Write-Host "⚠️  No API key provided - request may fail if authentication is required" -ForegroundColor Yellow
}

# Build request body
$body = @{
    force = $Force.IsPresent
} | ConvertTo-Json

Write-Host ""
Write-Host "🌐 Backend URL: $BackendUrl" -ForegroundColor Cyan
Write-Host "📊 Force re-index: $($Force.IsPresent)" -ForegroundColor Cyan
Write-Host ""

# Check current stats first
Write-Host "📊 Checking current codebase stats..." -ForegroundColor Cyan
try {
    $statsUrl = "$BackendUrl/api/codebase/stats"
    $statsResponse = Invoke-RestMethod -Uri $statsUrl -Method Get -Headers $headers -ErrorAction Stop
    
    Write-Host "   Current chunks: $($statsResponse.total_chunks)" -ForegroundColor Yellow
    Write-Host "   Status: $($statsResponse.status)" -ForegroundColor Yellow
    
    if ($statsResponse.total_chunks -gt 0 -and -not $Force.IsPresent) {
        Write-Host ""
        Write-Host "⚠️  Collection already has chunks!" -ForegroundColor Yellow
        Write-Host "   Use -Force to re-index anyway" -ForegroundColor Yellow
        Write-Host ""
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "❌ Indexing cancelled by user" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "   ⚠️  Could not get stats: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Starting codebase indexing..." -ForegroundColor Cyan
Write-Host "   This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Make API request
$indexUrl = "$BackendUrl/api/codebase/index"
try {
    $response = Invoke-RestMethod -Uri $indexUrl -Method Post -Headers $headers -Body $body -ErrorAction Stop
    
    Write-Host ""
    Write-Host "=" -NoNewline
    Write-Host ("=" * 59) -ForegroundColor Green
    Write-Host "✅ INDEXING COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=" -NoNewline
    Write-Host ("=" * 59) -ForegroundColor Green
    Write-Host ""
    
    if ($response.status -eq "success") {
        Write-Host "📊 Indexing Statistics:" -ForegroundColor Cyan
        Write-Host "   Total files indexed: $($response.stats.files_indexed)" -ForegroundColor White
        Write-Host "   Total chunks created: $($response.stats.chunks_created)" -ForegroundColor White
        Write-Host "   Final collection count: $($response.final_count)" -ForegroundColor White
        Write-Host ""
        
        if ($response.stats.directories) {
            Write-Host "   Breakdown by directory:" -ForegroundColor Cyan
            foreach ($dir in $response.stats.directories) {
                Write-Host "     - $($dir.directory): $($dir.files) files, $($dir.chunks) chunks" -ForegroundColor White
            }
        }
        
        Write-Host ""
        Write-Host "🎉 StillMe Codebase Assistant is now ready!" -ForegroundColor Green
        Write-Host "   You can now query the codebase via /api/codebase/query" -ForegroundColor Green
    } elseif ($response.status -eq "skipped") {
        Write-Host "ℹ️  Indexing skipped: $($response.message)" -ForegroundColor Yellow
        Write-Host "   Current count: $($response.current_count)" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  Unexpected response: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Yellow
    }
    
    exit 0
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: Indexing failed!" -ForegroundColor Red
    Write-Host ""
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   HTTP Status: $statusCode" -ForegroundColor Red
        
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            $errorJson = $errorBody | ConvertFrom-Json
            
            Write-Host "   Error: $($errorJson.detail)" -ForegroundColor Red
        } catch {
            Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        if ($statusCode -eq 401 -or $statusCode -eq 403) {
            Write-Host ""
            Write-Host "💡 Authentication failed. Please check:" -ForegroundColor Yellow
            Write-Host "   1. API key is correct" -ForegroundColor Yellow
            Write-Host "   2. STILLME_API_KEY is set on Railway" -ForegroundColor Yellow
        } elseif ($statusCode -eq 404) {
            Write-Host ""
            Write-Host "💡 Endpoint not found. Please check:" -ForegroundColor Yellow
            Write-Host "   1. Backend URL is correct" -ForegroundColor Yellow
            Write-Host "   2. Backend is deployed with latest code" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    exit 1
}

