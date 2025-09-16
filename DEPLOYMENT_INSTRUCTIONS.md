# 🚀 STILLME VPS DEPLOYMENT INSTRUCTIONS

## 📋 **THÔNG TIN VPS**
- **IP**: 160.191.89.99
- **Username**: root
- **Password**: StillMe@2025!
- **OS**: Ubuntu 22.04 LTS (thường)

## 🔧 **BƯỚC 1: SSH VÀO VPS**

### **Cách 1: PowerShell**
```powershell
ssh root@160.191.89.99
# Nhập password: StillMe@2025!
```

### **Cách 2: PuTTY**
1. **Host**: 160.191.89.99
2. **Port**: 22
3. **Username**: root
4. **Password**: StillMe@2025!

## 📁 **BƯỚC 2: UPLOAD FILES**

### **Cách 1: SCP (PowerShell)**
```powershell
# Tạo thư mục trên VPS
ssh root@160.191.89.99 "mkdir -p /opt/stillme"

# Upload toàn bộ deployment_package
scp -r deployment_package/* root@160.191.89.99:/opt/stillme/
```

### **Cách 2: WinSCP (GUI)**
1. **Host**: 160.191.89.99
2. **Username**: root
3. **Password**: StillMe@2025!
4. **Upload** toàn bộ thư mục `deployment_package` lên `/opt/stillme`

## 🚀 **BƯỚC 3: DEPLOY TRÊN VPS**

### **SSH vào VPS và chạy:**
```bash
# 1. Vào thư mục deployment
cd /opt/stillme

# 2. Cấp quyền thực thi
chmod +x deploy_vietnam_vps.sh
chmod +x health_check_desktop_sms.sh

# 3. Deploy với IP trực tiếp (không cần domain)
./deploy_vietnam_vps.sh 160.191.89.99 your-email@gmail.com

# Hoặc deploy với domain (nếu có)
./deploy_vietnam_vps.sh your-domain.com your-email@gmail.com
```

## 🧪 **BƯỚC 4: TEST DEPLOYMENT**

### **Test Gateway:**
```bash
# Health check
curl http://160.191.89.99:8000/health

# Version check
curl http://160.191.89.99:8000/version

# Send message
curl -X POST http://160.191.89.99:8000/send-message \
  -H "Content-Type: application/json" \
  -d '{"message":"xin chào stillme","language":"vi"}'
```

### **Test từ máy local:**
```powershell
# Health check
Invoke-WebRequest -Uri "http://160.191.89.99:8000/health" -Method GET

# Version check
Invoke-WebRequest -Uri "http://160.191.89.99:8000/version" -Method GET

# Send message
$body = @{message="xin chào stillme"; language="vi"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://160.191.89.99:8000/send-message" -Method POST -Body $body -ContentType "application/json"
```

## 📱 **BƯỚC 5: CONFIGURE NOTIFICATIONS**

### **Set environment variables:**
```bash
# SMS notifications
export ALERT_PHONE="+84901234567"  # Thay bằng số của bạn

# Optional: Telegram Bot
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Optional: Discord Webhook
export DISCORD_WEBHOOK_URL="your_webhook_url"
```

### **Test notifications:**
```bash
# Test SMS
python3 sms_notification.py

# Test Desktop notifications
python3 desktop_notification.py

# Test Health Check
./health_check_desktop_sms.sh
```

## 🔧 **BƯỚC 6: SETUP CRON JOB**

### **Tự động health check mỗi 5 phút:**
```bash
# Thêm cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/stillme/health_check_desktop_sms.sh") | crontab -

# Kiểm tra cron job
crontab -l
```

## 📊 **BƯỚC 7: MONITORING**

### **Check Docker containers:**
```bash
docker ps -a
docker logs stillme-gateway
docker logs stillme-ai-server
```

### **Check Nginx:**
```bash
sudo systemctl status nginx
sudo nginx -t
```

### **Check system resources:**
```bash
top
df -h
free -h
```

## 🎯 **KẾT QUẢ MONG ĐỢI**

**Sau khi deploy thành công:**
- ✅ **StillMe Gateway**: http://160.191.89.99:8000
- ✅ **Health Check**: http://160.191.89.99:8000/health
- ✅ **Version API**: http://160.191.89.99:8000/version
- ✅ **Send Message**: http://160.191.89.99:8000/send-message
- ✅ **Docker containers** chạy ổn định
- ✅ **Nginx** reverse proxy hoạt động
- ✅ **Health monitoring** tự động
- ✅ **SMS notifications** hoạt động

## 🚨 **TROUBLESHOOTING**

### **Docker không chạy:**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### **Nginx không chạy:**
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo nginx -t
```

### **Port bị block:**
```bash
sudo ufw allow 8000
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status
```

### **Check logs:**
```bash
# Docker logs
docker logs stillme-gateway
docker logs stillme-ai-server

# System logs
sudo journalctl -u docker
sudo journalctl -u nginx
```

## 📞 **SUPPORT**

**Nếu gặp vấn đề:**
1. **Check logs** trước
2. **Restart services** nếu cần
3. **Contact VPS provider** nếu cần
4. **StillMe team** sẵn sàng hỗ trợ

## 🎉 **CHÚC MỪNG!**

**StillMe đã được deploy thành công lên VPS Việt Nam!**
**Bây giờ bạn có thể:**
- **Kết nối Desktop/Mobile app** đến VPS
- **Nhận thông báo** qua SMS/Telegram/Discord
- **Monitor hệ thống** tự động
- **Sử dụng StillMe** từ mọi nơi!
