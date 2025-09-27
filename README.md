# 🌟 StillMe AI — Safe & Transparent AI Framework (Open-Core)

[![Tests](https://github.com/OWNER/REPO/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci-tests.yml)
[![Security](https://github.com/OWNER/REPO/actions/workflows/security-ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/security-ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-target%2085%25-lightgrey)](artifacts/coverage.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**StillMe** focuses on **Ethics · Security · Transparency**.  
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

## Daily Smart-Learning (MVP)

StillMe now includes a **safe daily smart-learning pipeline** that allows the AI to discover, evaluate, and learn from high-quality content while maintaining strict safety controls.

### How It Works

1. **Discovery**: Scans trusted sources (arXiv, OpenAI, DeepMind) for new content
2. **Scoring**: Evaluates content quality, relevance, and novelty using rubric-based scoring
3. **Approval**: Human-in-the-loop approval system for all content ingestion
4. **Ingestion**: Stores content in vector store and extracts structured claims
5. **Reporting**: Generates daily digest reports with metrics and recommendations

### Safety & Policy

- **Read-only learning**: No fine-tuning in MVP - only knowledge base updates
- **License compliance**: Only CC-BY, Apache, MIT, and other permissive licenses
- **Risk scanning**: Detects prompt injection, PII, and security risks
- **Human approval**: All content requires explicit human approval before ingestion
- **Citations required**: All responses based on ingested content must include citations

### Quick Start

```bash
# Scan content from all sources
python -m stillme_core.learning.pipeline --scan

# Check approval queue status
python -m stillme_core.learning.pipeline --status

# Approve an item for ingestion
python -m stillme_core.learning.pipeline --approve <item_id>

# Reject an item
python -m stillme_core.learning.pipeline --reject <item_id> --reason "Low quality"
```

### Learning Policy

The system follows strict policies defined in `policies/learning_policy.yaml`:
- **Allowlist domains**: Only arxiv.org, openai.com, deepmind.com
- **Quality threshold**: Minimum 0.72 quality score
- **Risk threshold**: Maximum 0.25 risk score
- **Daily limits**: Max 5 recommendations, 3 ingestions per day
- **No fine-tuning**: Read-only learning only

## Roadmap (short)

* ✅ **Phase 0**: Safety hardening (kill switch, rationale logging, secrets sweep)
* ✅ **Phase 1**: Read-only learning MVP (discovery → scoring → approval → ingest)
* 🔄 **Phase 2**: Skill template extraction and procedural learning
* 🔄 **Phase 3**: Self-quiz, consistency checking, and unlearning
* 🔄 **Phase 4**: Controlled adaptation with LoRA fine-tuning
* Increase test coverage to ≥85% lines / ≥80% branches
* Expand open ethics/security runners (keep sensitive patterns private)
* Iterate on documentation with community help

## Changelog

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
- `stillme_core/learning/` - Complete learning pipeline
- `stillme_core/kill_switch.py` - Emergency stop mechanism
- `stillme_core/rationale_logging.py` - Decision logging
- `stillme_core/security/secrets_sweep.py` - Security scanning
- `scripts/health_check.py` - System health validation
- `cli/kill_switch.py` - Kill switch CLI
- `policies/learning_policy.yaml` - Learning safety policies

**CLI Commands:**
- `python -m stillme_core.learning.pipeline --scan` - Scan content
- `python -m stillme_core.learning.pipeline --status` - Check queue
- `python -m stillme_core.learning.pipeline --approve <id>` - Approve item
- `python cli/kill_switch.py --status` - Check kill switch
- `python scripts/health_check.py` - System health check

## License

MIT for the open core. Private plugin is distributed under a separate license.
