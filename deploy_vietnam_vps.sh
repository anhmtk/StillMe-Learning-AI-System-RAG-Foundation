#!/bin/bash

# StillMe VPS Vietnam Deployment Script
# Author: StillMe AI
# Date: 2025-09-13
# Version: 1.0.0

# --- Configuration ---
DOMAIN=$1
EMAIL=$2
PROJECT_DIR="/opt/stillme"
NGINX_CONF_PATH="$PROJECT_DIR/nginx.conf"
DOCKER_COMPOSE_PATH="$PROJECT_DIR/docker-compose.yml"
HEALTH_CHECK_SCRIPT_PATH="$PROJECT_DIR/health_check.simple.sh"
CRON_JOB="*/5 * * * * $HEALTH_CHECK_SCRIPT_PATH"

# --- Colors ---
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Functions ---
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check for required arguments
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    log_error "Usage: $0 <your-domain.com> <your-email@example.com>"
fi

log_info "Starting StillMe VPS Vietnam Deployment for domain: $DOMAIN"

# 1. Update System
log_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y || log_error "Failed to update system."

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common || log_error "Failed to install prerequisites."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg || log_error "Failed to add Docker GPG key."
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null || log_error "Failed to add Docker repository."
    sudo apt update || log_error "Failed to update apt after adding Docker repo."
    sudo apt install -y docker-ce docker-ce-cli containerd.io || log_error "Failed to install Docker."
    sudo usermod -aG docker $USER || log_error "Failed to add user to docker group."
    log_info "Docker installed. Please log out and log back in for docker group changes to take effect, or run 'newgrp docker'."
else
    log_info "Docker is already installed."
fi

# 3. Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_info "Installing Docker Compose..."
    sudo apt install -y docker-compose || log_error "Failed to install Docker Compose."
else
    log_info "Docker Compose is already installed."
fi

# 4. Install Nginx
if ! command -v nginx &> /dev/null; then
    log_info "Installing Nginx..."
    sudo apt install -y nginx || log_error "Failed to install Nginx."
    sudo ufw allow 'Nginx Full' || log_error "Failed to allow Nginx through UFW."
    sudo systemctl enable nginx || log_error "Failed to enable Nginx."
    sudo systemctl start nginx || log_error "Failed to start Nginx."
else
    log_info "Nginx is already installed."
fi

# 5. Configure Firewall (UFW)
log_info "Configuring UFW firewall..."
sudo ufw allow OpenSSH || log_error "Failed to allow OpenSSH."
sudo ufw enable || log_error "Failed to enable UFW."
sudo ufw status verbose

# 6. Prepare Nginx configuration
log_info "Preparing Nginx configuration..."
# Replace placeholder domain in nginx.conf
sed -i "s/your-domain.com/$DOMAIN/g" "$NGINX_CONF_PATH" || log_error "Failed to update Nginx config with domain."
sudo cp "$NGINX_CONF_PATH" /etc/nginx/sites-available/stillme || log_error "Failed to copy Nginx config."
sudo ln -sf /etc/nginx/sites-available/stillme /etc/nginx/sites-enabled/ || log_error "Failed to symlink Nginx config."
sudo rm -f /etc/nginx/sites-enabled/default # Remove default Nginx config
sudo nginx -t && sudo systemctl reload nginx || log_error "Nginx config test failed or reload failed."

# 7. Setup Certbot for SSL
log_info "Setting up Certbot for SSL..."
sudo apt install -y certbot python3-certbot-nginx || log_error "Failed to install Certbot."

# Stop Nginx temporarily for Certbot to bind to port 80
sudo systemctl stop nginx

# Request SSL certificate
sudo certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect || log_error "Failed to obtain SSL certificate."

# Start Nginx again
sudo systemctl start nginx

# 8. Build and Run Docker Containers
log_info "Building and running Docker containers..."
docker-compose -f "$DOCKER_COMPOSE_PATH" build || log_error "Docker Compose build failed."
docker-compose -f "$DOCKER_COMPOSE_PATH" up -d || log_error "Docker Compose up failed."

# 9. Setup Health Check Cron Job
log_info "Setting up health check cron job..."
# Make health check script executable
chmod +x "$HEALTH_CHECK_SCRIPT_PATH" || log_error "Failed to make health check script executable."
# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - || log_error "Failed to add cron job."
log_info "Cron job added: $CRON_JOB"

log_info "✅ Deployment completed! Access your StillMe Gateway at https://$DOMAIN"
log_info "You can check Gateway health at https://$DOMAIN/health"
log_info "You can check AI Server health at https://$DOMAIN/ai/health"
log_info "Remember to configure environment variables for email notifications in your docker-compose.yml or .env file."
