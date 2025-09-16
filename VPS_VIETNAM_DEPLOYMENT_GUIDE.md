# 🇻🇳 VPS VIỆT NAM DEPLOYMENT GUIDE

## 🎯 **THÔNG TIN VPS CẦN THIẾT**

### **Từ email VPS:**
- **IP Address**: XXX.XXX.XXX.XXX
- **Username**: root (hoặc admin)
- **Password**: (từ email)
- **SSH Port**: 22 (thường)
- **OS**: Ubuntu 22.04 LTS (thường)

## 🚀 **BƯỚC 1: KẾT NỐI VPS**

### **Windows PowerShell:**
```powershell
# Kết nối SSH
ssh root@YOUR_VPS_IP

# Hoặc nếu username khác
ssh admin@YOUR_VPS_IP
```

### **Hoặc dùng PuTTY:**
1. **Download PuTTY**: [putty.org](https://putty.org)
2. **Host Name**: YOUR_VPS_IP
3. **Port**: 22
4. **Connection Type**: SSH
5. **Click "Open"**

## 📁 **BƯỚC 2: UPLOAD FILES LÊN VPS**

### **Cách 1: SCP (PowerShell)**
```powershell
# Tạo thư mục trên VPS
ssh root@YOUR_VPS_IP "mkdir -p /opt/stillme"

# Upload deployment package
scp -r deployment_package/* root@YOUR_VPS_IP:/opt/stillme/
```

### **Cách 2: WinSCP (GUI)**
1. **Download WinSCP**: [winscp.net](https://winscp.net)
2. **Host**: YOUR_VPS_IP
3. **Username**: root
4. **Password**: (từ email)
5. **Upload** toàn bộ thư mục `deployment_package` lên `/opt/stillme`

## 🌐 **BƯỚC 3: SETUP DOMAIN**

### **Option A: No-IP (Miễn phí)**
1. **Truy cập**: [noip.com](https://noip.com)
2. **Sign up** miễn phí
3. **Tạo hostname**: `stillme-gateway.ddns.net`
4. **Confirm email** (cần confirm mỗi 30 ngày)

### **Option B: FreeDNS.afraid.org**
1. **Truy cập**: [freedns.afraid.org](https://freedns.afraid.org)
2. **Sign up** miễn phí
3. **Tạo subdomain**: `stillme-gateway.afraid.org`

### **Option C: Sử dụng IP trực tiếp**
- **Gateway**: `http://YOUR_VPS_IP:8000`
- **HTTPS**: Cần SSL certificate

## 📧 **BƯỚC 4: SETUP EMAIL NOTIFICATIONS**

### **Gmail Settings:**
1. **Truy cập**: [myaccount.google.com/security](https://myaccount.google.com/security)
2. **Enable 2-Factor Authentication**
3. **App Passwords** → **Generate new password**
4. **Chọn "Mail"** và **"Other"**
5. **Nhập tên**: "StillMe VPS"
6. **Copy password** (16 ký tự)

### **Environment Variables:**
```bash
# Trên VPS, set các biến môi trường:
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-16-char-app-password"
export ALERT_EMAIL="your-email@gmail.com"
```

## 🚀 **BƯỚC 5: DEPLOY STILLME**

### **SSH vào VPS:**
```bash
ssh root@YOUR_VPS_IP
```

### **Chạy deployment script:**
```bash
cd /opt/stillme
chmod +x deploy_vietnam_vps.sh

# Deploy với domain
./deploy_vietnam_vps.sh your-domain.com your-email@gmail.com

# Hoặc deploy với IP trực tiếp
./deploy_vietnam_vps.sh YOUR_VPS_IP your-email@gmail.com
```

### **Hoặc deploy manual:**
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
sudo apt install -y docker.io docker-compose

# 3. Install Nginx
sudo apt install -y nginx

# 4. Build and run containers
docker-compose up -d

# 5. Setup SSL (nếu có domain)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🧪 **BƯỚC 6: TEST DEPLOYMENT**

### **Test Gateway:**
```bash
# Health check
curl http://YOUR_VPS_IP:8000/health

# Version check
curl http://YOUR_VPS_IP:8000/version

# Send message
curl -X POST http://YOUR_VPS_IP:8000/send-message \
  -H "Content-Type: application/json" \
  -d '{"message":"xin chào stillme","language":"vi"}'
```

### **Test HTTPS (nếu có domain):**
```bash
# Health check
curl https://your-domain.com/health

# Version check
curl https://your-domain.com/version
```

## 📱 **BƯỚC 7: CONFIGURE DESKTOP/MOBILE APP**

### **Update Gateway URL:**
- **Old**: `http://192.168.1.8:8000`
- **New**: `http://YOUR_VPS_IP:8000` hoặc `https://your-domain.com`

### **Test kết nối:**
1. **Desktop App**: Update config file
2. **Mobile App**: Update API endpoint
3. **Test chat**: Gửi tin nhắn thử

## 🔧 **TROUBLESHOOTING**

### **Docker không chạy:**
```bash
# Check Docker status
sudo systemctl status docker

# Start Docker
sudo systemctl start docker

# Check containers
docker ps -a
```

### **Nginx không chạy:**
```bash
# Check Nginx status
sudo systemctl status nginx

# Start Nginx
sudo systemctl start nginx

# Check config
sudo nginx -t
```

### **SSL không hoạt động:**
```bash
# Check SSL certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

## 📋 **CHECKLIST DEPLOYMENT**

- [ ] **VPS connection** - SSH thành công
- [ ] **Files uploaded** - deployment_package trên VPS
- [ ] **Domain setup** - No-IP hoặc FreeDNS
- [ ] **Email configured** - Gmail App Password
- [ ] **Docker installed** - docker-compose chạy
- [ ] **Nginx configured** - reverse proxy hoạt động
- [ ] **SSL certificate** - HTTPS hoạt động
- [ ] **Gateway test** - API endpoints trả lời
- [ ] **Desktop/Mobile** - App kết nối được
- [ ] **Email notifications** - Alert hoạt động

## 🎉 **KẾT QUẢ MONG ĐỢI**

**Sau khi deploy thành công:**
- ✅ **StillMe Gateway** chạy trên VPS Việt Nam
- ✅ **HTTPS/SSL** tự động (nếu có domain)
- ✅ **Email notifications** hoạt động
- ✅ **Desktop/Mobile app** kết nối được từ mọi nơi
- ✅ **Health monitoring** tự động
- ✅ **Uptime cao** - VPS Việt Nam ổn định

## 📞 **SUPPORT**

**Nếu gặp vấn đề:**
1. **Check logs**: `docker logs stillme-gateway`
2. **Check status**: `docker ps -a`
3. **Check network**: `netstat -tlnp`
4. **Contact support**: VPS provider hoặc StillMe team
