# StillMe Rollback Guide

## Overview

This guide provides comprehensive instructions for rolling back StillMe deployments across different environments and deployment strategies.

---

## **🔄 Rollback Strategies**

### **Rollback Types**

1. **Application Rollback**: Rollback to previous application version
2. **Configuration Rollback**: Rollback to previous configuration
3. **Database Rollback**: Rollback database changes
4. **Infrastructure Rollback**: Rollback infrastructure changes

### **Rollback Triggers**

- **Health Check Failures**: Continuous health check failures
- **High Error Rate**: Error rate > 5%
- **Performance Degradation**: P95 latency > 1000ms
- **Security Incidents**: Security breach or compromise
- **Manual Override**: Manual rollback decision

---

## **🐳 Docker Rollback**

### **Quick Rollback**

```bash
# Rollback to previous version
make rollback TAG=v1.2.3

# Or use rollback script directly
./scripts/rollback.sh --tag v1.2.3
```

### **Manual Docker Rollback**

#### **1. Identify Current Version**

```bash
# Check current running version
docker ps --filter "name=stillme" --format "table {{.Image}}"

# Check available versions
docker images stillme --format "table {{.Tag}}"
```

#### **2. Stop Current Container**

```bash
# Stop current container
docker stop stillme-prod

# Remove current container
docker rm stillme-prod
```

#### **3. Start Previous Version**

```bash
# Start previous version
docker run -d \
  --name stillme-prod \
  --restart unless-stopped \
  -p 8080:8080 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  stillme:v1.2.3

# Verify rollback
curl http://localhost:8080/healthz
```

### **Docker Compose Rollback**

#### **1. Update docker-compose.yml**

```yaml
# docker-compose.prod.yml
services:
  stillme-prod:
    image: stillme:v1.2.3  # Previous version
    # ... rest of configuration
```

#### **2. Deploy Previous Version**

```bash
# Deploy previous version
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Verify rollback
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8080/healthz
```

---

## **☸️ Kubernetes Rollback**

### **Deployment Rollback**

#### **1. Check Deployment History**

```bash
# Check deployment history
kubectl rollout history deployment/stillme -n stillme

# Check specific revision
kubectl rollout history deployment/stillme --revision=2 -n stillme
```

#### **2. Rollback to Previous Version**

```bash
# Rollback to previous version
kubectl rollout undo deployment/stillme -n stillme

# Rollback to specific revision
kubectl rollout undo deployment/stillme --to-revision=2 -n stillme
```

#### **3. Verify Rollback**

```bash
# Check rollout status
kubectl rollout status deployment/stillme -n stillme

# Check pod status
kubectl get pods -n stillme

# Check service health
kubectl port-forward svc/stillme 8080:8080 -n stillme
curl http://localhost:8080/healthz
```

### **Blue-Green Rollback**

#### **1. Switch Traffic Back**

```bash
# Switch traffic back to blue
kubectl patch service stillme -p '{"spec":{"selector":{"version":"blue"}}}'

# Verify traffic switch
kubectl get svc stillme -n stillme -o yaml
```

#### **2. Scale Down Green**

```bash
# Scale down green deployment
kubectl scale deployment stillme-green --replicas=0 -n stillme

# Verify green is scaled down
kubectl get pods -n stillme
```

### **Canary Rollback**

#### **1. Pause Canary**

```bash
# Pause canary rollout
kubectl patch rollout stillme -p '{"spec":{"paused":true}}' -n stillme

# Check rollout status
kubectl get rollout stillme -n stillme
```

#### **2. Rollback Canary**

```bash
# Rollback canary to stable version
kubectl patch rollout stillme -p '{"spec":{"rollbackTo":{"revision":1}}}' -n stillme

# Verify rollback
kubectl rollout status rollout/stillme -n stillme
```

---

## **🔧 Automated Rollback**

### **Rollback Script**

#### **Script Usage**

