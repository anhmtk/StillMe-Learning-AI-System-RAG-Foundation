#!/bin/bash

# SEAL-GRADE SYSTEM TESTS - K6 Load Test Runner
# Script chạy kiểm thử tải K6 cho hệ thống SEAL-GRADE

set -e

# Configuration
BASE_URL=${BASE_URL:-"http://localhost:8000"}
TEST_DURATION=${TEST_DURATION:-"2m"}
VIRTUAL_USERS=${VIRTUAL_USERS:-100}
SOAK_DURATION=${SOAK_DURATION:-"4h"}
REPORTS_DIR="reports"
ARTIFACTS_DIR="artifacts"

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

# Check if K6 is installed
check_k6() {
    if ! command -v k6 &> /dev/null; then
        log_error "K6 is not installed. Please install K6 first."
        log_info "Installation instructions: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi
    
    log_success "K6 is installed: $(k6 version)"
}

# Check if target server is running
check_server() {
    log_info "Checking if target server is running at $BASE_URL..."
    
    if curl -s -f "$BASE_URL/health/ai" > /dev/null; then
        log_success "Server is running and healthy"
    else
        log_error "Server is not running or not healthy at $BASE_URL"
        log_info "Please start the server before running load tests"
        exit 1
    fi
}

# Create directories
setup_directories() {
    log_info "Setting up directories..."
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$ARTIFACTS_DIR"
    log_success "Directories created"
}

# Run load test
run_load_test() {
    log_info "Starting SEAL-GRADE Load Test..."
    log_info "Configuration:"
    log_info "  Base URL: $BASE_URL"
    log_info "  Duration: $TEST_DURATION"
    log_info "  Virtual Users: $VIRTUAL_USERS"
    
    k6 run \
        --env BASE_URL="$BASE_URL" \
        --env TEST_DURATION="$TEST_DURATION" \
        --env VIRTUAL_USERS="$VIRTUAL_USERS" \
        --out json="$REPORTS_DIR/load_test_results.json" \
        --out csv="$REPORTS_DIR/load_test_results.csv" \
        --summary-export="$REPORTS_DIR/load_test_summary.json" \
        load_test_seal_grade.js
    
    if [ $? -eq 0 ]; then
        log_success "Load test completed successfully"
    else
        log_error "Load test failed"
        exit 1
    fi
}

# Run soak test
run_soak_test() {
    log_info "Starting SEAL-GRADE Soak Test..."
    log_info "Configuration:"
    log_info "  Base URL: $BASE_URL"
    log_info "  Duration: $SOAK_DURATION"
    log_info "  Virtual Users: 50"
    
    k6 run \
        --env BASE_URL="$BASE_URL" \
        --env SOAK_DURATION="$SOAK_DURATION" \
        --env VIRTUAL_USERS="50" \
        --out json="$REPORTS_DIR/soak_test_results.json" \
        --out csv="$REPORTS_DIR/soak_test_results.csv" \
        --summary-export="$REPORTS_DIR/soak_test_summary.json" \
        soak_test_seal_grade.js
    
    if [ $? -eq 0 ]; then
        log_success "Soak test completed successfully"
    else
        log_error "Soak test failed"
        exit 1
    fi
}

