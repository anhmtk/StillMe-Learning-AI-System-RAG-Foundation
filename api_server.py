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

# Import AgentController for testing
try:
    from stillme_core.controller import AgentController
except ImportError:
    AgentController = None

# Import SUL
try:
    from stillme_core.sul import get_sul
except ImportError:
    get_sul = None

# Import Supervisor
try:
    from stillme_core.supervisor import get_supervisor
except ImportError:
    get_supervisor = None

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
@app.post("/dev-agent/bridge")
async def dev_agent_bridge(req: BridgeIn):
    """AgentDev bridge endpoint - runs AgentDev orchestration"""
    if AgentController is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AgentDev unavailable: AgentController not found")
    
    # Run AgentDev with the prompt as goal
    try:
        controller = AgentController()
        result = controller.run_agent(goal=req.prompt, max_steps=3)
        
        # Extract key information
        summary = result.get("summary", "AgentDev completed")
        pass_rate = result.get("pass_rate", 0.0)
        steps_tail = result.get("steps", [])[-2:] if result.get("steps") else []  # Last 2 steps
        
        return {
            "summary": summary,
            "pass_rate": pass_rate,
            "steps_tail": steps_tail,
            "total_steps": result.get("total_steps", 0),
            "passed_steps": result.get("passed_steps", 0),
            "duration_s": result.get("total_duration_s", 0.0),
            "goal": result.get("goal", req.prompt)
        }
    except Exception as e:
        log.exception("AgentDev execution failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"AgentDev execution failed: {e}")

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health/ai")
async def health_ai():
    """Health check for AI services and AgentDev components"""
    gpt5_ok = False
    if ALLOW_GPT5 and gpt5_client:
        with suppress(Exception):
            gpt5_ok = await gpt5_client.health()
    ollama_ok = False
    with suppress(Exception):
        ollama_ok = await ollama_client.health()
    
    # Test AgentDev components
    agentdev_ok = False
    try:
        from stillme_core.controller import AgentController
        from stillme_core.planner import Planner
        from stillme_core.executor import PatchExecutor
        from stillme_core.verifier import Verifier
        
        # Quick component test
        controller = AgentController()
        agentdev_ok = True
    except Exception as e:
        log.warning(f"AgentDev components check failed: {e}")
    
    return {
        "ok": True,
        "details": {
            "gpt5": {"enabled": ALLOW_GPT5, "ok": gpt5_ok}, 
            "ollama": {"ok": ollama_ok},
            "agentdev": {"ok": agentdev_ok}
        }
    }

# -----------------------------------------------------------------------------
# SUL (System Understanding Layer)
# -----------------------------------------------------------------------------
@app.get("/sul/depends/on")
async def sul_depends_on(module: str):
    """Get dependencies and risk score for a module"""
    if get_sul is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SUL not available")
    
    try:
        sul = get_sul()
        result = sul.get_dependencies(module)
        return result
    except Exception as e:
        log.exception("SUL analysis failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"SUL analysis failed: {e}")

@app.get("/sul/where/is")
async def sul_where_is(symbol: str):
    """Find where a symbol is defined and used"""
    if get_sul is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SUL not available")
    
    try:
        sul = get_sul()
        result = sul.find_symbol(symbol)
        return result
    except Exception as e:
        log.exception("SUL symbol search failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"SUL symbol search failed: {e}")

# -----------------------------------------------------------------------------
# Supervisor
# -----------------------------------------------------------------------------
@app.post("/supervisor/run")
async def supervisor_run():
    """Run daily supervisor to collect signals and propose lessons"""
    if get_supervisor is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Supervisor not available")
    
    try:
        supervisor = get_supervisor()
        signals = supervisor.collect_signals()
        proposals = supervisor.propose_lessons(signals)
        proposals_file = supervisor.save_lesson_proposals(proposals)
        
        return {
            "ok": True,
            "signals_collected": len(signals.get("agentdev_logs", [])),
            "proposals_generated": len(proposals),
            "proposals_file": proposals_file,
            "proposals": [{"id": p.id, "title": p.title} for p in proposals]
        }
    except Exception as e:
        log.exception("Supervisor run failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Supervisor run failed: {e}")

@app.post("/supervisor/approve")
async def supervisor_approve(proposal_ids: List[str]):
    """Approve lesson proposals and create knowledge pack"""
    if get_supervisor is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Supervisor not available")
    
    try:
        supervisor = get_supervisor()
        knowledge_pack = supervisor.approve_lessons(proposal_ids)
        
        return {
            "ok": True,
            "knowledge_pack_id": knowledge_pack.id,
            "version": knowledge_pack.version,
            "lessons_count": len(knowledge_pack.lessons),
            "summary": knowledge_pack.summary
        }
    except Exception as e:
        log.exception("Supervisor approve failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Supervisor approve failed: {e}")

@app.get("/knowledge/current")
async def knowledge_current():
    """Get current knowledge pack"""
    if get_supervisor is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Supervisor not available")
    
    try:
        supervisor = get_supervisor()
        knowledge_pack = supervisor.get_latest_knowledge_pack()
        
        if knowledge_pack is None:
            return {"ok": True, "knowledge_pack": None}
        
        return {
            "ok": True,
            "knowledge_pack": {
                "id": knowledge_pack.id,
                "version": knowledge_pack.version,
                "created_at": knowledge_pack.created_at,
                "lessons_count": len(knowledge_pack.lessons),
                "summary": knowledge_pack.summary,
                "lessons": [{"id": l.id, "title": l.title} for l in knowledge_pack.lessons]
            }
        }
    except Exception as e:
        log.exception("Knowledge current failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Knowledge current failed: {e}")

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
