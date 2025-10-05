# 🚀 Phase 6 - AgentDev Self-Improvement Loop Deployment Guide

## 📋 Overview

This guide covers the deployment and production setup of the AgentDev Self-Improvement Loop system, including CI/CD integration, monitoring, and automated error fixing.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub CI     │───▶│  Autofix Loop   │───▶│   Production    │
│   Workflow      │    │   Pipeline      │    │   Deployment    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Artifacts     │    │   Monitoring    │    │   Health Check  │
│   Collection    │    │   & Metrics     │    │   & Validation  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Components

### 1. CI/CD Pipeline (`.github/workflows/ci-autofix.yml`)

**Features:**
- Automated test execution
- Autofix loop integration
- PR creation for successful fixes
- Artifact collection and storage
- Quality gate enforcement

**Workflow:**
1. **Initial Checks**: Run linting, type checking, tests
2. **Autofix Detection**: Check if fixes are needed
3. **Self-Improvement Loop**: Apply automated fixes
4. **Validation**: Re-run tests after fixes
5. **PR Creation**: Create PR for successful fixes
6. **Artifact Collection**: Store reports and metrics

### 2. Production Configuration (`agent_dev/config/production.py`)

**Configuration Sections:**
- **Database**: Production database settings
- **Autofix**: Self-improvement loop parameters
- **Monitoring**: Logging and metrics collection
- **Security**: Security scanning and validation
- **Performance**: Resource limits and optimization
- **Quality Gates**: Coverage and error thresholds

**Environment Variables:**
```bash
# Required
AGENTDEV_DATABASE_URL=sqlite:///agentdev_prod.db
AGENTDEV_LOG_LEVEL=INFO

# Optional
AGENTDEV_MAX_TRIES=3
AGENTDEV_ENABLE_LEARNING=true
AGENTDEV_ANOMALY_THRESHOLD=10.0
AGENTDEV_MIN_COVERAGE=85.0
```

### 3. Deployment Script (`scripts/deploy_autofix.py`)

**Capabilities:**
- Environment validation
- Database setup
- Monitoring configuration
- Health checks
- Production cycle execution

**Usage:**
```bash
# Validate environment
python scripts/deploy_autofix.py --validate-only

# Run health check
python scripts/deploy_autofix.py --health-check

# Run production cycle
python scripts/deploy_autofix.py --run-cycle

# Full deployment
python scripts/deploy_autofix.py
```

## 📊 Monitoring & Metrics

### Metrics Collection

**Database Tables:**
- `feedback_events`: Error patterns and fix outcomes
- `rule_definitions`: Rule definitions and hit counts
- `metrics_daily`: Daily performance metrics
- `patch_history`: Applied fixes and improvements

**Key Metrics:**
- Test pass rate
- Coverage percentage
- Error reduction
- Fix success rate
- Learning progress

### Anomaly Detection

**Thresholds:**
- Pass rate drop > 10%
- Coverage drop > 10%
- Error increase > 50%
- Z-score > 2.0

**Alerts:**
- Slack notifications
- Email alerts
- GitHub comments
- Dashboard updates

## 🛡️ Security & Quality

### Security Rules (`rulesets/security_rules.yaml`)

**Detection Patterns:**
- Hardcoded secrets
- SQL injection
- Path traversal
- Command injection
- Unsafe deserialization
- Weak cryptography
- Insecure random
- HTTP without HTTPS
- Debug code
- Type ignore abuse

### Quality Gates

**Requirements:**
- All tests must pass
- Coverage ≥ 85% overall
- Coverage ≥ 90% on touched files
- Zero Pyright errors
- Zero Ruff errors
- No `# type: ignore` abuse
- No commented-out code

## 🚀 Deployment Process

### 1. Pre-deployment

```bash
# Validate environment
python scripts/deploy_autofix.py --validate-only

# Check configuration
python -c "from agent_dev.config.production import validate_environment; print(validate_environment())"
```

### 2. Database Setup

```bash
# Create production database
python -c "
from agent_dev.persistence.models import create_database_engine, Base
engine = create_database_engine('sqlite:///agentdev_prod.db')
Base.metadata.create_all(engine)
print('Database created successfully')
"
```

### 3. CI/CD Integration

```yaml
# Add to .github/workflows/ci.yml
- name: Run AgentDev Autofix
  uses: ./.github/workflows/ci-autofix.yml
  if: failure()
```

