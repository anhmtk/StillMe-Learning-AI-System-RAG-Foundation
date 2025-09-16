# 🚀 VPS DEPLOYMENT PLAN - StillMe Gateway API (Simplified)

## 📋 **TỔNG QUAN**

**Ngày tạo**: 13/09/2025  
**Mục tiêu**: Deploy Gateway API lên VPS cho 1 user, đảm bảo kết nối ổn định  
**Thời gian thực hiện**: 2-3 ngày  
**Ưu tiên**: SIMPLE & COST-EFFECTIVE  

## 🎯 **CHIẾN LƯỢC DEPLOYMENT (RÚT GỌN)**

### **PHASE 1: LOCAL PREPARATION (1 ngày)**
- ✅ Fix AI Server import issues
- ✅ Test Gateway + AI Server locally
- ✅ Prepare Docker containers
- ✅ Create deployment scripts

### **PHASE 2: VPS SETUP (1 ngày)**
- 🔧 Setup VPS infrastructure (2 vCPU, 2GB RAM)
- 🔧 Install Docker & Docker Compose
- 🔧 Setup Nginx reverse proxy
- 🔧 Configure SSL certificates với Let's Encrypt
- 🔧 Setup domain & DNS

### **PHASE 3: DEPLOYMENT & MONITORING (1 ngày)**
- 🚀 Deploy Gateway API + AI Server
- 🚀 Test connectivity
- 📧 Setup basic email alerts
- 🔍 Simple health monitoring

## 🛠️ **VPS INFRASTRUCTURE REQUIREMENTS (SIMPLIFIED)**

### **VPS Specs (1 User):**
- **CPU**: 2 vCPU
- **RAM**: 2GB (có thể nâng lên 4GB nếu cần monitoring)
- **Storage**: 30GB SSD
- **Bandwidth**: 1TB/month
- **OS**: Ubuntu 22.04 LTS
- **Cost**: ~$5-10/month

### **Lý do cấu hình này:**
- ✅ **Đủ cho 1 user**: Gateway + AI Server không cần tài nguyên cao
- ✅ **Tiết kiệm chi phí**: Chỉ $5-10/tháng thay vì $20-50/tháng
- ✅ **Dễ vận hành**: Không cần quản lý phức tạp
- ✅ **Ổn định**: Đủ tài nguyên cho hoạt động bình thường

## 🐳 **DOCKER CONTAINERS**

### **1. Gateway Container**
```dockerfile
# Dockerfile.gateway
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY simple_gateway.py .
COPY config/ ./config/

EXPOSE 8000
CMD ["python", "simple_gateway.py"]
```

### **2. AI Server Container**
```dockerfile
# Dockerfile.ai-server
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY stable_ai_server.py .
COPY stillme_core/ ./stillme_core/
COPY config/ ./config/

EXPOSE 1216
CMD ["python", "stable_ai_server.py"]
```

### **3. Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    ports:
      - "8000:8000"
    environment:
      - STILLME_CORE_URL=http://ai-server:1216
    depends_on:
      - ai-server
    restart: unless-stopped

  ai-server:
    build:
      context: .
      dockerfile: Dockerfile.ai-server
    ports:
      - "1216:1216"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - gateway
    restart: unless-stopped
