# 🧪 SEAL-GRADE TEST ENVIRONMENT MATRIX
# Ma trận môi trường kiểm thử SEAL-GRADE

## 📋 Overview

This document outlines the test environment matrix for SEAL-GRADE system tests, including hardware specifications, software requirements, and configuration details.

Tài liệu này phác thảo ma trận môi trường kiểm thử cho hệ thống kiểm thử SEAL-GRADE, bao gồm thông số kỹ thuật phần cứng, yêu cầu phần mềm và chi tiết cấu hình.

---

## 🖥️ Environment Matrix

### Primary Test Environment (Ubuntu 22.04)

| Component | Specification | Notes |
|-----------|---------------|-------|
| **OS** | Ubuntu 22.04 LTS | Primary test environment |
| **CPU** | 4 cores, 2.4GHz | Intel/AMD x64 |
| **RAM** | 8GB | Minimum for load testing |
| **Storage** | 100GB SSD | Fast I/O for test data |
| **Network** | 1Gbps | For load testing |
| **Python** | 3.11.x | Latest stable version |
| **Node.js** | 18.x LTS | For K6 load testing |
| **Workers** | 4 | Parallel test execution |

### Secondary Test Environment (Windows 11)

| Component | Specification | Notes |
|-----------|---------------|-------|
| **OS** | Windows 11 Pro | Secondary test environment |
| **CPU** | 4 cores, 2.4GHz | Intel/AMD x64 |
| **RAM** | 8GB | Minimum for load testing |
| **Storage** | 100GB SSD | Fast I/O for test data |
| **Network** | 1Gbps | For load testing |
| **Python** | 3.11.x | Latest stable version |
| **Node.js** | 18.x LTS | For K6 load testing |
| **Workers** | 2 | Limited parallel execution |

### Tertiary Test Environment (macOS 13)

| Component | Specification | Notes |
|-----------|---------------|-------|
| **OS** | macOS 13 Ventura | Tertiary test environment |
| **CPU** | 4 cores, 2.4GHz | Apple Silicon/Intel |
| **RAM** | 8GB | Minimum for load testing |
| **Storage** | 100GB SSD | Fast I/O for test data |
| **Network** | 1Gbps | For load testing |
| **Python** | 3.11.x | Latest stable version |
| **Node.js** | 18.x LTS | For K6 load testing |
| **Workers** | 4 | Parallel test execution |

---

## 🔧 Software Requirements

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **Python** | 3.11.x | Core runtime |
| **pip** | 23.x | Package manager |
| **pytest** | 7.x | Test framework |
| **pytest-cov** | 4.x | Coverage reporting |
| **pytest-html** | 3.x | HTML reports |
| **pytest-xdist** | 3.x | Parallel execution |
| **coverage** | 7.x | Coverage analysis |
| **bandit** | 1.x | Security scanning |
| **safety** | 2.x | Dependency scanning |
| **semgrep** | 1.x | Static analysis |

### Load Testing Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **Node.js** | 18.x LTS | K6 runtime |
| **k6** | 0.47.x | Load testing |
| **curl** | 7.x | HTTP testing |
| **jq** | 1.x | JSON processing |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **git** | 2.x | Version control |
| **docker** | 24.x | Containerization |
| **docker-compose** | 2.x | Multi-container |
| **make** | 4.x | Build automation |
| **bash** | 5.x | Scripting |

---

## ⚙️ Configuration Details

### Environment Variables

```bash
# Test Configuration
STILLME_TEST_MODE=true
STILLME_LOG_LEVEL=DEBUG
STILLME_DISABLE_TELEMETRY=true

# Performance Thresholds
STILLME_GATEWAY_P95_SLO=300
STILLME_GATEWAY_P95_THRESHOLD=500
STILLME_ERROR_RATE_THRESHOLD=0.01
STILLME_RECOVERY_TIME_THRESHOLD=5
STILLME_ETHICS_VIOLATION_THRESHOLD=0.001

# Coverage Requirements
STILLME_LINES_MINIMUM=90
STILLME_BRANCHES_MINIMUM=80
STILLME_MUTATION_MINIMUM=70

# Load Testing
STILLME_CONCURRENT_USERS=500
STILLME_REQUESTS_PER_HOUR=10000
STILLME_SOAK_DURATION_HOURS=2

# Security Testing
STILLME_INJECTION_TEST_CASES=50
STILLME_JAILBREAK_TEST_CASES=30
STILLME_PII_REDACTION_CASES=25

# Chaos Engineering
STILLME_NETWORK_DELAY_MS=1000
STILLME_NETWORK_DROP_PERCENT=10
STILLME_API_TIMEOUT_SECONDS=30

# Random Seed
STILLME_RANDOM_SEED=42
```

### Test Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| **test_defaults.yaml** | Default test configuration | `config/test_defaults.yaml` |
| **pytest.ini** | Pytest configuration | `pytest.ini` |
| **coverage.ini** | Coverage configuration | `coverage.ini` |
| **bandit.yaml** | Security scan configuration | `bandit.yaml` |
| **semgrep.yml** | Static analysis configuration | `semgrep.yml` |

---

## 🚀 Setup Instructions

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/stillme-ai.git
cd stillme-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. Test Data Setup

```bash
# Create test directories
mkdir -p reports artifacts logs

# Copy test datasets
cp datasets/*.json tests/fixtures/

# Set permissions (Linux/macOS)
chmod +x k6/run_load_tests.sh
chmod +x scripts/*.sh
```

