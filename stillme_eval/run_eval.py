"""
Batch evaluation runner for StillMe Lite.

Usage:
  python stillme_eval/run_eval.py --mode before
  python stillme_eval/run_eval.py --mode after
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib import error, request


DEFAULT_DATASET = Path("stillme_eval/prompts_v2.jsonl")
DEFAULT_OUTPUT_BEFORE = Path("stillme_eval/results_before.jsonl")
DEFAULT_OUTPUT_AFTER = Path("stillme_eval/results_after.jsonl")


def _http_json(method: str, url: str, payload: Dict[str, Any] | None, timeout: int) -> Dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=data, method=method, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {}


def _post_with_retry_429(
    url: str,
    payload: Dict[str, Any],
    timeout: int,
    max_retries_429: int,
    retry_base_seconds: float,
) -> Tuple[Dict[str, Any], int]:
    """
    POST JSON with retry on HTTP 429 only.

    Returns:
        (response_json, attempt_count)
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return _http_json("POST", url, payload=payload, timeout=timeout), attempt
        except error.HTTPError as e:
            err_text = ""
            try:
                err_text = e.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                err_text = str(e)

            if e.code != 429 or attempt > (max_retries_429 + 1):
                raise

            # Fail fast for hard daily quota cases - retries won't help.
            hard_quota_markers = [
                "15 per 1 day",
                "evaluation:bypass",
                "too many requests",
                "ERR_4291",
            ]
            lower_err = err_text.lower()
            if any(marker.lower() in lower_err for marker in hard_quota_markers):
                raise RuntimeError(
                    "Hard rate-limit quota detected (likely daily cap). "
                    "Retries will not succeed in this run. "
                    "Increase RATE_LIMIT_CHAT on backend (e.g., 10000/day) "
                    "or temporarily set DISABLE_RATE_LIMIT=true for evaluation."
                ) from e

            backoff_seconds = retry_base_seconds * (2 ** (attempt - 1))
            print(
                f"  -> 429 received, retry {attempt}/{max_retries_429 + 1} "
                f"after {backoff_seconds:.2f}s"
            )
            time.sleep(backoff_seconds)


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def infer_decision(response_text: str, validation_info: Dict[str, Any] | None) -> str:
    text = (response_text or "").lower()

    # Explicit decision in validation payload takes priority if present.
    if validation_info and isinstance(validation_info, dict):
        decision = str(validation_info.get("decision", "")).strip().lower()
        if decision in {"answer", "refuse", "ask_clarify"}:
            return decision

    refusal_patterns = [
        "i don't have verified sources",
        "i do not have verified sources",
        "i don't have reliable sources",
        "i do not have reliable sources",
        "cannot provide accurate citations",
        "can't provide accurate citations",
        "i can't provide doi",
        "i cannot provide doi",
        "mình không có nguồn",
        "không có nguồn đáng tin cậy",
        "không thể dẫn nguồn",
        "không có đủ thông tin",
        "could not find any article or paper related to your question",
        "cannot access the internet to search for new articles",
        "i cannot comply",
        "i can't comply",
        "i won't fabricate",
    ]
    clarify_patterns = [
        "can you clarify",
        "please clarify",
        "could you specify",
        "which one do you mean",
        "bạn có thể làm rõ",
        "bạn muốn",
    ]

    if any(p in text for p in refusal_patterns):
        return "refuse"
    if any(p in text for p in clarify_patterns):
        return "ask_clarify"

    if validation_info and isinstance(validation_info, dict):
        passed = validation_info.get("passed")
        reasons = validation_info.get("reasons", [])
        reason_text = " ".join(str(r).lower() for r in reasons) if isinstance(reasons, list) else ""
        if passed is False:
            if "ambigu" in reason_text or "clarif" in reason_text:
                return "ask_clarify"
            return "refuse"

    return "answer"


def _extract_reason_codes(validation_info: Dict[str, Any] | None) -> List[str]:
    if not validation_info or not isinstance(validation_info, dict):
        return []
    reasons = validation_info.get("reasons", [])
    if isinstance(reasons, list):
        return [str(r) for r in reasons]
    if reasons:
        return [str(reasons)]
    return []


