#!/bin/bash

# 🔍 SIMPLE HEALTH CHECK SCRIPT FOR STILLME VPS
# 🔍 SCRIPT KIỂM TRA SỨC KHỎE ĐƠN GIẢN CHO STILLME VPS

# Configuration
DOMAIN=${DOMAIN:-"your-domain.com"}
ALERT_EMAIL=${ALERT_EMAIL:-"your-email@gmail.com"}
LOG_FILE="/opt/stillme/health_check.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Send email alert function
send_email_alert() {
    local subject="$1"
    local message="$2"
    
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
        log "📧 Email alert sent: $subject"
    else
        log "⚠️ Mail command not available, cannot send email alert"
    fi
}

# Check service health
check_service() {
    local service_name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    log "🔍 Checking $service_name at $url"
    
    # Make HTTP request
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_status" ]; then
        log "✅ $service_name is healthy (HTTP $response)"
        return 0
    else
        log "❌ $service_name is unhealthy (HTTP $response)"
        send_email_alert "StillMe $service_name Down" "The $service_name service is currently down. HTTP Status: $response"
        return 1
    fi
}

# Check Docker containers
check_docker_containers() {
    log "🐳 Checking Docker containers..."
    
    # Check if docker-compose is running
    if ! docker-compose ps | grep -q "Up"; then
        log "❌ Docker containers are not running"
        send_email_alert "StillMe Docker Containers Down" "Docker containers are not running. Check the VPS immediately."
        return 1
    fi
    
    # Check individual containers
    containers=("gateway" "ai-server" "nginx")
    for container in "${containers[@]}"; do
        if ! docker-compose ps | grep -q "$container.*Up"; then
            log "❌ Container $container is not running"
            send_email_alert "StillMe Container $container Down" "The $container container is not running."
            return 1
        fi
    done
    
    log "✅ All Docker containers are running"
    return 0
}

# Check system resources
check_system_resources() {
    log "💻 Checking system resources..."
    
    # Check disk space
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log "⚠️ Disk usage is high: ${disk_usage}%"
        send_email_alert "StillMe VPS Disk Space Warning" "Disk usage is at ${disk_usage}%. Consider cleaning up."
    else
        log "✅ Disk usage is normal: ${disk_usage}%"
    fi
    
    # Check memory usage
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -gt 90 ]; then
        log "⚠️ Memory usage is high: ${memory_usage}%"
        send_email_alert "StillMe VPS Memory Warning" "Memory usage is at ${memory_usage}%. Consider restarting services."
    else
        log "✅ Memory usage is normal: ${memory_usage}%"
    fi
    
    # Check CPU load
    cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    if (( $(echo "$cpu_load > 2.0" | bc -l) )); then
        log "⚠️ CPU load is high: $cpu_load"
        send_email_alert "StillMe VPS CPU Load Warning" "CPU load is high: $cpu_load. Check for resource-intensive processes."
    else
        log "✅ CPU load is normal: $cpu_load"
    fi
}

# Main health check function
main() {
    log "🚀 Starting StillMe VPS health check..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        log "❌ docker-compose.yml not found. Please run this script from the StillMe project directory."
        exit 1
    fi
    
    # Check Docker containers first
    if ! check_docker_containers; then
        log "❌ Docker container check failed"
        exit 1
    fi
    
    # Check services
    services_healthy=true
    
    # Check Gateway
    if ! check_service "Gateway" "https://$DOMAIN/health"; then
        services_healthy=false
    fi
    
    # Check AI Server
    if ! check_service "AI Server" "https://$DOMAIN/ai/health"; then
        services_healthy=false
    fi
    
    # Check system resources
    check_system_resources
    
    # Summary
    if [ "$services_healthy" = true ]; then
        log "✅ All services are healthy"
        exit 0
    else
        log "❌ Some services are unhealthy"
        exit 1
    fi
}

# Run main function
main "$@"
