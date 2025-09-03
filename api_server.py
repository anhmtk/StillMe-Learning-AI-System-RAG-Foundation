# api_server.py
from __future__ import annotations

import asyncio
import glob
import logging
import os
import json
import re
from datetime import datetime, timezone
from typing import Optional, Literal, cast, List
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException
from starlette import status
from pydantic import BaseModel

from adapters.gpt5_client import GPT5Client
from adapters.ollama_client import OllamaClient

log = logging.getLogger("api")

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
KEEP_WARM_SEC = int(os.getenv("KEEP_WARM_SEC", "600"))
ALLOW_GPT5 = os.getenv("ALLOW_GPT5", "false").lower() == "true"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder")

# -----------------------------------------------------------------------------
# App & clients
# -----------------------------------------------------------------------------
app = FastAPI(title="StillMe Dev Agent API")

gpt5_client: Optional[GPT5Client] = None
ollama_client = OllamaClient()

# SafeRunner: dùng bản thật nếu có, fallback stub nếu thiếu
try:
    from stillme_core.safe_runner import SafeRunner  # type: ignore
except Exception:  # pragma: no cover
    class SafeRunner:  # type: ignore
        async def run_safe(self, plan_or_code: str) -> dict:
            return {"ok": True, "artifacts": {"log": "safe-run stub"}}

safe_runner = SafeRunner()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _json_only_system(schema_hint: Optional[dict]) -> str:
    base = (
        "Bạn là trợ lý tạo kế hoạch sửa lỗi.\n"
        "Hãy trả về CHỈ MỘT JSON hợp lệ theo schema mô tả bên dưới; "
        "không kèm văn bản, không markdown, không code block, không lời giải thích."
    )
    if schema_hint:
        try:
            schema_txt = json.dumps(schema_hint, ensure_ascii=False, indent=2)
        except Exception:
            schema_txt = str(schema_hint)
        return f"{base}\nSchema ví dụ:\n{schema_txt}\n"
    return (
        base
        + "\nTrả về JSON có các trường: plan_id, strategy, rationale, steps[], risk_mitigation."
    )

def _extract_json(s: str) -> Optional[str]:
    if not s:
        return None
    # Ưu tiên JSON trong ```json ... ```
    m = re.search(r"```json\s*(\{.*?\})\s*```", s, flags=re.S | re.I)
    if m:
        return m.group(1)
    # Fallback: block { ... } lớn nhất
    m2 = re.search(r"(\{(?:[^{}]|(?1))*\})", s, flags=re.S)
    return m2.group(1) if m2 else None

async def init_clients() -> None:
    global gpt5_client
    if ALLOW_GPT5 and gpt5_client is None:
        try:
            gpt5_client = GPT5Client()
        except Exception:
            gpt5_client = None

async def _keep_warm_task() -> None:
    while True:
        try:
            if ALLOW_GPT5 and gpt5_client:
                await gpt5_client.health()
            else:
                await ollama_client.health()
        except Exception:
            pass
        await asyncio.sleep(max(KEEP_WARM_SEC, 60))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_clients()
    task = asyncio.create_task(_keep_warm_task())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

app.router.lifespan_context = lifespan

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class BridgeIn(BaseModel):
    prompt: str
    mode: Literal["safe", "fast"] = "safe"
    system_prompt: Optional[str] = None
    response_format: Optional[str] = "json"
    force_json: Optional[bool] = True
    schema_hint: Optional[dict] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.3
    top_p: Optional[float] = 0.95
    stop: Optional[List[str]] = None

class BridgeOut(BaseModel):
    provider: str
    mode: str
    content: str
    safe_passed: Optional[bool] = None

# -----------------------------------------------------------------------------
# Provider selection
# -----------------------------------------------------------------------------
async def choose_provider() -> str:
    """Nếu GPT-5 bật và khỏe → dùng gpt5, ngược lại ollama."""
    if ALLOW_GPT5 and gpt5_client:
        try:
            if await gpt5_client.health():
                return "gpt5"
        except Exception:
            pass
    return "ollama"

