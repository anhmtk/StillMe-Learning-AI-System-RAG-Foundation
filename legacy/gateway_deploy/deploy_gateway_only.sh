#!/bin/bash

# StillMe Gateway Only Deploy Script
# IP: 160.191.89.99
# Purpose: Test connection between Desktop/Mobile apps and StillMe

set -e

VPS_IP="160.191.89.99"
PROJECT_DIR="/opt/stillme-gateway"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

log_info "Starting StillMe Gateway Only Deploy for IP: $VPS_IP"
log_info "Purpose: Test Desktop/Mobile app connection"

# 1. Update System
log_info "Updating system packages..."
apt update && apt upgrade -y || log_error "Failed to update system"

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."
    apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    usermod -aG docker $USER
    log_info "Docker installed successfully"
else
    log_info "Docker is already installed"
fi

# 3. Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_info "Installing Docker Compose..."
    apt install -y docker-compose
else
    log_info "Docker Compose is already installed"
fi

# 4. Install Nginx
if ! command -v nginx &> /dev/null; then
    log_info "Installing Nginx..."
    apt install -y nginx
    ufw allow 'Nginx Full'
    systemctl enable nginx
    systemctl start nginx
else
    log_info "Nginx is already installed"
fi

# 5. Configure Firewall
log_info "Configuring UFW firewall..."
ufw allow OpenSSH
ufw allow 8000
ufw allow 80
ufw allow 443
ufw --force enable
ufw status verbose

# 6. Create project directory
log_info "Setting up project directory..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 7. Build and Run Gateway Only
log_info "Building and running Gateway only..."
docker-compose -f docker-compose.gateway.yml build --no-cache || log_error "Docker Compose build failed"
docker-compose -f docker-compose.gateway.yml up -d || log_error "Docker Compose up failed"

# 8. Wait for services to start
log_info "Waiting for Gateway to start..."
sleep 30

# 9. Health Check
log_info "Performing health checks..."
if curl -f http://localhost:8000/health; then
    log_info "✅ Gateway health check passed"
else
    log_warn "⚠️  Gateway health check failed"
fi

# 10. Show status
log_info "Deployment completed! Checking status..."
docker ps -a
echo ""
log_info "🎉 StillMe Gateway deployed successfully!"
log_info "Gateway URL: http://$VPS_IP:8000"
log_info "Health Check: http://$VPS_IP:8000/health"
echo ""
log_info "📱 For Desktop/Mobile apps, use:"
log_info "Gateway Endpoint: http://$VPS_IP:8000"
log_info "Test connection: curl http://$VPS_IP:8000/health"
echo ""
log_info "⚠️  Note: AI Server is running on your local machine (port 1216)"
log_info "Gateway will forward requests to: http://160.191.89.99:1216"
