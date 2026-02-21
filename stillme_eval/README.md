# StillMe Eval (Before vs After)

Reproducible evaluation toolkit for StillMe Lite.

## Files

- `prompts_v2.jsonl`: fixed prompt dataset (40 prompts, English, split by source-required in-kb vs out-of-kb)
- `run_eval.py`: batch inference runner (`before` or `after`)
- `metrics.py`: metric computation from JSONL outputs
- `generate_report.py`: summary table + optional report autofill
- `run_all.py`: one-command orchestration for full pipeline

## Quick Run

1. Start backend in **before** configuration (`ENABLE_VALIDATORS=false`), then run:

```bash
python stillme_eval/run_eval.py --mode before --api-base-url http://localhost:8000 --sleep-seconds 0.5 --max-retries-429 6
```

2. Start backend in **after** configuration (`ENABLE_VALIDATORS=true`), then run:

```bash
python stillme_eval/run_eval.py --mode after --api-base-url http://localhost:8000 --sleep-seconds 0.5 --max-retries-429 6
```

3. Generate metrics + auto-fill case study sample:

```bash
python stillme_eval/generate_report.py
```

## One-Command Batch

If you expose two URLs (or two env-configured deployments), run:

```bash
python stillme_eval/run_all.py --before-url <url_before> --after-url <url_after>
```

## Reliability Knobs

- `--sleep-seconds`: fixed delay between prompts (helps reduce rate limits)
- `--max-retries-429`: retry count for HTTP 429
- `--retry-base-seconds`: exponential backoff base (`1, 2, 4, 8...`)

## Isolation and Core Metrics

- Prompt isolation is enabled by default (unique `user_id` per prompt) to avoid cross-prompt context leakage.
- Use `--shared-user-id` only for debugging.
- Report now includes:
  - `request_failure_rate`
  - `refusal_recall_on_source_required`
  - `validator_only_refusal_rate_on_source_required`
  - `grounded_answer_rate_in_kb`
  - `false_refusal_rate_in_kb`
- CI/CD option:
  - `python stillme_eval/generate_report.py --strict-gate`
  - Exits with code `1` when `monitor -> warn` is `NO-GO`.