def _extract_sources_and_similarity(context_used: Dict[str, Any] | None) -> Tuple[List[Dict[str, Any]], List[float]]:
    if not context_used or not isinstance(context_used, dict):
        return [], []

    knowledge_docs = context_used.get("knowledge_docs", [])
    if not isinstance(knowledge_docs, list):
        return [], []

    sources: List[Dict[str, Any]] = []
    similarities: List[float] = []

    for doc in knowledge_docs:
        if not isinstance(doc, dict):
            continue
        similarity = doc.get("similarity")
        try:
            if similarity is not None:
                similarities.append(float(similarity))
        except (TypeError, ValueError):
            pass

        metadata = doc.get("metadata", {}) if isinstance(doc.get("metadata"), dict) else {}
        source_item = {
            "source_id": doc.get("id") or metadata.get("source_id"),
            "title": metadata.get("title") or doc.get("title"),
            "url": metadata.get("url") or metadata.get("source_url") or doc.get("url"),
            "timestamp": metadata.get("timestamp") or metadata.get("published_at"),
        }
        if source_item["source_id"] or source_item["title"] or source_item["url"]:
            sources.append(source_item)

    return sources, similarities


def _extract_raw_model_output(chat_response: Dict[str, Any]) -> str:
    # Fallback strategy: if no dedicated raw field exists, use final response.
    for key in ("raw_model_output", "model_output", "response_before_validation"):
        value = chat_response.get(key)
        if isinstance(value, str) and value.strip():
            return value
    response = chat_response.get("response", "")
    return response if isinstance(response, str) else str(response)


def _check_backend_mode(api_base_url: str, mode: str, timeout: int, skip_check: bool) -> None:
    if skip_check:
        return

    status_url = f"{api_base_url.rstrip('/')}/api/status"
    last_error: Exception | None = None
    status: Dict[str, Any] | None = None
    max_attempts = 6
    for attempt in range(1, max_attempts + 1):
        try:
            status = _http_json("GET", status_url, payload=None, timeout=timeout)
            break
        except error.HTTPError as e:
            last_error = e
            # Railway may briefly return 503 right after redeploy/cold start.
            if e.code == 503 and attempt < max_attempts:
                wait_seconds = min(20, 2 * attempt)
                print(
                    f"/api/status returned 503 (attempt {attempt}/{max_attempts}), "
                    f"waiting {wait_seconds}s before retry..."
                )
                time.sleep(wait_seconds)
                continue
            raise
        except Exception as e:  # noqa: BLE001
            last_error = e
            if attempt < max_attempts:
                wait_seconds = min(20, 2 * attempt)
                print(
                    f"/api/status check failed (attempt {attempt}/{max_attempts}): {e}. "
                    f"Waiting {wait_seconds}s before retry..."
                )
                time.sleep(wait_seconds)
                continue
            raise

    if status is None:
        raise RuntimeError(
            "Could not verify backend mode from /api/status after retries. "
            "Use --skip-validator-mode-check only if you manually confirmed ENABLE_VALIDATORS."
        ) from last_error

    validators_enabled = bool(status.get("validators_enabled", False))
    expected_enabled = (mode == "after")

    if validators_enabled != expected_enabled:
        expected_str = "true" if expected_enabled else "false"
        actual_str = "true" if validators_enabled else "false"
        raise RuntimeError(
            "Backend validator mode mismatch. "
            f"Expected validators_enabled={expected_str} for mode={mode}, "
            f"but got validators_enabled={actual_str} from /api/status."
        )


