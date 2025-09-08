# NOTE: AI Reminder: framework.py is sacred. Only modify if 100% sure.
import os
import subprocess
import shutil
import git
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from jsonschema import validate, ValidationError
import sys
import asyncio
from dotenv import load_dotenv

# Ensure local modules path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules")))

# Core components
from stillme_ethical_core.ethics_checker import EthicsChecker
from stillme_core.planner import Planner
from stillme_core.git_manager import GitManager
from stillme_core.sandbox_manager import DockerSandboxManager

# --- Bridge: AgentDev -> API server (/dev-agent/bridge)
try:
    from stillme_core.agent_dev_bridge import DevAgentBridge as _RealDevAgentBridge  # type: ignore
    DevAgentBridge = _RealDevAgentBridge  # type: ignore[assignment]
except Exception:
    class _DevAgentBridgeStub:
        def __init__(self, *args, **kwargs):
            pass
        async def ask(self, *args, **kwargs):
            raise RuntimeError("DevAgentBridge unavailable. Ensure stillme_core/agent_dev_bridge.py exists.")
    DevAgentBridge = _DevAgentBridgeStub  # type: ignore[assignment]


# Backup framework.py before run
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = Path("backup")
backup_dir.mkdir(exist_ok=True)
if Path("framework.py").exists():
    shutil.copy("framework.py", backup_dir / f"framework_backup_{timestamp}.py")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AgentDev-SafeMode")

# Self-reflection logger
reflection_log_path = Path("agent_logs")
reflection_log_path.mkdir(exist_ok=True)
def log_reflection(data: dict):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(reflection_log_path / "self_reflection.log", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {json.dumps(data, ensure_ascii=False)}\n")

# Load env
load_dotenv()

# Env vars
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 3))
ETHICS_CHECK_LEVEL = os.getenv("ETHICS_CHECK_LEVEL", "high")

# AI Plan schema
AI_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string"},
        "fix_strategy_summary": {"type": "string"},
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "modify_code", "run_pylint", "add_test", "run_tests",
                            "review_diff", "check_imports", "install_deps", "resolve_conflict"
                        ]
                    },
                    "file": {"type": "string", "pattern": "^(modules/|tests/|framework.py|requirements.txt)"},
                    "description": {"type": "string"},
                    "code_to_apply": {"type": "string", "nullable": True}
                },
                "required": ["action", "description"]
            }
        }
    },
    "required": ["root_cause", "fix_strategy_summary", "plan"]
}

# Add missing method to EthicsChecker if not exists
if not hasattr(EthicsChecker, "assess_framework_safety"):
    def _assess_framework_safety_stub(self, old_code: str, new_code: str) -> bool:
        # very light safeguard example; customize later
        danger = ("subprocess.run(  # SECURITY: Replaced with safe alternative" in new_code) or ("subprocess.Popen(" in new_code)
        return not danger
    setattr(EthicsChecker, "assess_framework_safety", _assess_framework_safety_stub)

