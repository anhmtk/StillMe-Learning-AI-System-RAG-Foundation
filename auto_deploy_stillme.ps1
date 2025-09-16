#!/usr/bin/env pwsh
# StillMe Auto Deploy Script for VPS
# Author: StillMe AI
# Date: 2025-09-15
# Version: 1.0.0

# Configuration
$VPS_IP = "160.191.89.99"
$VPS_USER = "root"
$EMAIL = "anhnguyen.nk86@gmail.com"
$DOMAIN = "160.191.89.99"  # Using IP as domain for now
$PROJECT_DIR = "/opt/stillme"

Write-Host "🚀 StillMe Auto Deploy Script" -ForegroundColor Green
Write-Host "VPS IP: $VPS_IP" -ForegroundColor Yellow
Write-Host "Email: $EMAIL" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Green

# Step 1: Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Cyan
if (Test-Path "deployment_package") {
    Remove-Item "deployment_package" -Recurse -Force
}
New-Item -ItemType Directory -Path "deployment_package" | Out-Null

# Copy essential files
$files_to_copy = @(
    "docker-compose.yml",
    "Dockerfile.gateway", 
    "Dockerfile.ai-server",
    "nginx.conf",
    "stable_ai_server.py",
    "requirements.txt",
    "health_check.simple.sh"
)

foreach ($file in $files_to_copy) {
    if (Test-Path $file) {
        Copy-Item $file "deployment_package/"
        Write-Host "✅ Copied $file" -ForegroundColor Green
    } else {
        Write-Host "⚠️  File not found: $file" -ForegroundColor Yellow
    }
}

# Copy directories
$dirs_to_copy = @(
    "stillme_core",
    "config", 
    "logs",
    "data"
)

foreach ($dir in $dirs_to_copy) {
    if (Test-Path $dir) {
        Copy-Item $dir "deployment_package/" -Recurse
        Write-Host "✅ Copied directory $dir" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Directory not found: $dir" -ForegroundColor Yellow
    }
}

# Step 2: Create VPS deployment script
Write-Host "📝 Creating VPS deployment script..." -ForegroundColor Cyan
$vps_script = @"
#!/bin/bash

# StillMe VPS Auto Deploy Script
# Generated automatically for IP: $VPS_IP

set -e

# Configuration
VPS_IP="$VPS_IP"
EMAIL="$EMAIL"
DOMAIN="$DOMAIN"
PROJECT_DIR="$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "\${GREEN}[INFO]\${NC} \$1"; }
log_warn() { echo -e "\${YELLOW}[WARN]\${NC} \$1"; }
log_error() { echo -e "\${RED}[ERROR]\${NC} \$1"; exit 1; }

log_info "Starting StillMe Auto Deploy for IP: \$VPS_IP"

# 1. Update System
log_info "Updating system packages..."
apt update && apt upgrade -y || log_error "Failed to update system"

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."
    apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    usermod -aG docker \$USER
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
ufw allow 1216
ufw allow 80
ufw allow 443
ufw --force enable
ufw status verbose

# 6. Create project directory
log_info "Setting up project directory..."
mkdir -p \$PROJECT_DIR
cd \$PROJECT_DIR

# 7. Build and Run Docker Containers
log_info "Building and running Docker containers..."
docker-compose build --no-cache || log_error "Docker Compose build failed"
docker-compose up -d || log_error "Docker Compose up failed"

# 8. Wait for services to start
log_info "Waiting for services to start..."
sleep 30

# 9. Health Check
log_info "Performing health checks..."
if curl -f http://localhost:8000/health; then
    log_info "✅ Gateway health check passed"
else
    log_warn "⚠️  Gateway health check failed"
fi

if curl -f http://localhost:1216/health; then
    log_info "✅ AI Server health check passed"
else
    log_warn "⚠️  AI Server health check failed"
fi