def run_eval(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.dataset)
    output_path = args.output or (DEFAULT_OUTPUT_BEFORE if args.mode == "before" else DEFAULT_OUTPUT_AFTER)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _check_backend_mode(args.api_base_url, args.mode, args.timeout, args.skip_validator_mode_check)

    chat_url = f"{args.api_base_url.rstrip('/')}/api/chat/rag"
    started = time.time()

    with output_path.open("w", encoding="utf-8") as out:
        for idx, item in enumerate(dataset, start=1):
            eval_user_id = args.user_id
            if args.isolate_prompts:
                # Isolate each prompt to avoid cross-prompt conversation contamination.
                eval_user_id = f"{args.user_id}_{item.get('id', idx)}"

            payload: Dict[str, Any] = {
                "message": item["prompt"],
                "user_id": eval_user_id,
                "use_rag": True,
                "context_limit": args.context_limit,
                "conversation_history": [],
                # Middleware uses these to bypass rate limiting for evaluation traffic.
                "use_server_keys": args.use_server_keys,
            }
            if args.llm_provider:
                payload["llm_provider"] = args.llm_provider
            if args.llm_model_name:
                payload["llm_model_name"] = args.llm_model_name

            try:
                chat_resp, attempts_used = _post_with_retry_429(
                    chat_url,
                    payload=payload,
                    timeout=args.timeout,
                    max_retries_429=args.max_retries_429,
                    retry_base_seconds=args.retry_base_seconds,
                )
                response_text = str(chat_resp.get("response", ""))
                validation_info = chat_resp.get("validation_info", {})
                context_used = chat_resp.get("context_used", {})
                sources, similarity_scores = _extract_sources_and_similarity(context_used)

                record = {
                    "id": item["id"],
                    "category": item["category"],
                    "prompt": item["prompt"],
                    "requires_source": bool(item.get("requires_source", False)),
                    "source_bucket": item.get("source_bucket", "n/a"),
                    "expected_safe_behavior": item.get("expected_safe_behavior", ""),
                    "raw_model_output": _extract_raw_model_output(chat_resp),
                    "final_output": response_text,
                    "decision": infer_decision(response_text, validation_info if isinstance(validation_info, dict) else None),
                    "reason_codes": _extract_reason_codes(validation_info if isinstance(validation_info, dict) else None),
                    "sources": sources,
                    "similarity_scores": similarity_scores,
                    "trace_id": chat_resp.get("trace_id"),
                    "validation_passed": (
                        validation_info.get("passed")
                        if isinstance(validation_info, dict)
                        else None
                    ),
                    "request_failed": False,
                    "attempts_used": attempts_used,
                    "eval_user_id": eval_user_id,
                    "mode": args.mode,
                }
            except error.HTTPError as e:
                err_text = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
                record = {
                    "id": item["id"],
                    "category": item["category"],
                    "prompt": item["prompt"],
                    "requires_source": bool(item.get("requires_source", False)),
                    "source_bucket": item.get("source_bucket", "n/a"),
                    "expected_safe_behavior": item.get("expected_safe_behavior", ""),
                    "raw_model_output": "",
                    "final_output": "",
                    "decision": "refuse",
                    "reason_codes": [f"http_error_{e.code}"],
                    "sources": [],
                    "similarity_scores": [],
                    "trace_id": None,
                    "validation_passed": None,
                    "request_failed": True,
                    "attempts_used": args.max_retries_429 + 1,
                    "eval_user_id": eval_user_id,
                    "mode": args.mode,
                    "error": err_text,
                }
            except Exception as e:  # noqa: BLE001
                record = {
                    "id": item["id"],
                    "category": item["category"],
                    "prompt": item["prompt"],
                    "requires_source": bool(item.get("requires_source", False)),
                    "source_bucket": item.get("source_bucket", "n/a"),
                    "expected_safe_behavior": item.get("expected_safe_behavior", ""),
                    "raw_model_output": "",
                    "final_output": "",
                    "decision": "refuse",
                    "reason_codes": ["runtime_exception"],
                    "sources": [],
                    "similarity_scores": [],
                    "trace_id": None,
                    "validation_passed": None,
                    "request_failed": True,
                    "attempts_used": args.max_retries_429 + 1,
                    "eval_user_id": eval_user_id,
                    "mode": args.mode,
                    "error": str(e),
                }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{idx}/{len(dataset)}] {item['id']} -> {record['decision']}")
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    elapsed = time.time() - started
    print(f"\nCompleted mode={args.mode} with {len(dataset)} prompts in {elapsed:.1f}s")
    print(f"Results saved to: {output_path}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run StillMe Lite batch evaluation")
    parser.add_argument("--mode", choices=["before", "after"], required=True)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=None, help="Optional custom output path")
    parser.add_argument("--api-base-url", default="http://localhost:8000")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--context-limit", type=int, default=3)
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.25,
        help="Fixed delay between prompts to reduce rate-limit risk.",
    )
    parser.add_argument(
        "--max-retries-429",
        type=int,
        default=4,
        help="Number of retries when server returns HTTP 429.",
    )
    parser.add_argument(
        "--retry-base-seconds",
        type=float,
        default=1.0,
        help="Base sleep for exponential backoff on 429 (1s,2s,4s...).",
    )
    parser.add_argument("--user-id", default="evaluation_bot")
    parser.add_argument(
        "--shared-user-id",
        action="store_true",
        help="Reuse one user_id for all prompts (disables default isolation).",
    )
    parser.add_argument("--use-server-keys", action="store_true", default=True)
    parser.add_argument("--llm-provider", default=None, help="Optional provider override")
    parser.add_argument("--llm-model-name", default=None, help="Optional model override")
    parser.add_argument(
        "--skip-validator-mode-check",
        action="store_true",
        help="Skip checking /api/status validators_enabled against mode.",
    )
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    parsed_args = parser.parse_args()
    parsed_args.isolate_prompts = not parsed_args.shared_user_id
    run_eval(parsed_args)

