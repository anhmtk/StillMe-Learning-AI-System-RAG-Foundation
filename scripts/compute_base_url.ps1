#!/usr/bin/env pwsh
# Compute Base URL - Windows PowerShell
# Trả về BASE_URL cho StillMe server

# Đọc port từ .env nếu có, hoặc detect từ server logs
$PORT = "8000"
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "SERVER_PORT=(\d+)") {
        $PORT = $matches[1]
    }
}

# Nếu server đang chạy, detect port thực tế
if (Test-Path "logs\server_error.log") {
    $detectedPort = & "$PSScriptRoot\detect_server_port.ps1"
    if ($detectedPort -and $detectedPort -ne "8000") {
        $PORT = $detectedPort
    }
}

# Lấy Tailscale IP
$TAILSCALE_IP = & "$PSScriptRoot\get_tailscale_ip.ps1"

if ($TAILSCALE_IP -and $TAILSCALE_IP -ne "") {
    $BASE_URL = "http://$TAILSCALE_IP`:$PORT"
} else {
    # Fallback: lấy LAN IP
    try {
        $lanIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
            $_.IPAddress -notlike "127.*" -and 
            $_.IPAddress -notlike "169.254.*" -and
            $_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual"
        } | Select-Object -First 1).IPAddress
        
        if ($lanIP) {
            $BASE_URL = "http://$lanIP`:$PORT"
        } else {
            # Fallback cuối cùng
            $BASE_URL = "http://localhost:$PORT"
        }
    } catch {
        $BASE_URL = "http://localhost:$PORT"
    }
}

Write-Output $BASE_URL

# Ghi vào config file
$configDir = "config"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}
$BASE_URL | Out-File -FilePath "$configDir\runtime_base_url.txt" -Encoding UTF8 -NoNewline