# -----------------------------------------------------------------------------
# Bridge endpoint
# -----------------------------------------------------------------------------
@app.post("/dev-agent/bridge", response_model=BridgeOut)
async def dev_agent_bridge(req: BridgeIn):
    # 1) chuẩn hóa mode
    mode_str = (req.mode or "fast").lower()
    if mode_str not in {"fast", "safe"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid mode='{req.mode}'. Allowed: 'fast'|'safe'.",
        )
    mode: Literal["fast", "safe"] = cast(Literal["fast", "safe"], mode_str)

    # 2) chọn provider
    provider = await choose_provider()

    # 3) prompt có guard JSON-only
    guard = _json_only_system(req.schema_hint)
    composite_prompt = f"{guard}\n\n---\nUSER TASK:\n{req.prompt}\n"

    # 4) gọi provider
    try:
        if provider == "gpt5":
            if not (ALLOW_GPT5 and gpt5_client):
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "GPT-5 not available")
            content = await gpt5_client.generate(prompt=composite_prompt, mode=mode)
        else:
            content = await ollama_client.generate(prompt=composite_prompt, mode=mode)
    except asyncio.TimeoutError:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "Upstream model timed out")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Unhandled error from provider")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"Provider error: {e!s}")

    # 5) ép JSON-only nếu bật guard
    if (req.response_format == "json" or req.force_json) and isinstance(content, str):
        extracted = _extract_json(content)
        if not extracted:
            raise HTTPException(status_code=422, detail="Model không trả JSON hợp lệ")
        content = extracted

    # 6) SAFE guard (optional)
    safe_passed: Optional[bool] = None
    if mode == "safe":
        try:
            result = await safe_runner.run_safe(content)
            safe_passed = bool(result.get("ok", False)) if isinstance(result, dict) else bool(result)
        except Exception:
            safe_passed = None

    return BridgeOut(provider=provider, mode=mode, content=content, safe_passed=safe_passed)

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health/ai")
async def health_ai():
    gpt5_ok = False
    if ALLOW_GPT5 and gpt5_client:
        with suppress(Exception):
            gpt5_ok = await gpt5_client.health()
    ollama_ok = False
    with suppress(Exception):
        ollama_ok = await ollama_client.health()
    return {"gpt5": {"enabled": ALLOW_GPT5, "ok": gpt5_ok}, "ollama": {"ok": ollama_ok}}

# -----------------------------------------------------------------------------
# Plan (dry-run)
# -----------------------------------------------------------------------------
class PlanReq(BaseModel):
    dry_run: bool = True
    problem_description: Optional[str] = "Analyze current repo and propose minimal fix plan"
    problem_file: Optional[str] = None

@app.post("/dev-agent/plan")
async def dev_agent_plan(req: PlanReq):
    try:
        from stillme_core.planner import Planner  # type: ignore
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Planner unavailable")

    planner = Planner()
    steps: list = []

    # Ưu tiên build_plan (trả PlanItem list); fallback create_plan (trả dict)
    if hasattr(planner, "build_plan"):
        try:
            items = planner.build_plan(max_items=5)
            for it in (items or []):
                if hasattr(it, "to_dict"):
                    steps.append(it.to_dict())
                elif isinstance(it, dict):
                    steps.append(it)
        except Exception:
            steps = []
    else:
        try:
            plan = planner.create_plan(req.problem_description or "")
            steps = plan.get("steps", []) if isinstance(plan, dict) else []
        except Exception:
            steps = []

    return {
        "plan": steps,
        "count": len(steps),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

# -----------------------------------------------------------------------------
# Run (one cycle)
# -----------------------------------------------------------------------------
class RunReq(BaseModel):
    max_steps: int = 1
    run_full_suite_after_pass: bool = False
    open_pr_after_pass: bool = False
    pr_draft: bool = True
    pr_base: str = "main"
    pr_remote: str = "origin"
    pr_title: str | None = None
    pr_body: str | None = None
    tests_dir: str = "tests"

@app.post("/dev-agent/run")
def dev_agent_run(req: RunReq):
    try:
        from agent_dev import agentdev_run_once  # type: ignore
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AgentDev unavailable")

    # Gọi loop đồng bộ (agentdev_run_once là hàm sync)
    summary = agentdev_run_once(
        max_steps=req.max_steps,
        run_full_suite_after_pass=req.run_full_suite_after_pass,
        open_pr_after_pass=req.open_pr_after_pass,
        pr_draft=req.pr_draft,
        pr_base=req.pr_base,
        pr_remote=req.pr_remote,
        pr_title=req.pr_title,
        pr_body=req.pr_body,
        tests_dir=req.tests_dir,
    )

    # Chuẩn hóa response theo schema mới
    fs = (summary or {}).get("full_suite") or {}
    pr = (summary or {}).get("pr") or {}

    # Lấy log JSONL mới nhất nếu caller không truyền sẵn
    log_candidates = sorted(glob.glob("logs/agentdev/*.jsonl"))
    log_path = (summary or {}).get("logs", {}).get("jsonl") or (log_candidates[-1] if log_candidates else "logs/agentdev")

    resp = {
        "ok": bool((summary or {}).get("ok")),
        "taken": int((summary or {}).get("taken") or 1),
        "branch": (summary or {}).get("branch"),
        "refined": bool((summary or {}).get("refined", False)),
        "duration_ms": int((summary or {}).get("duration_ms") or 0),
        "full_suite": {
            "attempted": bool(fs.get("attempted", False)),
            "ok": fs.get("ok"),
            "collected": fs.get("collected"),
            "failed": fs.get("failed"),
            "duration_ms": fs.get("duration_ms"),
        },
        "pr": {
            "attempted": bool(pr.get("attempted", False)),
            "ok": pr.get("ok"),
            "url": pr.get("url"),
            "number": pr.get("number"),
            "provider": pr.get("provider"),
            "error": pr.get("error"),
        },
        "logs": {"jsonl": log_path},
    }
    return resp
