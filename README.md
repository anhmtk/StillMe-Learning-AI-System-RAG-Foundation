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

## Roadmap (short)

* Stabilize open-core interfaces
* Increase test coverage to ≥85% lines / ≥80% branches
* Expand open ethics/security runners (keep sensitive patterns private)
* Iterate on documentation with community help

## License

MIT for the open core. Private plugin is distributed under a separate license.
