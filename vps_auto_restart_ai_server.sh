#!/bin/bash
# StillMe AI Server Auto-Restart Script
# Tự động restart AI Server khi gặp lỗi

set -e

# Configuration
VPS_IP="160.191.89.99"
VPS_USER="root"
VPS_PASSWORD="StillMe@2025!"
AI_SERVER_PORT="1216"
GATEWAY_PORT="21568"
LOG_FILE="/var/log/stillme_restart.log"
MAX_RETRIES=3
RETRY_DELAY=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    log "Checking $service_name on port $port..."
    
    # Use sshpass for password authentication
    if sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl is-active --quiet $service_name"; then
        return 0
    else
        return 1
    fi
}

# Test port connectivity
test_port() {
    local port=$1
    local service_name=$2
    
    log "Testing connectivity to $service_name on port $port..."
    
    if timeout 10 bash -c "</dev/tcp/$VPS_IP/$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Restart AI Server
restart_ai_server() {
    log "Restarting StillMe AI Server..."
    
    # Stop the service
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl stop stillme-ai-server" || true
    
    # Wait a moment
    sleep 5
    
    # Start the service
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl start stillme-ai-server"
    
    # Wait for service to start
    sleep 10
    
    # Check if it's running
    if check_service "stillme-ai-server" "$AI_SERVER_PORT"; then
        success "AI Server restarted successfully"
        return 0
    else
        error "Failed to restart AI Server"
        return 1
    fi
}

# Restart Gateway
restart_gateway() {
    log "Restarting StillMe Gateway..."
    
    # Stop the service
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl stop stillme-gateway" || true
    
    # Wait a moment
    sleep 5
    
    # Start the service
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl start stillme-gateway"
    
    # Wait for service to start
    sleep 10
    
    # Check if it's running
    if check_service "stillme-gateway" "$GATEWAY_PORT"; then
        success "Gateway restarted successfully"
        return 0
    else
        error "Failed to restart Gateway"
        return 1
    fi
}

# Get service status
get_service_status() {
    local service_name=$1
    
    log "Getting status for $service_name..."
    
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl status $service_name --no-pager -l" | tee -a "$LOG_FILE"
}

# Main monitoring function
monitor_services() {
    log "Starting StillMe services monitoring..."
    
    local ai_server_failed=false
    local gateway_failed=false
    local retry_count=0
    
    while true; do
        log "=== Monitoring cycle $(date) ==="
        
        # Check AI Server
        if ! test_port "$AI_SERVER_PORT" "AI Server"; then
            warning "AI Server is not responding on port $AI_SERVER_PORT"
            ai_server_failed=true
        else
            success "AI Server is responding on port $AI_SERVER_PORT"
            ai_server_failed=false
        fi
        
        # Check Gateway
        if ! test_port "$GATEWAY_PORT" "Gateway"; then
            warning "Gateway is not responding on port $GATEWAY_PORT"
            gateway_failed=true
        else
            success "Gateway is responding on port $GATEWAY_PORT"
            gateway_failed=false
        fi
        
        # Restart failed services
        if [ "$ai_server_failed" = true ]; then
            if restart_ai_server; then
                retry_count=0
            else
                retry_count=$((retry_count + 1))
                if [ $retry_count -ge $MAX_RETRIES ]; then
                    error "AI Server failed to restart after $MAX_RETRIES attempts"
                    get_service_status "stillme-ai-server"
                    retry_count=0
                fi
            fi
        fi
        
        if [ "$gateway_failed" = true ]; then
            if restart_gateway; then
                retry_count=0
            else
                retry_count=$((retry_count + 1))
                if [ $retry_count -ge $MAX_RETRIES ]; then
                    error "Gateway failed to restart after $MAX_RETRIES attempts"
                    get_service_status "stillme-gateway"
                    retry_count=0
                fi
            fi
        fi
        
        # Wait before next check
        log "Waiting $RETRY_DELAY seconds before next check..."
        sleep $RETRY_DELAY
    done
}

# One-time restart function
one_time_restart() {
    log "Performing one-time restart of StillMe services..."
    
    # Check current status
    log "Current service status:"
    get_service_status "stillme-ai-server"
    get_service_status "stillme-gateway"
    
    # Restart AI Server
    if ! test_port "$AI_SERVER_PORT" "AI Server"; then
        log "AI Server is down, restarting..."
        restart_ai_server
    else
        log "AI Server is running, no restart needed"
    fi
    
    # Restart Gateway
    if ! test_port "$GATEWAY_PORT" "Gateway"; then
        log "Gateway is down, restarting..."
        restart_gateway
    else
        log "Gateway is running, no restart needed"
    fi
    
    # Final status check
    log "Final service status:"
    get_service_status "stillme-ai-server"
    get_service_status "stillme-gateway"
    
    success "One-time restart completed"
}

# Test connectivity function
test_connectivity() {
    log "Testing StillMe services connectivity..."
    
    # Test AI Server
    if test_port "$AI_SERVER_PORT" "AI Server"; then
        success "AI Server is accessible on port $AI_SERVER_PORT"
    else
        error "AI Server is NOT accessible on port $AI_SERVER_PORT"
    fi
    
    # Test Gateway
    if test_port "$GATEWAY_PORT" "Gateway"; then
        success "Gateway is accessible on port $GATEWAY_PORT"
    else
        error "Gateway is NOT accessible on port $GATEWAY_PORT"
    fi
    
    # Test chat endpoint
    log "Testing chat endpoint..."
    local response=$(curl -s -w "%{http_code}" -o /dev/null "http://$VPS_IP:$GATEWAY_PORT/health" || echo "000")
    if [ "$response" = "200" ]; then
        success "Chat endpoint is responding (HTTP $response)"
    else
        error "Chat endpoint is NOT responding (HTTP $response)"
    fi
}

# Main script logic
main() {
    log "StillMe Auto-Restart Script started"
    log "VPS: $VPS_IP"
    log "AI Server Port: $AI_SERVER_PORT"
    log "Gateway Port: $GATEWAY_PORT"
    
    case "${1:-monitor}" in
        "monitor")
            monitor_services
            ;;
        "restart")
            one_time_restart
            ;;
        "test")
            test_connectivity
            ;;
        "status")
            get_service_status "stillme-ai-server"
            get_service_status "stillme-gateway"
            ;;
        *)
            echo "Usage: $0 {monitor|restart|test|status}"
            echo "  monitor  - Continuous monitoring and auto-restart (default)"
            echo "  restart  - One-time restart of all services"
            echo "  test     - Test connectivity to all services"
            echo "  status   - Show current service status"
            exit 1
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    if ! command -v sshpass &> /dev/null; then
        error "sshpass is not installed. Please install it first:"
        echo "  Ubuntu/Debian: sudo apt-get install sshpass"
        echo "  CentOS/RHEL: sudo yum install sshpass"
        echo "  macOS: brew install sshpass"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        error "curl is not installed. Please install it first."
        exit 1
    fi
}

# Run main function
check_dependencies
main "$@"
