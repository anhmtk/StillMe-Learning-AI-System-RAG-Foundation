#!/bin/bash

# StillMe Rollback Script
# Implements blue-green deployment rollback strategy

set -e

# Configuration
CURRENT_TAG=""
PREVIOUS_TAG=""
NAMESPACE="stillme"
SERVICE_NAME="stillme-prod"
HEALTH_CHECK_URL="http://localhost:8080/healthz"
READINESS_CHECK_URL="http://localhost:8080/readyz"
ROLLBACK_TIMEOUT=300  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
StillMe Rollback Script

Usage: $0 [OPTIONS]

OPTIONS:
    -t, --tag TAG           Previous tag to rollback to
    -n, --namespace NS      Kubernetes namespace (default: stillme)
    -s, --service NAME      Service name (default: stillme-prod)
    -u, --url URL           Health check URL (default: http://localhost:8080/healthz)
    -h, --help              Show this help message

EXAMPLES:
    $0 --tag v1.2.3
    $0 -t v1.2.3 -n production
    $0 -t v1.2.3 -s stillme-api

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            PREVIOUS_TAG="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -u|--url)
            HEALTH_CHECK_URL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$PREVIOUS_TAG" ]; then
    log_error "Previous tag is required. Use -t or --tag option."
    show_help
    exit 1
fi

# Get current tag
get_current_tag() {
    log_info "Getting current deployment tag..."
    
    # Try to get current tag from Docker
    if command -v docker &> /dev/null; then
        CURRENT_TAG=$(docker ps --filter "name=$SERVICE_NAME" --format "table {{.Image}}" | tail -n +2 | cut -d: -f2)
        if [ -z "$CURRENT_TAG" ]; then
            CURRENT_TAG="latest"
        fi
    else
        CURRENT_TAG="latest"
    fi
    
    log_info "Current tag: $CURRENT_TAG"
}

# Health check function
check_health() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    log_info "Checking health at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "Health check passed (attempt $attempt/$max_attempts)"
            return 0
        else
            log_warning "Health check failed (attempt $attempt/$max_attempts)"
            sleep 10
            attempt=$((attempt + 1))
        fi
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback function
rollback_deployment() {
    log_info "Starting rollback from $CURRENT_TAG to $PREVIOUS_TAG..."
    
    # Step 1: Pull previous image
    log_info "Pulling previous image: stillme:$PREVIOUS_TAG"
    if command -v docker &> /dev/null; then
        docker pull "stillme:$PREVIOUS_TAG" || {
            log_error "Failed to pull image stillme:$PREVIOUS_TAG"
            return 1
        }
    fi
    
    # Step 2: Update docker-compose or Kubernetes deployment
    log_info "Updating deployment configuration..."
    
    # For Docker Compose
    if [ -f "docker-compose.prod.yml" ]; then
        log_info "Updating docker-compose.prod.yml..."
        sed -i.bak "s|image: stillme:.*|image: stillme:$PREVIOUS_TAG|g" docker-compose.prod.yml
        
        # Restart services
        log_info "Restarting services with docker-compose..."
        docker-compose -f docker-compose.prod.yml up -d --force-recreate
    fi
    
    # For Kubernetes (if kubectl is available)
    if command -v kubectl &> /dev/null; then
        log_info "Updating Kubernetes deployment..."
        kubectl set image deployment/$SERVICE_NAME stillme=stillme:$PREVIOUS_TAG -n $NAMESPACE
        
        # Wait for rollout
        log_info "Waiting for rollout to complete..."
        kubectl rollout status deployment/$SERVICE_NAME -n $NAMESPACE --timeout=$ROLLBACK_TIMEOUT
    fi
    
    log_success "Deployment updated to $PREVIOUS_TAG"
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."
    
    # Wait for service to be ready
    sleep 30
    
    # Check health endpoints
    if ! check_health "$HEALTH_CHECK_URL"; then
        log_error "Health check failed after rollback"
        return 1
    fi
    
    if ! check_health "$READINESS_CHECK_URL"; then
        log_error "Readiness check failed after rollback"
        return 1
    fi
    
    # Verify tag
    if command -v docker &> /dev/null; then
        NEW_TAG=$(docker ps --filter "name=$SERVICE_NAME" --format "table {{.Image}}" | tail -n +2 | cut -d: -f2)
        if [ "$NEW_TAG" = "$PREVIOUS_TAG" ]; then
            log_success "Rollback verification successful - running $PREVIOUS_TAG"
        else
            log_warning "Tag verification failed - expected $PREVIOUS_TAG, got $NEW_TAG"
        fi
    fi
    
    log_success "Rollback verification completed"
}

# Main rollback process
main() {
    log_info "Starting StillMe rollback process..."
    log_info "Rolling back from $CURRENT_TAG to $PREVIOUS_TAG"
    
    # Get current tag
    get_current_tag
    
    # Confirm rollback
    log_warning "This will rollback the deployment from $CURRENT_TAG to $PREVIOUS_TAG"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
    
    # Perform rollback
    if rollback_deployment; then
        log_success "Rollback deployment completed"
    else
        log_error "Rollback deployment failed"
        exit 1
    fi
    
    # Verify rollback
    if verify_rollback; then
        log_success "Rollback verification completed"
    else
        log_error "Rollback verification failed"
        exit 1
    fi
    
    log_success "Rollback process completed successfully!"
    log_info "Service is now running version $PREVIOUS_TAG"
    
    # Generate rollback report
    cat > "artifacts/rollback_report_$(date +%Y%m%d_%H%M%S).md" << EOF
# Rollback Report

**Date:** $(date)
**From:** $CURRENT_TAG
**To:** $PREVIOUS_TAG
**Service:** $SERVICE_NAME
**Namespace:** $NAMESPACE

## Rollback Summary

- ✅ Previous image pulled successfully
- ✅ Deployment configuration updated
- ✅ Services restarted
- ✅ Health checks passed
- ✅ Readiness checks passed
- ✅ Tag verification completed

## Health Check Results

- **Health Endpoint:** $HEALTH_CHECK_URL - ✅ PASSED
- **Readiness Endpoint:** $READINESS_CHECK_URL - ✅ PASSED

## Next Steps

1. Monitor the service for any issues
2. Investigate the cause of the original deployment failure
3. Update deployment procedures if necessary
4. Document lessons learned

EOF
    
    log_info "Rollback report generated: artifacts/rollback_report_$(date +%Y%m%d_%H%M%S).md"
}

# Run main function
main "$@"
