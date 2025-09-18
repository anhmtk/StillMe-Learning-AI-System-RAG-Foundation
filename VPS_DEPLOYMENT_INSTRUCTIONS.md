# 🚀 StillMe VPS Deployment Instructions

## 📋 Tổng quan
Deploy StillMe AI system lên VPS đã được bảo mật (160.191.89.99)

## ✅ Đã hoàn thành
- ✅ **Security Hardening** - VPS đã được bảo mật hoàn toàn
- ✅ **Deployment Package** - Đã tạo sẵn trong `deployment_package/`
- ✅ **Firewall** - Ports 22, 21568, 1216 đã được mở

## 🚀 BƯỚC 1: COPY DEPLOYMENT PACKAGE LÊN VPS

### Sử dụng PowerShell External:
```powershell
# Mở PowerShell external (Win + R → powershell)
cd D:\stillme_ai

# Copy deployment package lên VPS
scp -r deployment_package root@160.191.89.99:/tmp/
```

**Nhập password:** `StillMe@2025!` khi được hỏi

## 🔧 BƯỚC 2: SSH VÀO VPS VÀ DEPLOY

### SSH vào VPS:
```bash
ssh root@160.191.89.99
```

**Nhập password:** `StillMe@2025!` khi được hỏi

### Chạy deployment script:
```bash
cd /tmp/deployment_package
chmod +x deploy.sh
./deploy.sh
```

## ⏱️ Thời gian deployment: 5-10 phút

### Script sẽ tự động:
1. **Update system packages**
2. **Install Python và dependencies**
3. **Tạo stillme user**
4. **Copy application files**
5. **Setup virtual environment**
6. **Install Python packages**
7. **Tạo systemd services**
8. **Start StillMe services**

## 📊 BƯỚC 3: KIỂM TRA SERVICES

### Kiểm tra trạng thái services:
```bash
systemctl status stillme-gateway
systemctl status stillme-ai
```

### Xem logs real-time:
```bash
# Gateway logs
journalctl -u stillme-gateway -f

# AI Server logs  
journalctl -u stillme-ai -f
```

### Kiểm tra ports:
```bash
netstat -tlnp | grep -E "(21568|1216)"
```

## 🌐 BƯỚC 4: TEST CONNECTION

### Test Gateway:
```bash
curl http://localhost:21568/health
```

### Test AI Server:
```bash
curl http://localhost:1216/health
```

### Test từ external:
```bash
# Từ máy local
curl http://160.191.89.99:21568/health
curl http://160.191.89.99:1216/health
```

## 🎯 KẾT QUẢ MONG ĐỢI

### Services sẽ chạy trên:
- **Gateway:** `http://160.191.89.99:21568`
- **AI Server:** `http://160.191.89.99:1216`

### Desktop/Mobile apps có thể connect tới:
- **Gateway URL:** `http://160.191.89.99:21568`
- **AI Server URL:** `http://160.191.89.99:1216`

## 🔧 TROUBLESHOOTING

### Nếu services không start:
```bash
# Check logs
journalctl -u stillme-gateway --no-pager
journalctl -u stillme-ai --no-pager

# Restart services
systemctl restart stillme-gateway
systemctl restart stillme-ai
```

### Nếu ports không accessible:
```bash
# Check firewall
ufw status

# Check if services are listening
ss -tlnp | grep -E "(21568|1216)"
```

### Nếu có lỗi Python:
```bash
# Check virtual environment
cd /opt/stillme
source venv/bin/activate
python --version
pip list
```

## 📱 BƯỚC 5: UPDATE CLIENT APPS

### Desktop App:
- Update Gateway URL từ `localhost:21568` → `160.191.89.99:21568`

### Mobile App:
- Update Gateway URL trong config
- Build APK mới với VPS endpoints

## 🎉 HOÀN THÀNH

Sau khi deployment thành công:
1. ✅ **VPS được bảo mật** với multi-layer security
2. ✅ **StillMe services chạy** trên ports 21568 và 1216
3. ✅ **Desktop/Mobile apps** có thể connect từ xa
4. ✅ **Systemd services** tự động restart khi crash
5. ✅ **Logs được lưu** trong systemd journal

## 📞 SUPPORT

Nếu có vấn đề, check:
1. **Security logs:** `/var/log/stillme/`
2. **Service logs:** `journalctl -u stillme-*`
3. **Firewall:** `ufw status`
4. **Network:** `netstat -tlnp`
