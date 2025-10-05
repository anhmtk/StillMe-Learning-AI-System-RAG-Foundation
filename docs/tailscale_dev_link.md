# 🌐 Tailscale Dev Link - Hướng Dẫn Kết Nối

## 📋 Tổng Quan

Hướng dẫn thiết lập kết nối ổn định giữa Desktop App / Android App với StillMe server chạy trên máy local thông qua Tailscale.

## 🔧 Cài Đặt Tailscale

### Windows
1. Tải Tailscale từ: https://tailscale.com/download/windows
2. Cài đặt và đăng nhập tài khoản
3. Kiểm tra: `tailscale status`

### Linux/macOS
```bash
# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh

# macOS
brew install tailscale
```

## 🚀 Cách Sử Dụng

### 1. Lấy Tailscale IP
```bash
# Windows PowerShell
tailscale ip -4

# Linux/macOS
tailscale ip -4
```

### 2. Chạy Dev Tasks

#### Windows PowerShell
```powershell
# Compute BASE_URL
scripts\compute_base_url.ps1

# Khởi động server
scripts\start_server.ps1

# Chờ server sẵn sàng
scripts\wait_ready.ps1

# Smoke test
scripts\smoke_test.ps1

# Dừng server
scripts\stop_server.ps1
```

#### Linux/macOS
```bash
# Compute BASE_URL
bash scripts/compute_base_url.sh

# Khởi động server
bash scripts/start_server.sh

# Chờ server sẵn sàng
bash scripts/wait_ready.sh

# Smoke test
bash scripts/smoke_test.sh

# Dừng server
bash scripts/stop_server.sh
```

### 3. VSCode Tasks
- `Ctrl+Shift+P` → "Tasks: Run Task"
- Chọn: `dev:baseurl`, `dev:server`, `dev:wait`, `dev:smoke`, `dev:stop`
- Hoặc chạy toàn bộ: `dev:full-pipeline`

## 📱 Cấu Hình Client

### Desktop App
1. Đọc `config/runtime_base_url.txt`
2. Hoặc sử dụng biến môi trường `SERVER_BASE_URL`
3. Thêm mục "Settings → Server URL" để override

### Android App (Debug/Dev Build)
1. Sử dụng `SERVER_BASE_URL` trong BuildConfig
2. Đọc `runtime_base_url.txt` nếu có cơ chế sync
3. Mặc định sử dụng Tailscale/LAN URL

#### Network Security Config
```xml
<!-- android/app/src/debug/AndroidManifest.xml -->
<application
    android:usesCleartextTraffic="true"
    android:networkSecurityConfig="@xml/network_security_config">
```

```xml
<!-- android/app/src/main/res/xml/network_security_config.xml -->
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">100.64.0.0</domain> <!-- Tailscale -->
        <domain includeSubdomains="true">192.168.0.0</domain> <!-- LAN -->
        <domain includeSubdomains="true">10.0.0.0</domain>    <!-- LAN -->
    </domain-config>
</network-security-config>
```

## 🔍 Health Check Endpoints

- `GET /livez` - Process is alive
- `GET /readyz` - Server is ready to accept requests
- `GET /version` - Version information
- `GET /health` - Detailed health check

## 🛠️ Troubleshooting

### App Không Kết Nối?
1. **Kiểm tra server logs:**
   ```bash
   # Windows
   Get-Content logs\server.log -Tail 20
   
   # Linux/macOS
   tail -20 logs/server.log
   ```

2. **Kiểm tra Tailscale status:**
   ```bash
   tailscale status
   ```

3. **Kiểm tra firewall:**
   - Windows: Mở port 8000 cho Private network
   - Linux: `sudo ufw allow 8000`

4. **Kiểm tra BASE_URL:**
   ```bash
   # Windows
   Get-Content config\runtime_base_url.txt
   
   # Linux/macOS
   cat config/runtime_base_url.txt
   ```

### Tailscale Chưa Đăng Nhập?
1. Chạy: `tailscale up`
2. Mở browser và đăng nhập
3. Hoặc fallback sang LAN IP (tự động)

### Server Không Khởi Động?
1. Kiểm tra port 8000 có bị chiếm không:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/macOS
   lsof -i :8000
   ```

2. Dừng process cũ:
   ```bash
   # Windows
   scripts\stop_server.ps1
   
   # Linux/macOS
   bash scripts/stop_server.sh
   ```

## 📊 Smoke Test

Chạy smoke test để kiểm tra toàn bộ pipeline:

```bash
# Windows
scripts\smoke_test.ps1

# Linux/macOS
bash scripts/smoke_test.sh
```

Kết quả được lưu trong `reports/tailscale_smoke.txt`

## 🔒 Bảo Mật

- **Dev Only**: CORS được bật cho Tailscale/LAN IP
- **Production**: Không sử dụng cấu hình này
- **Firewall**: Chỉ mở port 8000 cho Private network
- **Logs**: Không lộ bí mật nội bộ

## 📝 Logs

- **Server logs**: `logs/server.log`
- **Smoke test**: `reports/tailscale_smoke.txt`
- **PID file**: `logs/server.pid`

## 🎯 Best Practices

1. **Luôn chạy server detached** - không treo terminal
2. **Sử dụng health check** trước khi test
3. **Kiểm tra logs** khi có lỗi
4. **Fallback LAN IP** nếu Tailscale không có
5. **Timeout 5-10s** cho client requests
6. **Retry backoff** (0.5→1→2s) cho client

## 🚨 Lưu Ý Quan Trọng

- **Không sử dụng localhost** cho thiết bị thật
- **Emulator cũng dùng Tailscale IP**, không phải 10.0.2.2
- **Server chạy detached** - không block terminal
- **Dev-only changes** - không ảnh hưởng production
