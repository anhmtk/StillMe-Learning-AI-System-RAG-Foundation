# 🚀 StillMe Security Sandbox System - Phase 1

## 📋 Tổng Quan / Overview

Hệ thống Sandbox Security của StillMe cung cấp môi trường cô lập an toàn để thực hiện các bài test bảo mật mà không ảnh hưởng đến hệ thống production.

The StillMe Security Sandbox System provides a secure, isolated environment for conducting security tests without affecting the production system.

## 🏗️ Kiến Trúc / Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SANDBOX CONTROLLER                       │
├─────────────────────────────────────────────────────────────┤
│  • Docker Container Management                              │
│  • Resource Monitoring & Limits                            │
│  • Security Policy Enforcement                             │
│  • Network Isolation                                       │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    SANDBOX DEPLOYER                         │
├─────────────────────────────────────────────────────────────┤
│  • Automated Deployment                                     │
│  • Health Checks                                           │
│  • Application Code Deployment                             │
│  • Dependency Installation                                 │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY FRAMEWORK                       │
├─────────────────────────────────────────────────────────────┤
│  • Safe Attack Simulator                                   │
│  • Security Scanner                                        │
│  • Vulnerability Detection                                 │
│  • Risk Assessment                                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Cài Đặt / Installation

### 1. Yêu cầu hệ thống / System Requirements

- Docker Engine >= 20.10.0
- Python >= 3.9
- 4GB RAM (minimum)
- 10GB disk space

### 2. Cài đặt dependencies / Install Dependencies

```bash
# Install Python dependencies
pip install -r stillme_core/core/advanced_security/requirements_sandbox.txt

# Verify Docker installation
docker --version
docker-compose --version
```

### 3. Cấu hình / Configuration

Tạo file `.env` với các cấu hình sau:

```env
# Sandbox Configuration
SANDBOX_MAX_CONTAINERS=3
SANDBOX_MAX_MEMORY=512
SANDBOX_MAX_CPU=70
SANDBOX_TIMEOUT=900
SANDBOX_NETWORK_ISOLATION=true

# Security Configuration
SECURITY_METRICS_MAX_CPU=70
SECURITY_METRICS_MAX_MEMORY=512
SECURITY_METRICS_MAX_EXECUTION_TIME=900
SECURITY_METRICS_NETWORK_EGRESS_LIMIT=0
```

## 🚀 Sử Dụng / Usage

### 1. Khởi tạo Sandbox Controller

```python
import asyncio
from stillme_core.core.advanced_security.sandbox_controller import (
    SandboxController, 
    SandboxType
)

async def main():
    # Initialize sandbox controller
    controller = SandboxController()
    
    # Create security test sandbox
    sandbox = await controller.create_sandbox(
        name="security-test",
        sandbox_type=SandboxType.SECURITY_TEST,
        image="python:3.9-slim"
    )
    
    print(f"✅ Sandbox created: {sandbox.config.sandbox_id}")
    
    # Execute command in sandbox
    result = await controller.execute_in_sandbox(
        sandbox.config.sandbox_id,
        ["python", "-c", "print('Hello from sandbox!')"]
    )
    
    print(f"Command result: {result['stdout']}")
    
    # Clean up
    await controller.destroy_sandbox(sandbox.config.sandbox_id)

# Run the example
asyncio.run(main())
```

### 2. Sử dụng Sandbox Deployer

```python
import asyncio
from stillme_core.core.advanced_security.sandbox_deploy import SandboxDeployer

async def main():
    # Initialize deployer
    deployer = SandboxDeployer()
    
    # Deploy security sandbox
    success, sandbox_id, info = await deployer.deploy_security_sandbox(
        name="my-security-test",
        image="python:3.9-slim"
    )
    
    if success:
        print(f"✅ Deployment successful! Sandbox ID: {sandbox_id}")
        print(f"📊 Health status: {info['health_status']}")
    else:
        print(f"❌ Deployment failed: {info.get('error')}")
    
    # Clean up
    await deployer.cleanup_deployment(sandbox_id)

# Run the example
asyncio.run(main())
```

### 3. Chạy Security Tests

```python
import asyncio
from stillme_core.core.advanced_security.safe_attack_simulator import SafeAttackSimulator

async def main():
    # Initialize attack simulator
    simulator = SafeAttackSimulator()
    
    # Run SQL injection test
    result = simulator.run_simulation(
        scenario_id="OWASP_SQL_INJECTION",
        target_config={
            "host": "localhost",
            "use_test_data": True,
            "use_real_data": False
        }
    )
    
    print(f"✅ Simulation completed: {result.status}")
    print(f"🔍 Vulnerabilities found: {len(result.vulnerabilities_found)}")
    print(f"🛡️ Defenses triggered: {len(result.defenses_triggered)}")
    print(f"📊 Risk score: {result.risk_score}")

# Run the example
asyncio.run(main())
```