# Generate HTML report
generate_html_report() {
    log_info "Generating HTML report..."
    
    # Create HTML report from JSON results
    cat > "$REPORTS_DIR/load_test_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>SEAL-GRADE Load Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .success { border-left-color: #28a745; }
        .warning { border-left-color: #ffc107; }
        .error { border-left-color: #dc3545; }
        .threshold { font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SEAL-GRADE Load Test Report</h1>
        <p>Generated on: $(date)</p>
        <p>Base URL: $BASE_URL</p>
        <p>Test Duration: $TEST_DURATION</p>
        <p>Virtual Users: $VIRTUAL_USERS</p>
    </div>
    
    <h2>Test Results</h2>
    <div id="results">
        <p>Loading test results...</p>
    </div>
    
    <script>
        // Load and display results
        fetch('load_test_summary.json')
            .then(response => response.json())
            .then(data => {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = generateResultsHTML(data);
            })
            .catch(error => {
                document.getElementById('results').innerHTML = 
                    '<p class="error">Error loading test results: ' + error.message + '</p>';
            });
        
        function generateResultsHTML(data) {
            let html = '<h3>Performance Metrics</h3>';
            
            // Add metrics display logic here
            html += '<div class="metric">';
            html += '<strong>Total Requests:</strong> ' + (data.metrics?.http_reqs?.values?.count || 'N/A');
            html += '</div>';
            
            html += '<div class="metric">';
            html += '<strong>Requests per Second:</strong> ' + (data.metrics?.http_reqs?.values?.rate || 'N/A');
            html += '</div>';
            
            html += '<div class="metric">';
            html += '<strong>Response Time (P95):</strong> ' + (data.metrics?.http_req_duration?.values?.['p(95)'] || 'N/A') + 'ms';
            html += '</div>';
            
            html += '<div class="metric">';
            html += '<strong>Error Rate:</strong> ' + ((data.metrics?.http_req_failed?.values?.rate || 0) * 100).toFixed(2) + '%';
            html += '</div>';
            
            html += '<h3>Thresholds</h3>';
            if (data.thresholds) {
                for (const [threshold, result] of Object.entries(data.thresholds)) {
                    const className = result ? 'success' : 'error';
                    const status = result ? 'PASSED' : 'FAILED';
                    html += '<div class="metric ' + className + '">';
                    html += '<strong>' + threshold + ':</strong> <span class="' + (result ? 'passed' : 'failed') + '">' + status + '</span>';
                    html += '</div>';
                }
            }
            
            return html;
        }
    </script>
</body>
</html>
EOF
    
    log_success "HTML report generated: $REPORTS_DIR/load_test_report.html"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --load)
                RUN_LOAD_TEST=true
                shift
                ;;
            --soak)
                RUN_SOAK_TEST=true
                shift
                ;;
            --all)
                RUN_LOAD_TEST=true
                RUN_SOAK_TEST=true
                shift
                ;;
            --url)
                BASE_URL="$2"
                shift 2
                ;;
            --duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            --users)
                VIRTUAL_USERS="$2"
                shift 2
                ;;
            --soak-duration)
                SOAK_DURATION="$2"
                shift 2
                ;;
            --help)
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
}

# Show help
show_help() {
    cat << EOF
SEAL-GRADE Load Test Runner

Usage: $0 [OPTIONS]

Options:
    --load              Run load test only
    --soak              Run soak test only
    --all               Run both load and soak tests (default)
    --url URL           Base URL for testing (default: http://localhost:8000)
    --duration DURATION Load test duration (default: 2m)
    --users USERS       Number of virtual users (default: 100)
    --soak-duration DURATION Soak test duration (default: 4h)
    --help              Show this help message

Examples:
    $0 --load --users 200 --duration 5m
    $0 --soak --soak-duration 2h
    $0 --all --url http://staging.example.com

EOF
}

# Main function
main() {
    log_info "SEAL-GRADE Load Test Runner"
    log_info "=========================="
    
    # Parse arguments
    parse_arguments "$@"
    
    # Set default behavior
    if [ -z "$RUN_LOAD_TEST" ] && [ -z "$RUN_SOAK_TEST" ]; then
        RUN_LOAD_TEST=true
    fi
    
    # Check prerequisites
    check_k6
    check_server
    setup_directories
    
    # Run tests
    if [ "$RUN_LOAD_TEST" = true ]; then
        run_load_test
        generate_html_report
    fi
    
    if [ "$RUN_SOAK_TEST" = true ]; then
        run_soak_test
    fi
    
    log_success "All tests completed successfully!"
    log_info "Reports available in: $REPORTS_DIR/"
    log_info "Artifacts available in: $ARTIFACTS_DIR/"
}

# Run main function
main "$@"