### 4. Monitoring Setup

```bash
# Create log directory
mkdir -p logs

# Test monitoring
python -c "
from agent_dev.self_monitoring import MonitoringSystem
from agent_dev.persistence.repo import AgentDevRepo
from agent_dev.persistence.models import create_database_engine

engine = create_database_engine('sqlite:///agentdev_prod.db')
repo = AgentDevRepo(engine)
monitoring = MonitoringSystem(repo)

# Test logging
monitoring.log_run({'timestamp': '2025-01-01T00:00:00Z', 'pass_rate': 100.0})
print('Monitoring setup successful')
"
```

## 📈 Performance Optimization

### Resource Limits

**Configuration:**
- Max concurrent fixes: 3
- Fix timeout: 60 seconds
- Memory limit: 1024 MB
- Database pool size: 10
- Max overflow: 20

### Optimization Strategies

1. **Parallel Processing**: Enable concurrent fix application
2. **Caching**: Cache rule patterns and results
3. **Database Optimization**: Use connection pooling
4. **Memory Management**: Monitor and limit memory usage
5. **Timeout Handling**: Prevent hanging operations

## 🔍 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check database URL
echo $AGENTDEV_DATABASE_URL

# Test connection
python -c "from agent_dev.persistence.models import create_database_engine; engine = create_database_engine('$AGENTDEV_DATABASE_URL'); print('Connection successful')"
```

**2. Rule Engine Errors**
```bash
# Check rules file
ls -la rulesets/agentdev_rules.yaml

# Validate YAML
python -c "import yaml; yaml.safe_load(open('rulesets/agentdev_rules.yaml'))"
```

**3. Monitoring Issues**
```bash
# Check log directory
ls -la logs/

# Test monitoring
python scripts/deploy_autofix.py --health-check
```

### Health Check Commands

```bash
# Full health check
python scripts/deploy_autofix.py --health-check

# Database health
python -c "from agent_dev.persistence.repo import AgentDevRepo; repo = AgentDevRepo(engine); print('Database OK')"

# Monitoring health
python -c "from agent_dev.self_monitoring import MonitoringSystem; print('Monitoring OK')"

# Autofix health
python -c "from agent_dev.auto_fix import AutoFixSystem; print('Autofix OK')"
```

## 📚 API Reference

### Core Classes

**AutoFixSystem**
```python
from agent_dev.auto_fix import AutoFixSystem

autofix = AutoFixSystem(db_path="agentdev.db")
result = autofix.run_autofix_cycle()
```

**MonitoringSystem**
```python
from agent_dev.self_monitoring import MonitoringSystem

monitoring = MonitoringSystem(repo)
monitoring.log_run(metrics)
monitoring.record_metrics(metrics)
```

**RuleEngine**
```python
from agent_dev.rules.engine import RuleEngine

engine = RuleEngine()
engine.load_yaml_rules()
matching_rules = engine.find_matching_rules(error_text)
```

## 🎯 Success Metrics

### Deployment Success Criteria

- [ ] All tests passing (100%)
- [ ] Coverage ≥ 85% overall
- [ ] Coverage ≥ 90% on touched files
- [ ] Zero Pyright errors
- [ ] Zero Ruff errors
- [ ] Health check passing
- [ ] Monitoring active
- [ ] Autofix functional
- [ ] CI/CD integrated
- [ ] Documentation complete

### Performance Targets

- **Response Time**: < 5 seconds for autofix cycle
- **Success Rate**: > 90% for fix application
- **Coverage**: Maintain or improve coverage
- **Error Reduction**: > 50% error reduction
- **Learning**: Rule hit count increases

## 🔄 Maintenance

### Regular Tasks

1. **Daily**: Check health status
2. **Weekly**: Review metrics and anomalies
3. **Monthly**: Update rules and patterns
4. **Quarterly**: Performance optimization

### Updates

```bash
# Update rules
git pull origin main
python scripts/deploy_autofix.py --validate-only

# Update configuration
# Edit agent_dev/config/production.py
python scripts/deploy_autofix.py --health-check
```

## 📞 Support

### Documentation
- [Phase 5 Guide](PHASE5_SELF_IMPROVEMENT.md)
- [API Reference](API_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

### Contact
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: security@stillme.ai

---

**Generated by AgentDev Self-Improvement Loop** 🤖

**ko dùng # type: ignore và ko dùng comment out để che giấu lỗi**
