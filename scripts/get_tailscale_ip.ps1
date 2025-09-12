#!/usr/bin/env pwsh
# Get Tailscale IP - Windows PowerShell
# Trả về IPv4 của Tailscale interface hoặc chuỗi rỗng

try {
    # Thử dùng tailscale CLI trước
    $tailscaleIP = & tailscale ip -4 2>$null
    if ($tailscaleIP -and $tailscaleIP -match '^\d+\.\d+\.\d+\.\d+$') {
        Write-Output $tailscaleIP
        exit 0
    }
} catch {
    # CLI không có sẵn, tiếp tục với method khác
}

try {
    # Dò Adapter Tailscale* qua Get-NetIPConfiguration
    $tailscaleAdapters = Get-NetIPConfiguration | Where-Object { $_.InterfaceAlias -like "*Tailscale*" }
    
    foreach ($adapter in $tailscaleAdapters) {
        $ipv4 = $adapter.IPv4Address.IPAddress
        if ($ipv4 -and $ipv4 -match '^\d+\.\d+\.\d+\.\d+$') {
            Write-Output $ipv4
            exit 0
        }
    }
} catch {
    # Không tìm thấy Tailscale adapter
}

# Không tìm thấy Tailscale IP
Write-Output ""
exit 0
