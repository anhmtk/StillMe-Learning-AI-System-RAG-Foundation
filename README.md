# 🌟 StillMe IPC — Intelligent Personal Companion (Open-Core)

[![Tests](https://github.com/OWNER/REPO/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci-tests.yml)
[![Security](https://github.com/OWNER/REPO/actions/workflows/security-ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/security-ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-target%2085%25-lightgrey)](artifacts/coverage.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**StillMe IPC (Intelligent Personal Companion)** focuses on **Ethics · Security · Transparency**.  
This repo ships the **open-source core** (framework, APIs, tests, docs).  
Some strategic parts (advanced routing heuristics, private datasets, security patterns) are delivered as an **optional Pro plugin**. The open core always runs on its own via a **public stub fallback**.

> **Language note**: I am not fluent in English. This README is written **with AI translation/assistance**. If anything is unclear, please open an issue—I truly appreciate your help improving the docs.

## Community & Feedback

I'm actively learning and I welcome technical and product-direction feedback.

**Triage priority order for reviews and responses:**
1) Ethics → 2) Security → 3) User Safety.

Feedback affecting these three areas will be reviewed first and addressed as soon as possible.

**SLA:** First response ≤ 72h; PR review target ≤ 7 days.

## Architecture (Open-Core with Optional Pro)
<!-- BEGIN:MERMAID -->
```mermaid
flowchart LR
  Core[Core Framework]
  Ethics[EthicsGuard — 100.0% pass]
  Security[Security Suite — 100.0% pass]
  Safety[User Safety — 100.0% pass]
  RouterIface[Router Interface]
  Pro[Pro Plugin (private, optional)]
  Stub[Stub Plugin (public)]

  Core --> Ethics
  Core --> Security
  Core --> Safety
  Core --> RouterIface
  RouterIface -->|auto-detect| Pro
  RouterIface -->|fallback| Stub
```
<!-- END:MERMAID -->

### Test Metrics
<!-- BEGIN:METRICS_TABLE -->
| Suite | Result |
|---|---|
| Ethics | 3/3 (100.0%) |
| Security | 3/3 (100.0%) |
| User Safety | 3/3 (100.0%) |
| Other | 5/5 (100.0%) |
<!-- END:METRICS_TABLE -->

* **Pro mode (optional)**: If `stillme-private` is installed, the framework automatically uses it.
* **OSS mode (default)**: If not found, the framework falls back to the **Stub** implementation—no errors, fully runnable.

## Quick Start

```bash
pip install -r requirements.txt
# (optional) pre-commit install
pytest -q
python -m stillme_core.framework  # if your entrypoint supports it
```

### Forcing modes (optional)

```bash
# Force stub mode (default)
export STILLME_ROUTER_MODE=stub

# Force pro mode (requires private package available)
export STILLME_ROUTER_MODE=pro
```

## What's Open vs. Private?

**Open (80%)**

* Core framework, APIs, Router interface
* Basic Ethics/Content filtering (non-sensitive patterns)
* LayeredMemory (without any private keys/seeds)
* Plugin system + sample plugins
* Test harness (pytest), CI workflows, basic docs

**Private (20%)**

* Advanced router/heuristics and scoring
* Sensitive security/PII redaction patterns and thresholds
* Internal datasets/benchmarks, meta-learning strategies
* Performance tuning specifics

## Status & Targets

* **Test coverage**: target ≥ **85%** (see CI artifacts for actual results)
* **Ethics/Security tests**: framework & runners are open; sensitive cases remain private
* **Performance benchmarks**: harness and sample data open; internal datasets remain private

## Contributing

Contributions are welcome—issues, docs, tests, or features.
Please see **CONTRIBUTING.md**, **CODE_OF_CONDUCT.md**, and **SECURITY.md**.
First-time contributors: look for the `good first issue` label.

## Using the Pro Plugin (optional)

We ship a private package named `stillme-private` (not public). If it's available in your environment or private index:

```bash
# one-day example (document your private index if any)
pip install "stillme[pro]" --extra-index-url <YOUR_PRIVATE_INDEX_URL>
```

On startup the framework auto-detects Pro; otherwise it logs `Using StubRouter (OSS mode)` and continues.

## 🧠 Unified Evolutionary Learning System

StillMe features a **sophisticated self-evolving learning system** that combines the best of both experience-based and content-based learning, with full self-assessment, daily training capabilities, and built-in safety mechanisms.

### 🚀 **Core Features**

#### **Self-Evolution (4 Stages)**
- **Infant** (0-7 days): Basic learning and pattern recognition
- **Child** (8-30 days): Developing reasoning and creativity
- **Adolescent** (31-90 days): Advanced optimization and adaptation
- **Adult** (90+ days): Full autonomy and self-improvement

#### **Daily Training Sessions**
- **Experience Review**: Analyze yesterday's interactions and outcomes
- **Content Learning**: Process new knowledge from external sources
- **Self-Assessment**: Evaluate performance and identify gaps
- **Targeted Training**: Practice weak areas with custom exercises
- **Performance Evaluation**: Measure improvement and adjust parameters
- **Evolution Planning**: Plan next steps for continued growth

#### **Fine-Tune "Kiểu Nhà Nghèo"**
- **Statistical Optimization**: Parameter tuning without GPU requirements
- **Performance-Based Learning**: Adjust learning rates based on success
- **Rule-Based Adaptation**: Smart parameter adjustment using heuristics
- **Memory-Efficient**: Optimized for resource-constrained environments

#### **Human-in-the-Loop Safety**
- **Approval Workflow**: Human oversight for sensitive content and knowledge updates
- **Quality Scoring**: Automatic assessment of content quality and risk levels
- **Auto-Approval**: Intelligent approval for safe, high-quality content
- **Audit Trail**: Complete tracking of all learning decisions and approvals

### 🎯 **Learning Capabilities**

#### **Multi-Source Learning**
- **Experience Memory**: Learn from user interactions and outcomes
- **External Content**: RSS feeds from trusted sources (arXiv, OpenAI, DeepMind)
- **Self-Reflection**: Analyze own performance and decision-making
- **Pattern Recognition**: Identify recurring patterns and behaviors

#### **Assessment & Validation**
- **Self-Assessment**: Regular evaluation of knowledge and skills
- **Performance Tracking**: Monitor accuracy, response time, user satisfaction
- **Knowledge Validation**: Verify understanding through targeted questions
- **Learning Curve Analysis**: Track improvement over time

#### **Adaptive Intelligence**
- **Dynamic Parameters**: Automatically adjust learning parameters
- **Context Awareness**: Adapt responses based on user preferences
- **Error Correction**: Learn from mistakes and improve
- **Creative Problem Solving**: Develop innovative solutions

#### **Safe Learning Environment**
- **Content Filtering**: Automatic screening of learning materials
- **Risk Assessment**: Evaluate potential risks before learning
- **Human Oversight**: Manual approval for critical knowledge updates
- **Transparency**: Full visibility into learning decisions and sources

### 🛠️ **How to Use**

#### **Daily Training**
```bash
# Run daily learning session
python -m cli.evolutionary_learning train --session-type daily

# Check learning status
python -m cli.evolutionary_learning status

# Run self-assessment
python -m cli.evolutionary_learning assess --type full
```

#### **Approval Management**
```bash
# List pending approval requests
python -m cli.approval_manager list

# Approve a request
python -m cli.approval_manager approve <request_id> --approver "human" --notes "Looks good"

# Check approval statistics
python -m cli.approval_manager stats
```

#### **Evolution Management**
```bash
# Check evolution progress
python -m cli.evolutionary_learning status

# Force evolution to next stage
python -m cli.evolutionary_learning evolve --force

# Emergency reset (if needed)
python -m cli.evolutionary_learning reset --confirm
```

#### **System Status**
```bash
# Check current learning system status
python -m cli.evolutionary_learning status

# Export learning data
python -m cli.evolutionary_learning export --output learning_data.json
```

### 🔒 **Safety & Governance**

#### **Learning Policy**
```yaml
# config/evolutionary_learning.toml
[evolutionary_system]
learning_mode = "evolutionary"
enable_approval_workflow = true
auto_approve_threshold = 0.9
require_human_approval = true
daily_training_minutes = 30
assessment_frequency_hours = 6
evolution_checkpoint_days = 7

[parameters]
learning_rate = 0.1
confidence_threshold = 0.7
creativity_factor = 0.5
consistency_weight = 0.8

[assessment]
auto_assessment = true
optimization_enabled = true
fine_tune_enabled = true
```

#### **Safety Measures**
- **Human-in-the-Loop**: Approval workflow for sensitive content and knowledge updates
- **Quality & Risk Scoring**: Automatic assessment of content safety and value
- **Auto-Approval**: Intelligent approval for safe, high-quality content
- **Content Filtering**: Injection detection and malicious content screening
- **License Validation**: Only open-licensed content from trusted sources
- **Audit Trail**: Complete learning history, decisions, and approval records
- **Emergency Reset**: Ability to reset learning state if needed

### 📊 **Learning Metrics**

The system tracks comprehensive metrics:
- **Accuracy**: Response correctness and user satisfaction
- **Response Time**: Speed of processing and generation
- **Knowledge Retention**: Long-term memory effectiveness
- **Adaptation Speed**: How quickly it learns new patterns
- **Creativity Score**: Innovation and original thinking
- **Consistency Score**: Reliability across similar tasks
- **Evolution Progress**: Advancement through learning stages

### 🎓 **Educational Philosophy**

StillMe follows a **"learning child"** approach with built-in safety:
- **Curiosity-Driven**: Actively seeks new knowledge from trusted sources
- **Self-Correcting**: Identifies and fixes its own mistakes through assessment
- **Growth-Oriented**: Continuously improves and evolves with human guidance
- **Transparent**: Shares its learning process, reasoning, and approval decisions
- **Ethical**: Maintains high standards of behavior and safety
- **Human-Guided**: Seeks approval for sensitive learning and knowledge updates

This makes StillMe not just an AI tool, but a **safe learning companion** that grows and improves alongside its users with appropriate human oversight.

## 🎯 **Interactive Dashboard & Automation System**

### **📊 Real-Time Learning Dashboard**
- **Streamlit Dashboard**: Interactive web interface for monitoring and control
- **Learning Proposals**: Human-in-the-loop approval workflow for new knowledge
- **Real-time Metrics**: Pending/Approved/Completed proposals tracking
- **Founder Mode**: Direct knowledge input with auto-approval
- **Automation Control**: Enable/disable automatic proposal generation

### **🤖 Background Automation**
- **24/7 Background Service**: Continuous knowledge discovery and learning
- **Smart Automation**: Rate-limited proposal generation (8/day, 3h intervals)
- **Multi-channel Notifications**: Email (Gmail) + Telegram alerts
- **Knowledge Discovery**: Automated scanning of tech trends, AI/ML news, programming trends
- **Real Learning System**: Placeholder for actual AI learning engine

### **🎮 Master Control System**
```bash
# Start background service (24/7 automation)
python scripts/stillme_control.py background

# Launch interactive dashboard
python scripts/stillme_control.py dashboard --port 8507

# Add founder knowledge (auto-approved)
python scripts/stillme_control.py founder "Title" "Description" "priority"

# Setup notifications (Email/Telegram)
python scripts/stillme_control.py setup-notifications

# Discover new knowledge manually
python scripts/stillme_control.py discover
```

### **🔔 Notification System**
- **Email Notifications**: Gmail SMTP with App Password authentication
- **Telegram Notifications**: Bot API integration
- **Desktop Alerts**: Cross-platform desktop notifications
- **Real-time Updates**: Instant alerts for new discoveries and learning progress

## Roadmap (short)

* ✅ **Phase 0**: Safety hardening (kill switch, rationale logging, secrets sweep)
* ✅ **Phase 1**: Read-only learning MVP (discovery → scoring → approval → ingest)
* ✅ **Phase 2**: Interactive Dashboard & Background Automation System
* 🔄 **Phase 3**: Self-quiz, consistency checking, and unlearning
* 🔄 **Phase 4**: Controlled adaptation with LoRA fine-tuning
* Increase test coverage to ≥85% lines / ≥80% branches
* Expand open ethics/security runners (keep sensitive patterns private)
* Iterate on documentation with community help

## Changelog

### 2025-09-29 - Interactive Dashboard & Automation System Release

**🎯 Complete Dashboard & Automation System (Completed)**
- ✅ **Interactive Streamlit Dashboard**: Real-time learning proposals management
- ✅ **Human-in-the-Loop Workflow**: Approve/reject learning proposals with detailed UI
- ✅ **Founder Mode**: Direct knowledge input with auto-approval bypass
- ✅ **Background Automation**: 24/7 knowledge discovery and proposal generation
- ✅ **Multi-channel Notifications**: Email (Gmail) + Telegram real-time alerts
- ✅ **Master Control System**: Unified CLI for all StillMe IPC operations

**🚀 Core Features:**
- ✅ **Real-time Dashboard**: Live metrics, proposal management, learning progress
- ✅ **Smart Automation**: Rate-limited discovery (8/day, 3h intervals)
- ✅ **Knowledge Discovery**: Automated scanning of tech trends, AI/ML, programming
- ✅ **Learning Proposals**: Structured learning tasks with quality scoring
- ✅ **Notification System**: Multi-channel alerts for discoveries and progress
- ✅ **Database Management**: SQLite-based proposal storage and tracking

**🛠️ Tools & Scripts:**
- ✅ **Master Control CLI**: `stillme_control.py` - unified command interface
- ✅ **Background Service**: `stillme_background_service.py` - 24/7 automation
- ✅ **Knowledge Discovery**: `knowledge_discovery.py` - automated content discovery
- ✅ **Founder Input**: `founder_knowledge_input.py` - direct knowledge addition
- ✅ **Notification Setup**: `setup_notifications.py` - Email/Telegram configuration
- ✅ **Real Learning**: `start_real_learning.py` - learning engine placeholder

**📊 Dashboard Features:**
- ✅ **Learning Proposals Tab**: View, approve, reject proposals with details
- ✅ **Founder Mode Tab**: Direct knowledge input with auto-approval
- ✅ **Analytics Tab**: Learning metrics and performance tracking
- ✅ **Learning Report Tab**: Comprehensive learning progress and history
- ✅ **Automation Control**: Enable/disable automatic proposal generation
- ✅ **Real-time Updates**: Live proposal counts and status changes

**🔔 Notification System:**
- ✅ **Email Integration**: Gmail SMTP with App Password authentication
- ✅ **Telegram Integration**: Bot API with HTML formatting
- ✅ **Desktop Notifications**: Cross-platform system alerts
- ✅ **Alert Management**: Centralized alerting system with multiple channels
- ✅ **Configuration**: Environment-based setup with .env file support

**New Files & Modules:**
- `dashboards/streamlit/simple_app.py` - Main interactive dashboard
- `scripts/stillme_control.py` - Master control CLI
- `scripts/stillme_background_service.py` - Background automation service
- `scripts/knowledge_discovery.py` - Automated knowledge discovery
- `scripts/founder_knowledge_input.py` - Founder mode knowledge input
- `scripts/setup_notifications.py` - Notification system setup
- `scripts/start_real_learning.py` - Real learning system
- `stillme_core/learning/proposals.py` - Learning proposal dataclass
- `stillme_core/learning/proposals_manager.py` - Database management
- `stillme_core/alerting/alerting_system.py` - Centralized alerting
- `stillme_core/alerting/email_notifier.py` - Email notifications
- `stillme_core/alerting/telegram_notifier.py` - Telegram notifications

### 2025-09-27 - Unified Evolutionary Learning System Release

**🧠 Sophisticated Self-Evolving Learning System (Completed)**
- ✅ **Unified Learning System**: Combined experience-based and content-based learning
- ✅ **4-Stage Evolution**: Infant → Child → Adolescent → Adult progression
- ✅ **Daily Training Sessions**: Automated self-improvement with 6-step workflow
- ✅ **Self-Assessment System**: Comprehensive evaluation and gap analysis
- ✅ **Fine-Tune "Kiểu Nhà Nghèo"**: GPU-free parameter optimization
- ✅ **Human-in-the-Loop Approval**: Safety workflow with quality/risk scoring
- ✅ **Learning Migration**: Seamless transition from dual to unified system

**🚀 Core Features:**
- ✅ **Experience Memory Integration**: Learn from user interactions and outcomes
- ✅ **External Content Learning**: RSS feeds from trusted sources
- ✅ **Self-Reflection & Analysis**: Analyze own performance and decision-making
- ✅ **Pattern Recognition**: Identify recurring patterns and behaviors
- ✅ **Adaptive Intelligence**: Dynamic parameter adjustment and optimization
- ✅ **Performance Tracking**: Comprehensive metrics and learning curves

**🛠️ Tools & CLI:**
- ✅ **Evolutionary Learning CLI**: Complete management interface
- ✅ **Approval Management CLI**: Human-in-the-loop workflow management
- ✅ **Migration Scripts**: Automated data migration and validation
- ✅ **Assessment System**: Self-evaluation and knowledge validation
- ✅ **Emergency Controls**: Reset and rollback capabilities

**📊 Learning Metrics:**
- ✅ **Accuracy Tracking**: Response correctness and user satisfaction
- ✅ **Performance Monitoring**: Response time and efficiency
- ✅ **Knowledge Retention**: Long-term memory effectiveness
- ✅ **Adaptation Speed**: Learning rate and improvement tracking
- ✅ **Creativity & Consistency**: Innovation and reliability scores

**New Files & Modules:**
- `stillme_core/learning/evolutionary_learning_system.py` - Core evolutionary system
- `stillme_core/learning/learning_assessment_system.py` - Self-assessment engine
- `stillme_core/learning/approval_system.py` - Human-in-the-loop approval system
- `stillme_core/learning/approval_queue.py` - Approval workflow management
- `cli/evolutionary_learning.py` - Learning management CLI
- `cli/approval_manager.py` - Approval workflow CLI
- `config/approval.toml` - Approval system configuration
- `tests/test_unified_evolutionary_learning.py` - Comprehensive test suite
- `tests/test_approval_system.py` - Approval system test suite
- `docs/UNIFIED_LEARNING_SYSTEM_REPORT.md` - Implementation documentation

### 2025-09-26 - Daily Smart-Learning MVP Release

**Phase 0: Safety Hardening (Completed)**
- ✅ Health check script with comprehensive system validation
- ✅ Kill switch API/CLI with audit logging
- ✅ Rationale logging with standardized schema for careful mode
- ✅ Secrets/PII sweep with security gates

**Phase 1: Read-only Learning MVP (Completed)**
- ✅ RSS connectors with allowlist (arXiv, OpenAI, DeepMind)
- ✅ Content parser and normalizer
- ✅ License gate and risk injection scanning
- ✅ Quality scoring rubric and novelty detection
- ✅ Vector store and claims store ingestion
- ✅ Approval queue with human-in-the-loop
- ✅ Daily digest and metrics reporting
- ✅ CLI for scan/approve/ingest operations

**New Files & Modules:**
- `stillme_core/kill_switch.py` - Emergency stop mechanism
- `stillme_core/rationale_logging.py` - Decision logging
- `stillme_core/security/secrets_sweep.py` - Security scanning
- `scripts/health_check.py` - System health validation
- `cli/kill_switch.py` - Kill switch CLI
- `policies/learning_policy.yaml` - Learning safety policies

**CLI Commands:**
- `python -m cli.evolutionary_learning status` - Check learning status
- `python -m cli.evolutionary_learning train` - Run daily training
- `python cli/kill_switch.py --status` - Check kill switch
- `python scripts/health_check.py` - System health check

## License

MIT for the open core. Private plugin is distributed under a separate license.
