# Privacy Mode - StillMe AI Framework

## Overview

StillMe AI Framework implements comprehensive privacy controls to protect user data while enabling intelligent habit learning and reflex responses.

## Privacy Principles

### 1. Opt-in by Default
- **Habit Learning**: Disabled by default (`habits_opt_in: false`)
- **Data Collection**: Minimal by default, explicit consent required
- **Analytics**: Anonymized and aggregated only

### 2. Data Minimization
- **Cue Hashing**: User input cues are hashed (SHA256) for privacy
- **TTL/Retention**: Automatic data expiration (default: 90 days)
- **No Raw PII**: No personal identifiable information stored in habit data

### 3. User Control
- **Export**: Full data export capability (GDPR compliance)
- **Delete**: Complete data deletion on request
- **Opt-out**: Immediate cessation of data collection

## Privacy Features

### Habit Store Privacy

```yaml
# config/reflex_engine.yaml
privacy:
  enabled: true
  habits_opt_in: false  # Default: opt-out
  hash_cues: true       # Hash user input cues
  ttl_days: 90         # 90 days retention
```

#### Cue Hashing
- User input cues are hashed using SHA256
- Only first 16 characters stored for debugging
- Original text never stored
- Example: "Hello world" → "a948904f2f0f"

#### Data Retention
- **TTL (Time To Live)**: Automatic deletion after 90 days
- **Decay**: Habit confidence decreases over time if unused
- **Cleanup**: Expired habits automatically removed

#### Quorum Requirements
- Habits only created after multiple observations
- Prevents single-user poisoning attacks
- Default: 3 observations within 7 days

### Observability Privacy

#### Logging
- **Trace IDs**: Unique identifiers for request tracking
- **No PII**: User IDs and tenant IDs only (no names/emails)
- **Structured Logs**: JSON format for easy filtering

#### Metrics
- **Aggregated Only**: No individual user tracking
- **Anonymized**: Statistical data only
- **Retention**: Metrics data expires automatically

## Configuration

### Environment Variables
```bash
# Privacy settings
STILLME__PRIVACY__ENABLED=true
STILLME__PRIVACY__HABITS_OPT_IN=false
STILLME__PRIVACY__HASH_CUES=true
STILLME__PRIVACY__TTL_DAYS=90

# Quorum settings
STILLME__QUORUM__THRESHOLD=3
STILLME__QUORUM__WINDOW_DAYS=7

# Decay settings
STILLME__DECAY__HALF_LIFE_DAYS=30
STILLME__DECAY__MIN_THRESHOLD=0.1
```

### Runtime Configuration
```python
from stillme_core.middleware.habit_store import HabitStore

# Initialize with privacy settings
habit_store = HabitStore({
    "privacy": {
        "enabled": True,
        "habits_opt_in": False,  # User must opt-in
        "hash_cues": True,
        "ttl_days": 90
    },
    "quorum": {
        "threshold": 3,
        "window_days": 7
    },
    "decay": {
        "half_life_days": 30,
        "min_threshold": 0.1
    }
})
```

## GDPR Compliance

### Data Subject Rights

#### Right to Access
```python
# Export all user data
export_data = habit_store.export_habits(user_id="user123")
```

#### Right to Erasure
```python
# Delete all user data
deleted_count = habit_store.delete_habits(user_id="user123")
```

#### Right to Portability
- Data exported in JSON format
- Includes all habit data and metadata
- Can be imported into other systems

### Data Processing Lawfulness
- **Consent**: Explicit opt-in for habit learning
- **Legitimate Interest**: System optimization and safety
- **Contract**: Service delivery and functionality

## Security Measures

### Data Protection
- **Encryption**: Data encrypted at rest and in transit
- **Access Control**: Role-based access to sensitive data
- **Audit Logs**: All data access logged and monitored

### Threat Mitigation
- **Habit Poisoning**: Quorum requirements prevent single-user attacks
- **Data Leakage**: Cue hashing prevents input reconstruction
- **Timing Attacks**: Decay mechanisms prevent long-term tracking

## Monitoring and Compliance

### Privacy Metrics
- **Opt-in Rate**: Percentage of users who enable habit learning
- **Data Retention**: Average age of stored habits
- **Deletion Rate**: Frequency of data deletion requests

### Compliance Monitoring
- **Data Minimization**: Regular audits of stored data
- **Retention Compliance**: Automated TTL enforcement
- **Access Logs**: Monitoring of data access patterns

## Best Practices

### For Developers
1. **Always check opt-in status** before collecting data
2. **Use structured logging** with no PII
3. **Implement data export/deletion** endpoints
4. **Regular privacy audits** of stored data

### For Users
1. **Review privacy settings** before enabling features
2. **Understand data retention** policies
3. **Use export/delete** features as needed
4. **Report privacy concerns** immediately

## Privacy by Design

### Architecture
- **Privacy First**: Privacy controls built into core architecture
- **Minimal Data**: Only necessary data collected and stored
- **User Control**: Users have full control over their data

### Implementation
- **Default Privacy**: Privacy-protective defaults
- **Transparency**: Clear privacy policies and controls
- **Accountability**: Regular privacy impact assessments

## Contact and Support

For privacy-related questions or concerns:
- **Privacy Officer**: privacy@stillme.ai
- **Data Protection**: dpo@stillme.ai
- **Security Issues**: security@stillme.ai

## Updates

This privacy policy is updated regularly to reflect:
- New privacy features
- Regulatory changes
- User feedback and concerns
- Technical improvements

Last updated: 2024-01-15
