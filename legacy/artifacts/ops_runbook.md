# AgentDev Operations Runbook - 24/7 Technical Manager

## 🎯 Overview

AgentDev Operations Service is a 24/7 automated technical manager that continuously monitors, maintains, and escalates issues in the StillMe codebase.

## 📋 Components

### Core Modules
- **PatrolRunner**: Executes periodic health checks
- **IssueClassifier**: Categorizes issues by severity
- **EscalationManager**: Handles incident response
- **Notifiers**: Email and Telegram alerting

### Entry Points
- **Main Service**: `scripts/start_agentdev_monitor.py`
- **Windows Scheduler**: `scripts/install_windows_task.ps1`

## ⏰ Patrol Schedule

### Quick Patrol (Every 15 minutes)
- **Ruff Check**: Fast linting scan
- **Pytest Smoke**: Basic test validation
- **Auto-fix**: Minor issues (W293, W291, I001, F401)

### Deep Patrol (Every 6 hours)
- **Full Quick Patrol**: All quick patrol checks
- **Red-Team Security**: Light security pattern scanning
- **Comprehensive Analysis**: Full system health assessment

## 🚨 Issue Classification

### MINOR Issues
- **Rules**: W293, W291, I001, F401
- **Action**: Auto-fix with `ruff --fix`
- **Escalation**: None (logged only)

### MAJOR Issues
- **Rules**: F821, E999, ImportError, SyntaxError
- **Action**: Escalate to technical team
- **Channels**: Email + Telegram
- **Severity**: SEV-2

### SECURITY Issues
- **Patterns**: Hardcoded secrets, unsafe functions
- **Action**: Immediate escalation
- **Channels**: Email + Telegram
- **Severity**: SEV-1

## 📧 Notification Channels

### Email Configuration
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL=alerts@yourcompany.com
```

### Telegram Configuration
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🔧 Management Commands

### Start Service
```bash
# Normal mode
python scripts/start_agentdev_monitor.py

# Daemon mode
python scripts/start_agentdev_monitor.py --daemon

# Dry run (test)
python scripts/start_agentdev_monitor.py --dry-run
```

### Windows Task Scheduler
```powershell
# Install task
.\scripts\install_windows_task.ps1

# Remove task
.\scripts\install_windows_task.ps1 -Remove

# View task
Get-ScheduledTask -TaskName "AgentDevOpsService"
```

### Monitor Logs
```bash
# Real-time logs
Get-Content logs\agentdev_ops.log -Tail 20 -Wait

# View recent activity
Get-Content logs\agentdev_ops.log -Tail 100
```

## 📊 Incident Response

### SEV-1 (Security)
- **Title**: `[SEV-1] Rủi ro bảo mật (Risk Score: X.XX)`
- **Response Time**: Immediate
- **Action**: Review security findings, apply mitigations

### SEV-2 (Major)
- **Title**: `[SEV-2] Lỗi kiểm thử logic module X`
- **Response Time**: Within 1 hour
- **Action**: Fix test failures, resolve import errors

### SEV-3 (Minor)
- **Title**: `[SEV-3] Lỗi chất lượng code (X lỗi)`
- **Response Time**: Within 4 hours
- **Action**: Review auto-fixes, manual cleanup if needed

## 🛡️ Pre-flight Checks

Before any operations, AgentDev performs mandatory inventory checks:

1. **Core Modules**: Verify essential files exist
2. **Duplicate Detection**: Check for conflicting versions
3. **Import Validation**: Ensure clean import paths

If pre-flight fails, operations are halted and issues reported.

## 🔄 Rollback Procedures

### Automatic Rollback
- Triggered when `errors_after >= errors_before`
- Restores from backup directory
- Logs rollback reason

### Manual Rollback
```bash
# Restore from backup
cp -r agentdev_backups/backup_YYYYMMDD_HHMMSS/* .

# Verify restoration
python scripts/start_agentdev_monitor.py --dry-run
```

## 📈 Performance Metrics

### Key Indicators
- **Patrol Success Rate**: Target >95%
- **Auto-fix Success**: Target >80%
- **Response Time**: <5 minutes for SEV-1
- **False Positive Rate**: <10%

### Monitoring
- Log files: `logs/agentdev_ops.log`
- Metrics: Patrol duration, issue counts, escalation rates
- Alerts: Failed patrols, high error rates

## 🚀 Deployment

### Production Setup
1. Configure environment variables
2. Install Windows task scheduler
3. Verify notification channels
4. Run initial dry-run test
5. Start service in daemon mode

### Maintenance
- Weekly log rotation
- Monthly performance review
- Quarterly security assessment
- Annual configuration audit

## 📞 Support

### Troubleshooting
- Check logs: `logs/agentdev_ops.log`
- Verify configuration: Environment variables
- Test notifications: `--dry-run` mode
- Validate imports: Pre-flight checks

### Emergency Procedures
- Stop service: `Stop-ScheduledTask -TaskName "AgentDevOpsService"`
- Manual patrol: `python scripts/start_agentdev_monitor.py --dry-run`
- Escalate to technical lead if service fails

---

**Last Updated**: 2025-10-01  
**Version**: 1.0  
**Maintainer**: AgentDev Operations Team