class AgentDev:
    def __init__(self, problem_description: str, problem_file: str):
        self.problem_description = problem_description
        self.problem_file = problem_file

        self.planner = Planner()
        if not hasattr(self.planner, "plan"):
            raise AttributeError("Planner object is missing 'plan()' method.")

        self.git_manager = GitManager()
        self.ethics_checker = EthicsChecker(level=ETHICS_CHECK_LEVEL)
        self.sandbox = DockerSandboxManager()
        self.current_attempt = 0
        self.max_attempts = MAX_ATTEMPTS
        self.previous_plan_feedback = ""
        self.initial_branch = self.git_manager.get_current_branch()
        self.fix_branch_name = f"agent-fix-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.bridge = DevAgentBridge()

    # ---------- File helpers (work with/without sandbox methods) ----------
    def _read_file(self, path: str) -> str:
        try:
            if hasattr(self.sandbox, "read_file_content"):
                return self.sandbox.read_file_content(path)  # type: ignore[attr-defined]
        except Exception:
            pass
        p = Path(path)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def _write_file(self, path: str, content: str) -> bool:
        try:
            if hasattr(self.sandbox, "write_file_content"):
                ok = self.sandbox.write_file_content(path, content)  # type: ignore[attr-defined]
                return bool(ok)
        except Exception:
            pass
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return True

    # --------------------- Bridge planning (FAST) --------------------------
    def _build_plan_prompt(self, problem_description: str, problem_file: str, current_attempt: int, previous_feedback: str) -> str:
        schema_str = json.dumps(AI_PLAN_SCHEMA, ensure_ascii=False)
        return f"""
You are StillMe Dev Agent. Generate a FIX PLAN as strict JSON (no markdown, no backticks).
Problem file: {problem_file}
Attempt: {current_attempt}

Problem description (raw):
{problem_description.strip()}

Previous feedback (if any):
{previous_feedback.strip()}

Constraints:
- Follow EXACTLY this JSON Schema (keys & types). Do not add extra keys.
- 'file' must match ^(modules/|tests/|framework.py|requirements.txt)
- 'action' ∈ ["modify_code","run_pylint","add_test","run_tests","review_diff","check_imports","install_deps","resolve_conflict"]
- Keep 'code_to_apply' minimal and self-contained (only when needed).
- Output: JSON ONLY, no explanation.

JSON_SCHEMA:
{schema_str}
""".strip()

    async def _bridge_fast_async(self, prompt: str) -> Dict[str, Any]:
        return await self.bridge.ask(prompt=prompt, mode="fast", provider="auto")

    async def _bridge_safe_async(self, prompt: str) -> Dict[str, Any]:
        return await self.bridge.ask(prompt=prompt, mode="safe", provider="auto")

    def _plan_with_bridge(self, problem_description: str, problem_file: str, current_attempt: int, previous_feedback: str) -> Optional[Dict[str, Any]]:
        prompt = self._build_plan_prompt(problem_description, problem_file, current_attempt, previous_feedback)
        try:
            res = asyncio.run(self.bridge.ask(prompt=prompt, mode="fast", provider="ollama"))

        except Exception as e:
            logger.warning(f"Bridge FAST call failed: {e}")
            return None

        text = (res.get("content") or "").strip()
        # unwrap ```json ... ```
        if text.startswith("```"):
            if text.lower().startswith("```json"):
                text = text[7:].strip("`").strip()
            else:
                text = text.strip("`").strip()

        try:
            data = json.loads(text)
            validate(instance=data, schema=AI_PLAN_SCHEMA)
            logger.info("Plan via Bridge (FAST) → JSON schema VALID.")
            return data
        except Exception as e:
            logger.warning(f"Plan via Bridge INVALID JSON/schema: {e}. Raw: {text[:400]}...")
            self.previous_plan_feedback = f"Your last plan was invalid JSON or schema. Error: {e}. Return strict JSON only."
            return None

    # ------------------------ Local actions -------------------------------
    def _run_tests(self) -> Dict[str, Any]:
        logger.info("Running tests...")
        result = self.sandbox.run_command(["python", "-m", "pytest", "tests/"])
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}

    def _run_pylint(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"Running Pylint on {file_path}...")
        result = self.sandbox.run_command(["pylint", file_path])
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}

    def _apply_code_changes(self, file_path: str, code_to_apply: str) -> bool:
        old_code = self._read_file(file_path)

        if file_path == "framework.py":
            removed_lines = [ln for ln in old_code.splitlines() if ln.strip() and ln.strip() not in code_to_apply]
            if len(removed_lines) > 50:
                logger.warning("⚠️ Attempt to remove too many lines from framework.py. Aborting patch.")
                log_reflection({"file": file_path, "reason": "too_many_lines_removed"})
                return False
            ok = True
            if hasattr(self.ethics_checker, "assess_framework_safety"):
                try:
                    ok = bool(getattr(self.ethics_checker, "assess_framework_safety")(old_code, code_to_apply))  # type: ignore[misc]
                except Exception:
                    ok = True
            if not ok:
                logger.warning("❌ New code would weaken framework.py. Change blocked.")
                log_reflection({"file": file_path, "reason": "ethics_fail"})
                return False

        logger.info(f"Applying code changes to {file_path}...")
        success = self._write_file(file_path, code_to_apply)
        if success:
            logger.info(f"Successfully wrote changes to {file_path}.")
            return True
        else:
            logger.error(f"Failed to write changes to {file_path}.")
            return False

    def _review_diff(self) -> Dict[str, Any]:
        logger.info("Reviewing diff...")
        result = self.sandbox.run_command(["git", "diff"])
        if result.returncode == 0:
            logger.info("Diff content:\n" + result.stdout)
            return {"success": True, "diff": result.stdout}
        else:
            logger.error(f"Failed to get diff: {result.stderr}")
            return {"success": False, "error": result.stderr}

    def _check_imports(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"Checking imports in {file_path}...")
        result = self.sandbox.run_command([
            "python", "-c",
            f"import ast; f='{file_path}'; import sys; print('Syntax OK') if ast.parse(open(f,'r',encoding='utf-8').read()) is not None else sys.exit(1)"
        ])
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}

    def _install_deps(self) -> Dict[str, Any]:
        logger.info("Installing dependencies from requirements.txt...")
        result = self.sandbox.run_command(["pip", "install", "-r", "requirements.txt"])
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}

    def _resolve_conflict(self, file_path: str, code_to_apply: Optional[str]) -> bool:
        logger.info(f"Attempting to resolve conflict for {file_path}...")
        if code_to_apply:
            logger.info(f"Applying specific code to resolve conflict in {file_path}...")
            return self._apply_code_changes(file_path, code_to_apply)
        else:
            logger.warning("resolve_conflict action requires file and code_to_apply or more explicit handling.")
            return False

    # --------------------------- Main loop -------------------------------
    def run(self):
        logger.info(f"AgentDev started for problem: '{self.problem_description}' in file: '{self.problem_file}'")

        # 1) Git branch
        self.git_manager.create_and_checkout_branch(self.fix_branch_name)

        # 2) Start Docker sandbox
        if not self.sandbox.start_container():
            logger.critical("Failed to start Docker sandbox. Aborting.")
            self.git_manager.revert_uncommitted_changes()
            return

        try:
            # 3) Attempts loop
            while self.current_attempt < self.max_attempts:
                self.current_attempt += 1
                logger.info(f"--- Attempt {self.current_attempt} to fix the issue ---")

                # Plan via bridge first; fallback to local planner
                plan_json = self._plan_with_bridge(
                    problem_description=self.problem_description,
                    problem_file=self.problem_file,
                    current_attempt=self.current_attempt,
                    previous_feedback=self.previous_plan_feedback or ""
                )

                if plan_json is None:
                    logger.info("Bridge planning failed or invalid. Falling back to Planner.plan()...")
                    plan_json = self.planner.plan(
                        problem_description=self.problem_description,
                        problem_file=self.problem_file,
                        current_attempt=self.current_attempt,
                        previous_plan_feedback=self.previous_plan_feedback
                    )

                if plan_json is None:
                    logger.error("Planning failed: invalid JSON plan. Retrying with feedback.")
                    self.previous_plan_feedback = "AI did not provide a valid JSON plan. Please adhere strictly to the AI_PLAN_SCHEMA."
                    continue

                # Ethics check
                if not self.ethics_checker.check_plan(plan_json):
                    logger.warning("Ethics check failed for the generated plan. Retrying with feedback.")
                    self.previous_plan_feedback = "The previous plan failed ethics check. Please provide an ethical solution."
                    continue

                # Execute steps
                all_steps_successful = True
                test_passed_after_fix = False

                for step in plan_json.get("plan", []):
                    action = step.get("action")
                    file_path = step.get("file")
                    description = step.get("description")
                    code_to_apply = step.get("code_to_apply")

                    logger.info(f"Executing step: [{action}] - {description}")
                    step_success = False
                    action_result = {"success": False, "message": "Action not executed or failed"}

                    if action == "modify_code":
                        if file_path and code_to_apply is not None:
                            step_success = self._apply_code_changes(file_path, code_to_apply)
                            action_result = {"success": step_success, "message": f"Modified {file_path}"}
                        else:
                            logger.error("Missing file_path or code_to_apply for modify_code action.")
                    elif action == "add_test":
                        if file_path and code_to_apply is not None:
                            step_success = self._apply_code_changes(file_path, code_to_apply)
                            action_result = {"success": step_success, "message": f"Added test to {file_path}"}
                        else:
                            logger.error("Missing file_path or code_to_apply for add_test action.")
                    elif action == "run_tests":
                        test_result = self._run_tests()
                        step_success = test_result["success"]
                        action_result = {"success": step_success, "stdout": test_result["stdout"], "stderr": test_result["stderr"]}
                        if step_success:
                            logger.info("Tests passed!")
                            test_passed_after_fix = True
                        else:
                            logger.warning("Tests failed!")
                            self.previous_plan_feedback = f"Tests failed after step: {description}\nStdout: {test_result['stdout']}\nStderr: {test_result['stderr']}"
                    elif action == "run_pylint":
                        if file_path:
                            pylint_result = self._run_pylint(file_path)
                            step_success = pylint_result["success"]
                            action_result = {"success": step_success, "stdout": pylint_result["stdout"], "stderr": pylint_result["stderr"]}
                            if not step_success:
                                logger.warning(f"Pylint issues found in {file_path}:\n{pylint_result['stdout']}{pylint_result['stderr']}")
                        else:
                            logger.error("Missing file_path for run_pylint action.")
                    elif action == "review_diff":
                        diff_result = self._review_diff()
                        step_success = diff_result["success"]
                        action_result = {"success": step_success, "diff": diff_result.get("diff", "")}
                    elif action == "check_imports":
                        if file_path:
                            import_check_result = self._check_imports(file_path)
                            step_success = import_check_result["success"]
                            action_result = {"success": step_success, "stdout": import_check_result["stdout"], "stderr": import_check_result["stderr"]}
                        else:
                            logger.error("Missing file_path for check_imports action.")
                    elif action == "install_deps":
                        deps_result = self._install_deps()
                        step_success = deps_result["success"]
                        action_result = {"success": step_success, "stdout": deps_result["stdout"], "stderr": deps_result["stderr"]}
                    elif action == "resolve_conflict":
                        if file_path and code_to_apply is not None:
                            step_success = self._resolve_conflict(file_path, code_to_apply)
                        else:
                            logger.warning("resolve_conflict action requires file and code_to_apply or more explicit handling.")
                            step_success = False
                    else:
                        logger.warning(f"Unknown action: {action}. Skipping.")
                        continue

                    if not step_success:
                        all_steps_successful = False
                        logger.error(f"Step '{action}' failed. Reason: {action_result.get('stderr') or action_result.get('message', 'Unknown error')}")
                        self.previous_plan_feedback = f"Previous step '{action}' failed: {description}. Result: {action_result}. Please re-evaluate your plan."
                        break

                if all_steps_successful and test_passed_after_fix:
                    logger.info("Issue successfully fixed and all tests passed!")
                    self.git_manager.commit_changes(f"Fix: {plan_json['fix_strategy_summary']}")
                    return

            logger.error(f"Agent failed to fix the issue after {self.max_attempts} attempts. Manual intervention required.")
            logger.info(f"Last known error: {self.previous_plan_feedback or 'AI failed to provide a valid plan conforming to schema.'}")

        except Exception as e:
            logger.critical(f"An unhandled error occurred during AgentDev execution: {e}", exc_info=True)
        finally:
            logger.info("Keeping agent branch for debugging.")
            self.sandbox.stop_container()
            logger.info("AgentDev process finished.")

