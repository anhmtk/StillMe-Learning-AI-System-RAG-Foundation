#!/bin/bash

# 🚀 StillMe Gateway VPS Deployment Script (Simplified)
# For 1 user, cost-effective setup

set -e

echo "🚀 Starting StillMe Gateway VPS Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${1:-"your-domain.com"}
EMAIL=${2:-"your-email@gmail.com"}

echo -e "${YELLOW}Domain: $DOMAIN${NC}"
echo -e "${YELLOW}Email: $EMAIL${NC}"

# Update system
echo -e "${GREEN}📦 Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo -e "${GREEN}📦 Installing essential packages...${NC}"
sudo apt install -y curl wget git unzip software-properties-common

# Install Docker
echo -e "${GREEN}🐳 Installing Docker...${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
echo -e "${GREEN}🐳 Installing Docker Compose...${NC}"
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
echo -e "${GREEN}🌐 Installing Nginx...${NC}"
sudo apt install -y nginx

# Install Certbot for SSL
echo -e "${GREEN}🔒 Installing Certbot for SSL...${NC}"
sudo apt install -y certbot python3-certbot-nginx

# Setup firewall
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# Create project directory
echo -e "${GREEN}📁 Creating project directory...${NC}"
sudo mkdir -p /opt/stillme
sudo chown $USER:$USER /opt/stillme
cd /opt/stillme

# Clone repository (replace with your repo)
echo -e "${GREEN}📥 Cloning repository...${NC}"
# git clone https://github.com/your-repo/stillme-ai.git .
# For now, we'll create the necessary files

# Create Dockerfiles
echo -e "${GREEN}🐳 Creating Dockerfiles...${NC}"

# Gateway Dockerfile
cat > Dockerfile.gateway << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY simple_gateway.py .
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "simple_gateway.py"]
EOF

# AI Server Dockerfile
cat > Dockerfile.ai-server << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY stable_ai_server.py .
COPY stillme_core/ ./stillme_core/
COPY config/ ./config/

# Create logs and data directories
RUN mkdir -p logs data

# Expose port
EXPOSE 1216

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:1216/health || exit 1

# Run the application
CMD ["python", "stable_ai_server.py"]
EOF

# Create docker-compose.yml
echo -e "${GREEN}🐳 Creating docker-compose.yml...${NC}"
cat > docker-compose.yml << EOF
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:1216/health"]
      interval: 30s
      timeout: 10s
      retries: 3

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
EOF

# Create nginx.conf
echo -e "${GREEN}🌐 Creating nginx.conf...${NC}"
cat > nginx.conf << EOF
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

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }

    # HTTPS Server
    server {
        listen 443 ssl;
        server_name $DOMAIN;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Gateway Routes
        location / {
            proxy_pass http://gateway;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # AI Server Routes
        location /ai/ {
            proxy_pass http://ai-server/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Health Check
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Create SSL directory
mkdir -p ssl

# Create health check script
echo -e "${GREEN}🔍 Creating health check script...${NC}"
cat > health_check.sh << EOF
#!/bin/bash

GATEWAY_URL="https://$DOMAIN/health"
AI_SERVER_URL="https://$DOMAIN/ai/health"
ALERT_EMAIL="$EMAIL"

# Check Gateway
if ! curl -f -s \$GATEWAY_URL > /dev/null; then
    echo "Gateway is down at \$(date)" | mail -s "StillMe Gateway Down" \$ALERT_EMAIL
fi

# Check AI Server
if ! curl -f -s \$AI_SERVER_URL > /dev/null; then
    echo "AI Server is down at \$(date)" | mail -s "StillMe AI Server Down" \$ALERT_EMAIL
fi
EOF

chmod +x health_check.sh

# Install mailutils for email alerts
echo -e "${GREEN}📧 Installing mailutils...${NC}"
sudo apt install -y mailutils

# Setup cron job for health checks
echo -e "${GREEN}⏰ Setting up cron job...${NC}"
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/stillme/health_check.sh") | crontab -

# Build and start containers
echo -e "${GREEN}🐳 Building and starting containers...${NC}"
docker-compose up -d --build

# Wait for services to start
echo -e "${GREEN}⏳ Waiting for services to start...${NC}"
sleep 30

# Setup SSL certificate
echo -e "${GREEN}🔒 Setting up SSL certificate...${NC}"
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL

# Restart nginx with SSL
echo -e "${GREEN}🔄 Restarting nginx with SSL...${NC}"
docker-compose restart nginx

# Test deployment
echo -e "${GREEN}🧪 Testing deployment...${NC}"
sleep 10

if curl -f -s https://$DOMAIN/health > /dev/null; then
    echo -e "${GREEN}✅ Gateway is healthy!${NC}"
else
    echo -e "${RED}❌ Gateway health check failed${NC}"
fi

if curl -f -s https://$DOMAIN/ai/health > /dev/null; then
    echo -e "${GREEN}✅ AI Server is healthy!${NC}"
else
    echo -e "${RED}❌ AI Server health check failed${NC}"
fi

echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo -e "${YELLOW}📱 Your StillMe Gateway is now available at: https://$DOMAIN${NC}"
echo -e "${YELLOW}🔍 Health check: https://$DOMAIN/health${NC}"
echo -e "${YELLOW}🤖 AI Server: https://$DOMAIN/ai/health${NC}"
echo -e "${YELLOW}📧 Email alerts configured for: $EMAIL${NC}"
echo -e "${YELLOW}⏰ Health checks every 5 minutes${NC}"

echo -e "${GREEN}📋 Next steps:${NC}"
echo -e "${YELLOW}1. Update your Desktop/Mobile app to use: https://$DOMAIN${NC}"
echo -e "${YELLOW}2. Test the connection from your apps${NC}"
echo -e "${YELLOW}3. Monitor logs with: docker-compose logs -f${NC}"
echo -e "${YELLOW}4. Check health status: ./health_check.sh${NC}"