```

## 🔧 **NGINX CONFIGURATION**

### **nginx.conf**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream gateway {
        server gateway:8000;
    }

    upstream ai-server {
        server ai-server:1216;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ai/ {
            proxy_pass http://ai-server/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 📧 **SIMPLE NOTIFICATION SYSTEM**

### **Email Notifications Only (SMTP)**
```python
# simple_notification.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class SimpleEmailNotification:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.to_email = os.getenv('ALERT_EMAIL')

    def send_alert(self, subject, message):
        if not all([self.username, self.password, self.to_email]):
            print("⚠️ Email notification not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = self.to_email
            msg['Subject'] = f"[StillMe Alert] {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email alert sent: {subject}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

# Global instance
email_notifier = SimpleEmailNotification()
```

### **Health Check Script**
```bash
#!/bin/bash
# health_check.sh

GATEWAY_URL="https://your-domain.com/health"
AI_SERVER_URL="https://your-domain.com/ai/health"
ALERT_EMAIL="your-email@gmail.com"

# Check Gateway
if ! curl -f -s $GATEWAY_URL > /dev/null; then
    echo "Gateway is down!" | mail -s "StillMe Gateway Down" $ALERT_EMAIL
fi

# Check AI Server
if ! curl -f -s $AI_SERVER_URL > /dev/null; then
    echo "AI Server is down!" | mail -s "StillMe AI Server Down" $ALERT_EMAIL
fi
```

### **Cron Job Setup**
```bash
# Add to crontab: crontab -e
# Check every 5 minutes
*/5 * * * * /path/to/health_check.sh
```

## 🚀 **DEPLOYMENT SCRIPTS**

### **deploy.sh**
```bash
#!/bin/bash

# VPS Deployment Script
echo "🚀 Starting StillMe Gateway Deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y

# Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y

# Clone repository
git clone https://github.com/your-repo/stillme-ai.git
cd stillme-ai

# Build and start containers
docker-compose up -d --build

# Setup SSL certificate
sudo certbot --nginx -d your-domain.com

echo "✅ Deployment completed!"
```

## 📊 **SIMPLE MONITORING**

### **Health Check Endpoints**
- `GET /health` - Basic health check
- `GET /metrics` - Simple system metrics
- `GET /status` - Service status

### **Simple Monitoring**
- ✅ **Docker logs**: `docker-compose logs -f`
- ✅ **Health checks**: Cron job every 5 minutes
- ✅ **Email alerts**: Khi service down
- ✅ **Basic metrics**: CPU, RAM, disk usage
- ❌ **No complex dashboard**: Bỏ Grafana/Prometheus
- ❌ **No real-time monitoring**: Chỉ cần biết khi có vấn đề

## 🔒 **SECURITY CONSIDERATIONS**

### **1. Firewall Configuration**
```bash
# UFW Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### **2. SSL/TLS Configuration**
- Let's Encrypt certificates
- HSTS headers
- SSL/TLS 1.3
- Perfect Forward Secrecy

### **3. API Security**
- Rate limiting
- CORS configuration
- Input validation
- Authentication tokens

## 📈 **EXPECTED RESULTS (SIMPLIFIED)**

### **Before VPS Deployment:**
- ❌ Local-only access
- ❌ No 24/7 availability
- ❌ No SSL/HTTPS
- ❌ No monitoring
- ❌ No notifications

### **After VPS Deployment:**
- ✅ **Global access**: Desktop/Mobile app kết nối từ mọi nơi
- ✅ **24/7 availability**: Gateway luôn online
- ✅ **SSL/HTTPS security**: Kết nối bảo mật
- ✅ **Simple monitoring**: Health checks + email alerts
- ✅ **Cost-effective**: Chỉ $5-10/tháng
- ✅ **Easy maintenance**: Không cần quản lý phức tạp
- ✅ **Stable connection**: Kết nối ổn định cho 1 user

## 🎯 **NEXT STEPS (SIMPLIFIED)**

1. **Choose VPS Provider** (DigitalOcean $5/month, Vultr $6/month, Linode $5/month)
2. **Setup VPS** with Ubuntu 22.04 (2 vCPU, 2GB RAM, 30GB SSD)
3. **Deploy Gateway API** using Docker
4. **Setup domain & SSL** với Let's Encrypt
5. **Setup email notifications** với SMTP
6. **Test end-to-end connectivity**
7. **Setup cron health checks**

---

**Status**: 📋 PLANNING  
**Priority**: 🚨 SIMPLE & COST-EFFECTIVE  
**Estimated Effort**: 2-3 ngày  
**Cost**: $5-10/tháng  
**Expected ROI**: 300%+ improvement in reliability với chi phí thấp