# 10. Show status
log_info "Deployment completed! Checking status..."
docker ps -a
echo ""
log_info "🎉 StillMe Gateway deployed successfully!"
log_info "Gateway URL: http://\$VPS_IP:8000"
log_info "AI Server URL: http://\$VPS_IP:1216"
log_info "Health Check: http://\$VPS_IP:8000/health"
echo ""
log_info "You can now test the deployment with:"
log_info "curl http://\$VPS_IP:8000/health"
log_info "curl http://\$VPS_IP:1216/health"
"@

$vps_script | Out-File -FilePath "deployment_package/deploy_vps.sh" -Encoding UTF8
Write-Host "✅ Created VPS deployment script" -ForegroundColor Green

# Step 3: Create upload script
Write-Host "📤 Creating upload script..." -ForegroundColor Cyan
$upload_script = @"
# Upload StillMe to VPS
Write-Host "Uploading files to VPS..." -ForegroundColor Cyan

# Create directory on VPS
ssh $VPS_USER@$VPS_IP "mkdir -p $PROJECT_DIR"

# Upload all files
scp -r deployment_package/* ${VPS_USER}@${VPS_IP}:${PROJECT_DIR}/

Write-Host "✅ Files uploaded successfully!" -ForegroundColor Green
Write-Host "Now running deployment on VPS..." -ForegroundColor Yellow

# Run deployment script on VPS
ssh $VPS_USER@$VPS_IP "cd $PROJECT_DIR && chmod +x deploy_vps.sh && ./deploy_vps.sh"

Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host "Gateway: http://$VPS_IP:8000" -ForegroundColor Cyan
Write-Host "AI Server: http://$VPS_IP:1216" -ForegroundColor Cyan
"@

$upload_script | Out-File -FilePath "upload_and_deploy.ps1" -Encoding UTF8
Write-Host "✅ Created upload script" -ForegroundColor Green

# Step 4: Create test script
Write-Host "🧪 Creating test script..." -ForegroundColor Cyan
$test_script = @"
# Test StillMe Deployment
Write-Host "Testing StillMe deployment..." -ForegroundColor Cyan

# Test Gateway
Write-Host "Testing Gateway..." -ForegroundColor Yellow
try {
    `$response = Invoke-WebRequest -Uri "http://$VPS_IP:8000/health" -UseBasicParsing
    Write-Host "✅ Gateway Health: `$(`$response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: `$(`$response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Gateway test failed: `$_" -ForegroundColor Red
}

# Test AI Server
Write-Host "Testing AI Server..." -ForegroundColor Yellow
try {
    `$response = Invoke-WebRequest -Uri "http://$VPS_IP:1216/health" -UseBasicParsing
    Write-Host "✅ AI Server Health: `$(`$response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: `$(`$response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "❌ AI Server test failed: `$_" -ForegroundColor Red
}

# Test send message
Write-Host "Testing send message..." -ForegroundColor Yellow
try {
    `$body = @{
        message = "xin chào stillme"
        language = "vi"
    } | ConvertTo-Json
    
    `$response = Invoke-WebRequest -Uri "http://$VPS_IP:8000/send-message" -Method POST -Body `$body -ContentType "application/json" -UseBasicParsing
    Write-Host "✅ Send Message: `$(`$response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: `$(`$response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Send message test failed: `$_" -ForegroundColor Red
}

Write-Host "🎉 Testing completed!" -ForegroundColor Green
"@

$test_script | Out-File -FilePath "test_deployment.ps1" -Encoding UTF8
Write-Host "✅ Created test script" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Auto Deploy Script Created Successfully!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\upload_and_deploy.ps1" -ForegroundColor Cyan
Write-Host "2. Wait for deployment to complete" -ForegroundColor Cyan
Write-Host "3. Run: .\test_deployment.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your StillMe will be available at:" -ForegroundColor Yellow
Write-Host "Gateway: http://$VPS_IP:8000" -ForegroundColor Cyan
Write-Host "AI Server: http://$VPS_IP:1216" -ForegroundColor Cyan
Write-Host ""