# -------------------------- Demo main -----------------------------------
if __name__ == "__main__":
    # prepare demo faulty module
    Path("modules").mkdir(exist_ok=True)
    example_module_content_error = """
def some_function_in_module():
    return 10 / 0
"""
    with open("modules/example_module.py", "w", encoding="utf-8") as f:
        f.write(example_module_content_error)

    os.makedirs("tests", exist_ok=True)
    with open("tests/test_example_module.py", "w", encoding="utf-8") as f:
        f.write("# Initial test file for example_module\n")

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("pytest\npylint\nopenai\nollama\ncryptography\njsonschema\ngitpython\nhttpx\n")

    problem_description = """
Traceback (most recent call last):
  File "framework.py", line 5, in <module>
    result = some_function_in_module()
  File "modules/example_module.py", line 2, in some_function_in_module
    return 10 / 0
ZeroDivisionError: division by zero
"""
    problem_file = "modules/example_module.py"

    agent = AgentDev(problem_description, problem_file)
    agent.run()

# =====================
# AgentDev one-shot loop
# =====================
from typing import Optional
from pathlib import Path as _Path
import datetime as _dt
from stillme_core.plan_types import PlanItem as _PlanItem
from stillme_core.executor import PatchExecutor as _PatchExecutor
from stillme_core.bug_memory import BugMemory as _BugMemory
from stillme_core.planner import Planner as _Planner
from stillme_core.ai_manager import AIManager as _AIManager


