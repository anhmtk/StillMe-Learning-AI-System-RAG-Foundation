# quick-start.ps1 - One-click setup script for StillMe (Windows PowerShell)

Write-Host "🧠 StillMe - Self-Evolving AI System" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop:" -ForegroundColor Red
    Write-Host "   https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ docker-compose found" -ForegroundColor Green
} catch {
    Write-Host "❌ docker-compose not found. Trying 'docker compose'..." -ForegroundColor Yellow
    try {
        docker compose version | Out-Null
        Write-Host "✅ Docker Compose (v2) found" -ForegroundColor Green
    } catch {
        Write-Host "❌ docker compose not available. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found. Creating from env.example..." -ForegroundColor Yellow
    if (Test-Path env.example) {
        Copy-Item env.example .env
        Write-Host "✅ Created .env file. Please edit it with your API keys!" -ForegroundColor Green
    } else {
        Write-Host "❌ env.example not found. Creating basic .env..." -ForegroundColor Yellow
        @"
# API Keys
DEEPSEEK_API_KEY=sk-REPLACE_ME
OPENAI_API_KEY=sk-REPLACE_ME

# Learning Configuration
LEARNING_INTERVAL_HOURS=4
AUTO_APPROVAL_THRESHOLD=0.8
COMMUNITY_MIN=0.6
COMMUNITY_MAX=0.8
"@ | Out-File -FilePath .env -Encoding UTF8
        Write-Host "✅ Created basic .env file. Please add your API keys!" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env file with your API keys before continuing!" -ForegroundColor Yellow
    Read-Host "Press Enter after editing .env file"
}

# Create data directory if it doesn't exist
if (-not (Test-Path data)) {
    New-Item -ItemType Directory -Path data | Out-Null
}

Write-Host "🚀 Starting StillMe with Docker Compose..." -ForegroundColor Cyan
Write-Host ""

# Start services
try {
    docker-compose up -d
} catch {
    docker compose up -d
}

Write-Host ""
Write-Host "✅ StillMe is starting up!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "🔌 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Backend is still starting... Please wait a moment." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 StillMe is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "To stop: docker-compose down" -ForegroundColor Cyan
Write-Host ""