```bash
# Basic rollback
./scripts/rollback.sh --tag v1.2.3

# Rollback with namespace
./scripts/rollback.sh --tag v1.2.3 --namespace production

# Rollback with service name
./scripts/rollback.sh --tag v1.2.3 --service stillme-api

# Rollback with custom health check URL
./scripts/rollback.sh --tag v1.2.3 --url http://api.stillme.ai/healthz
```

#### **Script Options**

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tag` | Previous tag to rollback to | Required |
| `-n, --namespace` | Kubernetes namespace | `stillme` |
| `-s, --service` | Service name | `stillme-prod` |
| `-u, --url` | Health check URL | `http://localhost:8080/healthz` |
| `-h, --help` | Show help message | - |

### **GitHub Actions Rollback**

#### **Manual Rollback Workflow**

```yaml
# .github/workflows/rollback.yml
name: Manual Rollback

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rollback'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - staging
      tag:
        description: 'Tag to rollback to'
        required: true
        type: string

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Rollback deployment
      run: |
        ./scripts/rollback.sh --tag ${{ github.event.inputs.tag }} --namespace ${{ github.event.inputs.environment }}
    
    - name: Verify rollback
      run: |
        curl -f http://localhost:8080/healthz
        curl -f http://localhost:8080/readyz
```

#### **Trigger Rollback**

```bash
# Trigger rollback via GitHub CLI
gh workflow run rollback.yml -f environment=production -f tag=v1.2.3

# Or via GitHub UI
# Go to Actions > Manual Rollback > Run workflow
```

---

## **📊 Rollback Verification**

### **Health Checks**

#### **1. Service Health**

```bash
# Check liveness probe
curl http://localhost:8080/healthz

# Check readiness probe
curl http://localhost:8080/readyz

# Check metrics endpoint
curl http://localhost:8080/metrics
```

#### **2. Application Health**

```bash
# Check application logs
kubectl logs -f deployment/stillme -n stillme

# Check for errors
kubectl logs deployment/stillme -n stillme | grep ERROR

# Check resource usage
kubectl top pods -n stillme
```

### **Performance Verification**

#### **1. Load Testing**

```bash
# Run load tests
make load-test

# Check performance metrics
curl http://localhost:8080/metrics | grep http_request_duration
```

#### **2. SLO Compliance**

```bash
# Check SLO compliance
curl http://localhost:8080/metrics | grep -E "(p95|error_rate|availability)"
```

### **Security Verification**

#### **1. Security Headers**

```bash
# Check security headers
curl -I http://localhost:8080/ | grep -E "(X-|Strict-|Content-Security)"
```

#### **2. Security Scans**

```bash
# Run security scans
make security

# Check security compliance
curl http://localhost:8080/security/status
```

---

## **🚨 Emergency Rollback**

### **Emergency Procedures**

#### **1. Immediate Rollback**

```bash
# Emergency rollback script
./scripts/emergency_rollback.sh

# Or manual emergency rollback
kubectl rollout undo deployment/stillme -n stillme
kubectl rollout status deployment/stillme -n stillme
```

#### **2. Kill Switch Activation**

```bash
# Activate kill switch
curl -X POST http://localhost:8080/security/kill-switch/activate

# Verify kill switch
curl http://localhost:8080/security/kill-switch/status
```

#### **3. Service Isolation**

```bash
# Scale down service
kubectl scale deployment stillme --replicas=0 -n stillme

# Or delete service
kubectl delete deployment stillme -n stillme
```

### **Emergency Contacts**

- **On-Call Engineer**: +1-XXX-XXX-XXXX
- **Security Team**: security@stillme.ai
- **Management**: management@stillme.ai
- **Incident Response**: incident@stillme.ai

---

## **📋 Rollback Checklist**

### **Pre-Rollback Checklist**

- [ ] **Identify Issue**: Document the issue requiring rollback
- [ ] **Assess Impact**: Determine scope and impact of rollback
- [ ] **Notify Team**: Inform relevant team members
- [ ] **Backup Data**: Ensure data is backed up
- [ ] **Test Rollback**: Test rollback procedure in staging
- [ ] **Prepare Rollback**: Identify target version for rollback