def _ensure_log_file(log_dir: _Path) -> _Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    today = _dt.datetime.now().strftime("%Y%m%d")
    base = log_dir / f"{today}.jsonl"
    # rotate if > 10MB
    def _size(p: _Path) -> int:
        return p.stat().st_size if p.exists() else 0
    if _size(base) <= 10 * 1024 * 1024:
        return base
    # find next index
    idx = 1
    while True:
        cand = log_dir / f"{today}-{idx}.jsonl"
        if _size(cand) <= 10 * 1024 * 1024:
            return cand
        idx += 1


def _log_jsonl(log_dir: _Path, record: dict) -> _Path:
    lf = _ensure_log_file(log_dir)
    record = {"ts": _dt.datetime.now().isoformat(), **record}
    with lf.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return lf


def agentdev_run_once(
    *,
    planner: Optional[object] = None,
    executor: Optional[object] = None,
    bug_memory: Optional[object] = None,
    log_dir: _Path = _Path("logs/agentdev"),
    run_full_suite_after_pass: bool = False,
    tests_dir: str = "tests",
    open_pr_after_pass: bool = False,
    pr_draft: bool = True,
    pr_base: str = "main",
    pr_remote: str = "origin",
    pr_title: Optional[str] = None,
    pr_body: Optional[str] = None,
):
    """
    Skeleton one-shot:
    - planner.build_plan() -> [PlanItem]
    - executor.apply_patch_and_test(PlanItem)
    - on fail: bug_memory.record(...); try refine once (stub) then stop
    - write JSONL log
    Returns: True on success; False/None on fail.
    """
    # Defaults for real run, tests may inject fakes
    planner = planner or _Planner()
    executor = executor or _PatchExecutor()
    bug_memory = bug_memory or _BugMemory()

    # Build plan items
    items = None
    if hasattr(planner, "build_plan"):
        try:
            items = planner.build_plan()
        except Exception:
            items = None
    if items is None:
        # Fallback: derive a trivial PlanItem from normalized plan
        plan = getattr(planner, "create_plan", None)
        if callable(plan):
            raw = planner.create_plan("Dry-run: analyze and propose a tiny fix")
            steps = (raw or {}).get("steps", [])
            if steps:
                items = [
                    _PlanItem(id=str(steps[0].get("step_id", "1")), title="auto-step", action=steps[0].get("action", "edit_file"))
                ]
            else:
                items = []
        else:
            items = []

    result_bool: Optional[bool] = None
    chosen = items[0] if items else None

    log_path = _log_jsonl(log_dir, {"step": "start", "items": len(items or [])})

    if not chosen:
        _log_jsonl(log_dir, {"step": "no_plan_items", "ok": True})
        return True

    # Apply patch & test
    import time as _t
    t_start = _t.perf_counter()
    branch_name = None
    # Create feature branch up front
    try:
        if hasattr(executor, "create_feature_branch"):
            ts = _dt.datetime.now().strftime("%Y%m%d%H%M%S")
            branch_name = f"feature/agentdev-{ts}"
            _ = executor.create_feature_branch(branch_name)
    except Exception:
        branch_name = None
    t0 = _t.perf_counter()
    try:
        diff = getattr(chosen, "patch", None) or getattr(chosen, "diff_hint", "") or ""
        if not diff:
            # Synthesize patch via model
            ai = _AIManager()
            context = ""  # TODO: optional file context extraction
            diff = ai.generate_patch(chosen, context=context)
            chosen.patch = diff or None

        if hasattr(executor, "apply_patch_and_test"):
            exec_res = executor.apply_patch_and_test(chosen)
        else:
            if diff:
                _ = executor.apply_unified_diff(diff)
            exec_res = executor.run_pytest(getattr(chosen, "tests_to_run", None))
            exec_res = {"ok": bool(getattr(exec_res, "ok", False))}
    except Exception as e:
        exec_res = {"ok": False, "error": str(e)}

    ok = bool(exec_res.get("ok", False)) if isinstance(exec_res, dict) else False
    duration_ms = int((_t.perf_counter() - t0) * 1000)
    if ok:
        _log_jsonl(log_dir, {"step": "apply", "item_id": chosen.id, "action": chosen.action, "ok": True, "branch": branch_name, "refined": False, "test_files": getattr(chosen, "tests_to_run", []), "duration_ms": duration_ms})
        result_bool = True
    else:
        # Record bug memory once
        try:
            if hasattr(bug_memory, "record"):
                bug_memory.record(file=getattr(chosen, "target", ""), test_name=(chosen.tests_to_run or [None])[0], message=str(exec_res))
        except Exception:
            pass
        _log_jsonl(log_dir, {"step": "apply", "item_id": getattr(chosen, "id", "?"), "action": getattr(chosen, "action", ""), "ok": False, "error_summary": str(exec_res)[:500], "duration_ms": duration_ms, "branch": branch_name})

        # Try one refine (REFINE_MAX=1)
        try:
            ai = _AIManager()
            refine_prompt_context = {
                "previous_patch": diff or "",
                "result": exec_res,
                "tests": getattr(chosen, "tests_to_run", []),
            }
            # Reuse PlanItem with updated diff_hint
            chosen.diff_hint = (diff or "") + "\n# refine based on test failures above"
            t1 = _t.perf_counter()
            new_diff = ai.generate_patch(chosen, context=json.dumps(refine_prompt_context))
            if new_diff:
                if hasattr(executor, "apply_patch_and_test"):
                    chosen.patch = new_diff
                    r2 = executor.apply_patch_and_test(chosen)
                    ok2 = bool(r2.get("ok", False)) if isinstance(r2, dict) else False
                else:
                    _ = executor.apply_unified_diff(new_diff)
                    r2 = executor.run_pytest(getattr(chosen, "tests_to_run", None))
                    ok2 = bool(getattr(r2, "ok", False))
            else:
                ok2 = False
        except Exception:
            ok2 = False
        result_bool = True if ok2 else False
        duration2_ms = int((_t.perf_counter() - t1) * 1000)
        _log_jsonl(log_dir, {"step": "refine", "item_id": getattr(chosen, "id", "?"), "refined": True, "ok": result_bool, "duration_ms": duration2_ms, "branch": branch_name})

    # Post-pass: run full suite if requested and apply passed
    fs_attempted = False
    fs_ok = None
    fs_col = None
    fs_failed = None
    fs_dur = None
    if result_bool and run_full_suite_after_pass:
        fs_attempted = True
        try:
            ok_all, collected, failed, dur_ms_all, raw_path = executor.run_pytest_all(tests_dir)
            fs_ok = ok_all
            fs_col = collected
            fs_failed = failed
            fs_dur = dur_ms_all
            _log_jsonl(log_dir, {"step": "full_suite", "ok": bool(ok_all), "branch": branch_name, "duration_ms": dur_ms_all, "collected": collected, "failed": failed})
            result_bool = result_bool and ok_all
        except Exception as e:
            fs_ok = False
            fs_failed = -1
            _log_jsonl(log_dir, {"step": "full_suite", "ok": False, "branch": branch_name, "error_summary": str(e)[:500]})

    # Optionally open PR
    pr_summary = {"attempted": False, "ok": None, "url": None, "number": None, "provider": None, "error": None}
    if result_bool and open_pr_after_pass:
        # title/body defaults
        title = pr_title or f"agentdev: {getattr(chosen, 'title', getattr(chosen, 'id', 'fix'))}"
        body = pr_body or "Automated fix by AgentDev. See logs for details."
        try:
            # push branch first
            _ = executor.push_branch(pr_remote)
            pr_summary = executor.create_pull_request(title=title, body=body, base=pr_base, remote=pr_remote, draft=pr_draft)
        except Exception as e:
            pr_summary = {"attempted": True, "ok": False, "url": None, "number": None, "provider": None, "error": str(e)}
        _log_jsonl(log_dir, {"step": "pr_create", "ok": bool(pr_summary.get("ok")), "branch": branch_name, "pr_url": pr_summary.get("url"), "pr_number": pr_summary.get("number"), "error_summary": pr_summary.get("error")})

    total_ms = int((_t.perf_counter() - t_start) * 1000)
    # Return structured summary for API layer
    return {
        "ok": bool(result_bool),
        "branch": branch_name,
        "refined": not ok and bool(result_bool),
        "duration_ms": total_ms,
        "full_suite": {
            "attempted": fs_attempted,
            "ok": fs_ok,
            "collected": fs_col,
            "failed": fs_failed,
            "duration_ms": fs_dur,
        },
        "pr": pr_summary,
    }