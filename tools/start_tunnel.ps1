# StillMe SSH Reverse Tunnel Script for Windows
# Tạo SSH reverse tunnel từ Local PC đến VPS
param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIp,
    
    [Parameter(Mandatory=$false)]
    [string]$VpsUser = "root",
    
    [Parameter(Mandatory=$false)]
    [int]$LocalPort = 1216,
    
    [Parameter(Mandatory=$false)]
    [int]$RemotePort = 1216
)

Write-Host "🚀 Starting StillMe SSH Reverse Tunnel..." -ForegroundColor Green
Write-Host "📡 Local: 127.0.0.1:$LocalPort -> VPS: $VpsIp:$RemotePort" -ForegroundColor Cyan
Write-Host "🔒 Security: HMAC authentication enabled" -ForegroundColor Yellow
Write-Host "=" * 50

# Check if SSH is available
try {
    $sshVersion = ssh -V 2>&1
    Write-Host "✅ SSH found: $sshVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ SSH not found. Please install OpenSSH or use WSL." -ForegroundColor Red
    exit 1
}

# Create tunnel command
$tunnelCmd = "ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -N -R $RemotePort`:127.0.0.1:$LocalPort $VpsUser@$VpsIp"

Write-Host "🔧 Tunnel command: $tunnelCmd" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  IMPORTANT:" -ForegroundColor Yellow
Write-Host "1. Make sure Local Backend is running: python local_stillme_backend.py" -ForegroundColor White
Write-Host "2. Set GATEWAY_SECRET in both .env files" -ForegroundColor White
Write-Host "3. Press Ctrl+C to stop tunnel" -ForegroundColor White
Write-Host ""

# Start tunnel
try {
    Write-Host "🌐 Starting tunnel..." -ForegroundColor Green
    Invoke-Expression $tunnelCmd
} catch {
    Write-Host "❌ Tunnel failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🛑 Tunnel stopped." -ForegroundColor Yellow