### **Rollback Execution Checklist**

- [ ] **Stop Traffic**: Stop traffic to affected service
- [ ] **Execute Rollback**: Run rollback procedure
- [ ] **Verify Health**: Check service health endpoints
- [ ] **Test Functionality**: Verify core functionality
- [ ] **Monitor Metrics**: Watch key performance metrics
- [ ] **Check Logs**: Review application logs for errors

### **Post-Rollback Checklist**

- [ ] **Verify Rollback**: Confirm rollback was successful
- [ ] **Monitor System**: Monitor system for 24-48 hours
- [ ] **Document Incident**: Document incident and rollback
- [ ] **Root Cause Analysis**: Investigate root cause
- [ ] **Update Procedures**: Update rollback procedures if needed
- [ ] **Team Communication**: Communicate status to team

---

## **🔍 Troubleshooting**

### **Common Rollback Issues**

#### **1. Rollback Fails**

```bash
# Check deployment status
kubectl get deployment stillme -n stillme

# Check pod status
kubectl get pods -n stillme

# Check events
kubectl get events -n stillme --sort-by='.lastTimestamp'

# Check logs
kubectl logs deployment/stillme -n stillme
```

#### **2. Health Checks Fail**

```bash
# Check health endpoints
curl -v http://localhost:8080/healthz
curl -v http://localhost:8080/readyz

# Check service configuration
kubectl describe service stillme -n stillme

# Check ingress
kubectl describe ingress stillme -n stillme
```

#### **3. Performance Issues**

```bash
# Check resource usage
kubectl top pods -n stillme
kubectl top nodes

# Check metrics
curl http://localhost:8080/metrics

# Check for resource limits
kubectl describe pod -l app=stillme -n stillme
```

### **Debug Commands**

```bash
# Debug pod
kubectl debug pod/stillme-xxx -n stillme

# Port forward for debugging
kubectl port-forward svc/stillme 8080:8080 -n stillme

# Execute commands in pod
kubectl exec -it deployment/stillme -n stillme -- /bin/bash

# Check configuration
kubectl describe configmap stillme-config -n stillme
kubectl describe secret stillme-secrets -n stillme
```

---

## **📚 Best Practices**

### **Rollback Best Practices**

1. **Automated Rollback**: Implement automated rollback triggers
2. **Health Checks**: Comprehensive health check validation
3. **Monitoring**: Real-time monitoring during rollback
4. **Documentation**: Document all rollback procedures
5. **Testing**: Regular rollback testing in staging

### **Prevention Best Practices**

1. **Staging Testing**: Thorough testing in staging environment
2. **Canary Deployments**: Use canary deployments for risky changes
3. **Feature Flags**: Use feature flags for gradual rollouts
4. **Monitoring**: Comprehensive monitoring and alerting
5. **Backup Strategy**: Regular backups and recovery testing

### **Communication Best Practices**

1. **Incident Communication**: Clear incident communication
2. **Status Updates**: Regular status updates during rollback
3. **Post-Incident Review**: Conduct post-incident reviews
4. **Lessons Learned**: Document and share lessons learned
5. **Team Training**: Regular team training on rollback procedures

---

## **🔗 Additional Resources**

### **Documentation**

- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [CI/CD Overview](CI_CD_OVERVIEW.md)
- [Security Operations](SECURITY_OPERATIONS.md)
- [Monitoring Guide](MONITORING_GUIDE.md)

### **Tools**

- [kubectl](https://kubernetes.io/docs/reference/kubectl/)
- [Docker](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

### **Support**

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/stillme-ai/stillme/issues)
- **Security**: [SECURITY.md](../SECURITY.md)
- **Community**: [GitHub Discussions](https://github.com/stillme-ai/stillme/discussions)

---

**Last Updated**: $(date)
**Next Review**: $(date -d "+3 months")
**Maintainer**: StillMe DevOps Team