### 3. Configuration Setup

```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env  # or your preferred editor

# Validate configuration
python scripts/validate_config.py
```

### 4. Service Setup

```bash
# Start required services
python stable_ai_server.py &
python api_server.py &

# Verify services
curl http://localhost:1216/health/ai
curl http://localhost:8000/health/ai
```

---

## 🧪 Test Execution

### Unit Tests

```bash
# Run all unit tests
pytest tests/test_unit_core_modules.py -v -m "unit"

# Run with coverage
pytest tests/test_unit_core_modules.py --cov=stillme_core --cov=modules --cov-report=html

# Run in parallel
pytest tests/test_unit_core_modules.py -n 4
```

### Integration Tests

```bash
# Run integration tests
pytest tests/test_integration_cross_module.py -v -m "integration"

# Run with HTML report
pytest tests/test_integration_cross_module.py --html=reports/integration_report.html
```

### Security Tests

```bash
# Run security tests
pytest tests/test_security_ethics.py -v -m "security or ethics"

# Run security scans
bandit -r stillme_core/ modules/
safety check
semgrep --config=auto stillme_core/ modules/
```

### Load Tests

```bash
# Run load tests
cd k6
./run_load_tests.sh --load --duration 2m --users 100

# Run soak tests
./run_load_tests.sh --soak --soak-duration 4h
```

---

## 📊 Performance Benchmarks

### Expected Performance Metrics

| Metric | Target | Ubuntu | Windows | macOS |
|--------|--------|--------|---------|-------|
| **Unit Test Execution** | <30s | 25s | 35s | 28s |
| **Integration Test Execution** | <60s | 45s | 65s | 50s |
| **Security Test Execution** | <45s | 40s | 55s | 42s |
| **Load Test Execution** | <5m | 4m | 6m | 4.5m |
| **Memory Usage** | <1GB | 800MB | 1.2GB | 900MB |
| **CPU Usage** | <80% | 70% | 85% | 75% |

### Load Test Scenarios

| Scenario | Duration | Users | Expected RPS | Expected P95 |
|----------|----------|-------|--------------|--------------|
| **Smoke Test** | 1m | 10 | 50 | <100ms |
| **Load Test** | 2m | 100 | 200 | <300ms |
| **Stress Test** | 5m | 500 | 500 | <500ms |
| **Soak Test** | 4h | 50 | 100 | <400ms |

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Test Failures
```bash
# Check test logs
tail -f logs/test.log

# Run specific test with verbose output
pytest tests/test_unit_core_modules.py::TestLayeredMemoryV1::test_memory_initialization -v -s

# Check test environment
python scripts/check_test_env.py
```

#### 2. Performance Issues
```bash
# Check system resources
htop  # Linux/macOS
taskmgr  # Windows

# Monitor test execution
pytest tests/ --durations=10

# Profile test execution
pytest tests/ --profile
```

#### 3. Load Test Issues
```bash
# Check K6 installation
k6 version

# Verify server connectivity
curl -f http://localhost:8000/health/ai

# Check load test configuration
cd k6
./run_load_tests.sh --help
```

#### 4. Security Scan Issues
```bash
# Check Bandit installation
bandit --version

# Run Bandit with verbose output
bandit -r stillme_core/ modules/ -v

# Check Safety installation
safety --version

# Run Safety with verbose output
safety check -v
```

---

## 📈 Monitoring and Reporting

### Test Metrics Collection

| Metric | Collection Method | Storage | Retention |
|--------|-------------------|---------|-----------|
| **Test Results** | pytest-html | reports/ | 30 days |
| **Coverage Data** | coverage.py | htmlcov/ | 30 days |
| **Performance Data** | K6 | k6/reports/ | 30 days |
| **Security Data** | Bandit/Safety | reports/ | 90 days |
| **Logs** | Python logging | logs/ | 7 days |

### Reporting Schedule

| Report Type | Frequency | Recipients | Format |
|-------------|-----------|------------|--------|
| **Unit Test Results** | Every commit | Developers | HTML/JSON |
| **Integration Test Results** | Every commit | Developers | HTML/JSON |
| **Security Scan Results** | Daily | Security Team | JSON/TXT |
| **Load Test Results** | Weekly | DevOps Team | JSON/HTML |
| **Coverage Reports** | Every commit | Developers | HTML |

---

## 🔧 Maintenance

### Daily Tasks
- [ ] Check test execution status
- [ ] Review test failures
- [ ] Update test data if needed
- [ ] Monitor system resources

### Weekly Tasks
- [ ] Run full test suite
- [ ] Update dependencies
- [ ] Review performance metrics
- [ ] Clean up old reports

### Monthly Tasks
- [ ] Update test environment
- [ ] Review and update test cases
- [ ] Performance optimization
- [ ] Security audit

---

## 📞 Support

### Contact Information
- **Test Team**: test-team@stillme.ai
- **DevOps Team**: devops@stillme.ai
- **Security Team**: security@stillme.ai

### Escalation Path
1. **Level 1**: Test Team
2. **Level 2**: DevOps Team
3. **Level 3**: Engineering Manager

### Documentation
- **Test Documentation**: `docs/`
- **API Documentation**: `docs/api/`
- **Troubleshooting Guide**: `docs/TROUBLESHOOTING.md`

---

**Document Created**: 2025-01-15  
**Document Version**: 1.0  
**Next Review**: 2025-02-15  
**Maintained By**: SEAL-GRADE Test Team