## 🧪 Testing

### 1. Chạy Unit Tests

```bash
# Run all tests
python -m pytest stillme_core/core/advanced_security/test_sandbox_system.py -v

# Run specific test class
python -m pytest stillme_core/core/advanced_security/test_sandbox_system.py::TestSandboxController -v

# Run with coverage
python -m pytest stillme_core/core/advanced_security/test_sandbox_system.py --cov=. --cov-report=html
```

### 2. Chạy Integration Tests

```bash
# Make sure Docker is running
docker --version

# Run integration tests
python -m pytest stillme_core/core/advanced_security/test_sandbox_system.py::TestIntegration -v
```

### 3. Chạy Performance Tests

```bash
# Run performance tests
python stillme_core/core/advanced_security/test_sandbox_system.py
```

## 📊 Monitoring & Logging

### 1. Sandbox Status Monitoring

```python
# Get sandbox status
status = controller.get_sandbox_status(sandbox_id)
print(f"Status: {status['status']}")
print(f"Resource usage: {status['resource_usage']}")
print(f"Security violations: {status['security_violations']}")
```

### 2. Deployment Reports

```python
# Get deployment report
report = deployer.get_deployment_report()
print(f"Total deployments: {report['total_deployments']}")
print(f"Successful: {report['successful_deployments']}")
print(f"Failed: {report['failed_deployments']}")
```

### 3. Security Reports

```python
# Get security report
security_report = simulator.get_safety_report()
print(f"Total simulations: {security_report['total_simulations']}")
print(f"Safety checks passed: {security_report['safety_checks_passed']}")
```

## 🔒 Security Features

### 1. Network Isolation
- Containers chạy với `network_mode: "none"`
- Không có internet access
- Chỉ internal networking được phép

### 2. Resource Limits
- CPU limit: 70% maximum
- Memory limit: 512MB maximum
- Execution timeout: 15 minutes
- Disk usage: 100MB maximum

### 3. Process Isolation
- Non-root user execution
- Dropped capabilities
- Security options enabled
- Read-only filesystem for system directories

### 4. Data Protection
- No real data access
- Automatic cleanup
- Encrypted temporary storage
- Audit logging

## 🚨 Troubleshooting

### 1. Docker Issues

```bash
# Check Docker status
docker info

# Restart Docker service
sudo systemctl restart docker

# Check container logs
docker logs <container_id>
```

### 2. Resource Issues

```bash
# Check system resources
htop
df -h
free -h

# Clean up Docker resources
docker system prune -a
```

### 3. Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart session
newgrp docker
```

## 📈 Performance Optimization

### 1. Container Optimization
- Sử dụng multi-stage builds
- Minimize image size
- Cache dependencies
- Use .dockerignore

### 2. Resource Optimization
- Monitor resource usage
- Adjust limits based on workload
- Use resource quotas
- Implement auto-scaling

### 3. Network Optimization
- Use internal networks
- Minimize network calls
- Cache results
- Batch operations

## 🔄 Next Steps (Phase 2)

1. **Red Team Module Enhancement**
   - AI-powered attack generation
   - Pattern-based vulnerability detection
   - Adaptive attack strategies

2. **Blue Team Module Development**
   - Anomaly detection
   - Automatic hardening
   - Defense verification

3. **Integration with Existing Modules**
   - Experience Memory integration
   - Decision Engine integration
   - Predictive Analytics integration

4. **Advanced Security Features**
   - Zero-day simulation
   - APT simulation
   - Insider threat detection

## 📞 Support

Nếu gặp vấn đề, vui lòng:

1. Kiểm tra logs trong `/workspace/logs/`
2. Chạy health checks
3. Xem troubleshooting guide
4. Tạo issue trên GitHub

For support, please:

1. Check logs in `/workspace/logs/`
2. Run health checks
3. Review troubleshooting guide
4. Create GitHub issue

---

**⚠️ Lưu ý quan trọng / Important Notice:**

- Luôn chạy tests trong sandbox environment
- Không bao giờ sử dụng real data trong tests
- Monitor resource usage thường xuyên
- Clean up sandboxes sau khi sử dụng

- Always run tests in sandbox environment
- Never use real data in tests
- Monitor resource usage regularly
- Clean up sandboxes after use
