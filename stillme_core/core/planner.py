"""
planner.py - Tạo kế hoạch thực hiện sửa lỗi hoặc viết module mới bằng AI
Phiên bản cải tiến với:
1. Tự động sửa lỗi phổ biến (rule-based)
2. Prompt engineering chuẩn JSON
3. Fallback thông minh với local cache
4. Chuẩn hoá (normalize) JSON từ AI trước khi validate để giảm fail
"""

import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from stillme_core.ai_manager import AIManager
from stillme_core.ai_plan_schema import AI_PLAN_SCHEMA
from stillme_core.bug_memory import BugMemory
from stillme_core.plan_types import PlanItem

logger = logging.getLogger("AgentDev-Planner")

# ------------------------------
# Rule-based fixes cho các lỗi phổ biến
# ------------------------------
RULE_BASED_FIXES = {
    "ZeroDivisionError": {
        "module_name": "auto_fix",
        "description": "Auto-fix for division by zero.",
        "objectives": ["Prevent runtime ZeroDivisionError", "Return safe value"],
        "steps": [
            {
                "step_id": "1",
                "action": "modify_code",
                "reasoning": "Wrap risky division with try/except and return safe default.",
            }
        ],
    },
    "NameError": {
        "module_name": "auto_fix",
        "description": "Auto-fix for undefined name.",
        "objectives": ["Avoid NameError by defining missing variables"],
        "steps": [
            {
                "step_id": "1",
                "action": "add_variable_check",
                "reasoning": "Add default initialization if variable is missing.",
            }
        ],
    },
}

# ------------------------------
# Helpers: bóc/parse/chuẩn hoá JSON do AI trả về
# ------------------------------


def _unwrap_markdown_fence(text: str) -> str:
    """Bóc ```json ... ``` hoặc ``` ... ``` nếu có."""
    t = text.strip()
    if t.startswith("```") and t.endswith("```"):
        # loại bỏ 3 backticks đầu/cuối
        t = t[3:-3].strip()
        # nếu có prefix 'json' thì bỏ luôn
        if t.lower().startswith("json"):
            t = t[4:].strip()
    return t


def _extract_json_block(text: str) -> str:
    """
    Cố gắng lấy ra JSON object từ một chuỗi có thể lẫn văn bản.
    Chiến lược:
      1) Nếu toàn chuỗi load được → trả về luôn
      2) Thử bóc ```json ... ```
      3) Tìm block {...} đầu tiên bằng đếm ngoặc
    """
    t = text.strip()
    # 1) thử parse trực tiếp
    try:
        json.loads(t)
        return t
    except Exception:
        pass

    # 2) bóc fence
    t2 = _unwrap_markdown_fence(t)
    try:
        json.loads(t2)
        return t2
    except Exception:
        pass

    # 3) quét block { ... } cân bằng
    start = t.find("{")
    if start == -1:
        return t
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = t[start : i + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    break
    # fallback: trả lại bản gốc (để caller quyết định)
    return t


def _normalize_plan_v1(raw: dict[str, Any], problem_file: str | None) -> dict[str, Any]:
    """
    Chuẩn hoá JSON “yếu” thành schema Planner (module_name, description, objectives, steps[{step_id, action, reasoning}]).
    - Điền mặc định khi thiếu
    - Chuyển các field lạ về field chuẩn (code → reasoning, explanation → reasoning)
    - Thêm step_id nếu thiếu
    """
    module_name = raw.get("module_name") or (
        Path(problem_file).stem if problem_file else "unknown_module"
    )
    description = raw.get("description") or "Auto-generated fix plan."
    objectives_in = raw.get("objectives")
    if not isinstance(objectives_in, list):
        objectives = ["Fix error and add minimal validation"]
    else:
        objectives = [str(x) for x in objectives_in if x is not None]

    steps_in = raw.get("steps") or []
    steps_out: list[dict[str, str]] = []

    # Ánh xạ một số action “tự do” về nhóm chung (tùy chọn)
    ACTION_MAP = {
        "propose_solution": "review_diff",
        "provide_solution": "review_diff",
        "suggest_solution": "review_diff",
        "analyze": "analyze_error",
    }

    for idx, s in enumerate(steps_in, 1):
        if not isinstance(s, dict):
            continue
        action = s.get("action") or "review_diff"
        action = ACTION_MAP.get(action, action)
        reasoning = (
            s.get("reasoning")
            or s.get("code")
            or s.get("explanation")
            or s.get("text")
            or ""
        )
        steps_out.append(
            {
                "step_id": str(s.get("step_id") or idx),
                "action": str(action),
                "reasoning": str(reasoning),
            }
        )

    if not steps_out:
        steps_out.append(
            {
                "step_id": "1",
                "action": "analyze_error",
                "reasoning": "Analyze the stacktrace and locate the failing line.",
            }
        )

    return {
        "module_name": str(module_name),
        "description": str(description),
        "objectives": objectives,
        "steps": steps_out,
    }


class Planner:
    def __init__(self):
        self.ai_manager = AIManager()
        self.last_plan = None
        self.last_raw_ai_response = None
        self.fallback_cache: dict[str, dict[str, Any]] = {}
        self.bugmem = BugMemory()
        self.plan_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def create_plan(
        self,
        prompt: str,
        error_type: str | None = None,
        problem_file: str | None = None,
    ) -> dict[str, Any]:
        """
        Tạo kế hoạch sửa lỗi cho DevAgent.
        - Ưu tiên: rule-based → AI (safe) → cache → AI (fast) → last_plan → safe_dummy
        - Luôn trả về dict JSON hợp lệ; KHÔNG bao giờ trả None.
        """
        # 1) Rule-based fix nếu có
        if error_type in RULE_BASED_FIXES:
            logger.info(f"🛠 Áp dụng rule-based fix cho {error_type}")
            plan = RULE_BASED_FIXES[error_type]
            self._cache_valid_response(prompt, plan)
            self.last_plan = plan
            return plan

        # 2) Prompt có cấu trúc
        enhanced_prompt = self._build_structured_prompt(prompt)

        # 3) Gọi AI (safe/think), yêu cầu CHỈ JSON
        system_prompt = (
            "Bạn là trợ lý tạo kế hoạch sửa lỗi. "
            "Chỉ trả về JSON hợp lệ theo schema đã mô tả, không kèm văn bản ngoài JSON."
        )

        def _preview(s: str | None) -> str:
            try:
                return (s or "")[:300].replace("\n", "\\n")
            except Exception:
                return "<unpreviewable>"

        # --- Lần 1: SAFE / THINK ---
        try:
            logger.info("⛏ Gọi Bridge (mode=think/safe) để tạo kế hoạch JSON…")
            schema_hint = {
                "plan_id": "string",
                "strategy": "rule_based_fix | ai_generated | from_cache",
                "rationale": "string",
                "steps": [
                    {
                        "id": "string",
                        "title": "string",
                        "action": "edit_file | run_tests | create_file | refactor | command",
                        "detail": "string",
                        "target": "string or null",
                        "patch": "string or null",
                    }
                ],
                "risk_mitigation": "string",
            }

            raw_response = self.ai_manager.get_ai_response(
                enhanced_prompt,
                mode="safe",
                max_tokens=512,
                temperature=0.3,
                top_p=0.95,
                system_prompt=system_prompt,  # như anh đã có
                response_format="json",
                force_json=True,
                schema_hint=schema_hint,
            )

            self.last_raw_ai_response = raw_response
            logger.debug(f"🔍 Raw SAFE preview: { _preview(raw_response) }")
        except Exception as e:
            logger.exception(f"SAFE call error: {e}")
            raw_response = None

        plan = self._try_parse_and_validate_plan(raw_response, problem_file)
        if plan:
            logger.info("✅ Kế hoạch AI (safe) hợp lệ")
            self._cache_valid_response(prompt, plan)
            self.last_plan = plan
            return plan

        # 4) Dùng cache nếu có
        cached_plan = self._get_cached_plan(prompt)
        if cached_plan:
            logger.warning("⚠ Dùng cached plan thay vì gọi AI lại (sau SAFE)")
            self.last_plan = cached_plan
            return cached_plan

        # --- Lần 2: FAST ---
        try:
            logger.warning("⚠ SAFE không hợp lệ. Fallback qua Bridge (mode=fast)…")
            raw_response_fast = self.ai_manager.get_ai_response(
                enhanced_prompt,
                mode="fast",
                max_tokens=512,
                temperature=0.4,
                top_p=0.95,
                system_prompt=system_prompt,
            )
            logger.debug(f"🔍 Raw FAST preview: { _preview(raw_response_fast) }")
        except Exception as e:
            logger.exception(f"FAST call error: {e}")
            raw_response_fast = None

        plan = self._try_parse_and_validate_plan(raw_response_fast, problem_file)
        if plan:
            logger.info("✅ Kế hoạch AI (fast) hợp lệ")
            self._cache_valid_response(prompt, plan)
            self.last_plan = plan
            return plan

        # 5) Dùng last_plan nếu có
        if self.last_plan:
            logger.error("❌ AI fail. Dùng last_plan dự phòng")
            return self.last_plan

        # 6) Cuối cùng: trả về safe_dummy để KHÔNG bao giờ None
        logger.error("❌ Không thể tạo kế hoạch sau nhiều lần thử → trả safe_dummy")
        safe_dummy = {
            "plan_id": "safe_dummy",
            "strategy": "from_cache",
            "rationale": "AI không tạo được kế hoạch hợp lệ. Trả về kế hoạch rỗng an toàn.",
            "steps": [],
            "risk_mitigation": "Đánh dấu cần can thiệp thủ công; không thực thi thay đổi.",
            "from_cache": True,
        }
        # Không cache dummy để tránh “ô nhiễm” cache
        return safe_dummy

    def _try_parse_and_validate_plan(
        self, raw_response: str | None, problem_file: str | None = None
    ) -> dict[str, Any] | None:
        # Chặn None / chuỗi rỗng
        if (
            not raw_response
            or not isinstance(raw_response, str)
            or not raw_response.strip()
        ):
            logger.warning("⚠ raw_response trống hoặc None → bỏ qua parse")
            return None

        # Log ngắn gọn để debug
        preview = raw_response[:200].replace("\n", "\\n")
        logger.debug(f"Raw AI plan preview: {preview}")

        try:
            json_str = _extract_json_block(raw_response)
            try:
                data = json.loads(json_str)
            except Exception:
                # Nếu không parse được → dựng khung tối thiểu
                data = {
                    "module_name": (
                        Path(problem_file).stem if problem_file else "unknown_module"
                    ),
                    "steps": [],
                }

            # Chuẩn hoá về schema Planner
            normalized = _normalize_plan_v1(data, problem_file=problem_file)

            # Validate lần cuối theo AI_PLAN_SCHEMA
            validate(instance=normalized, schema=AI_PLAN_SCHEMA)
            return normalized

        except (ValidationError, Exception) as e:
            logger.error(f"❌ Lỗi validate plan: {e!s}")
            return None

    def _build_structured_prompt(
        self, problem_desc: str, strict_json: bool = False
    ) -> str:
        base_prompt = """Hãy trả lời theo ĐÚNG định dạng JSON sau (ví dụ):
    ```json
    {
      "module_name": "example_module",
      "description": "Short summary of the fix plan.",
      "objectives": ["objective 1", "objective 2"],
      "steps": [
        {"step_id": "1", "action": "analyze_error", "reasoning": "why/how"},
        {"step_id": "2", "action": "review_diff", "reasoning": "what to check"}
      ]
    }

    Yêu cầu:

    Bắt buộc dùng double quotes

    Không chứa markdown hay văn bản thừa ngoài khối JSON

    Luôn có "module_name", "description", "objectives" và ít nhất 1 step

    Step phải có "step_id", "action", "reasoning"

    Vấn đề cần giải quyết:
    """
        if strict_json:
            base_prompt += (
                "\nQUAN TRỌNG: Trả về CHỈ JSON hợp lệ, không có giải thích kèm theo.\n"
            )
            return base_prompt + problem_desc
        else:
            return base_prompt + problem_desc

    def _cache_valid_response(self, prompt: str, plan: dict[str, Any]):
        prompt_key = hashlib.sha256(prompt.encode()).hexdigest()
        self.fallback_cache[prompt_key] = plan

    def _get_cached_plan(self, prompt: str) -> dict[str, Any] | None:
        prompt_key = hashlib.sha256(prompt.encode()).hexdigest()
        return self.fallback_cache.get(prompt_key)

    # ------------------------------
    # Multi-step builder (heuristic)
    # ------------------------------
    def build_plan(self, max_items: int = 5) -> list[PlanItem]:
        # Check cache first
        cache_key = f"plan_{max_items}"
        import time

        current_time = time.time()

        if cache_key in self.plan_cache:
            cached_time, cached_items = self.plan_cache[cache_key]
            if current_time - cached_time < self.cache_ttl:
                logger.info(f"Using cached plan for max_items={max_items}")
                return cached_items

        items: list[PlanItem] = []

        try:
            logger.info(f"Building plan with max_items={max_items}")

            # a) git status with enhanced timeout handling
            try:
                import os

                # Skip git operations in test mode
                if os.getenv("AGENTDEV_TEST_MODE") or os.getenv("SKIP_GIT_OPERATIONS"):
                    logger.info("Skipping git status in test mode")
                else:
                    p = subprocess.run(
                        ["git", "status", "--porcelain"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if p.returncode == 0:
                        for ln in p.stdout.splitlines():
                            ln = ln.strip()
                            if not ln:
                                continue
                            # format: ' M path' or '?? path'
                            parts = ln.split()
                            if len(parts) < 2:
                                continue
                            file_path = parts[-1]
                            if file_path.endswith(".py") and not file_path.startswith(
                                "tests/"
                            ):
                                test_guess = f"tests/test_{Path(file_path).stem}.py"
                                items.append(
                                    PlanItem(
                                        id=f"GIT-{len(items)+1}",
                                        title=f"Review & fix {file_path}",
                                        action="edit_file",
                                        target=file_path,
                                        diff_hint="",
                                        tests_to_run=[test_guess],
                                        risk="medium",
                                    )
                                )
                                if len(items) >= max_items:
                                    return items
                    else:
                        logger.warning(f"Git status failed: {p.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning("Git status timed out")
            except Exception as e:
                logger.warning(f"Git status error: {e}")

            # If no items found, create fallback plan
            if not items:
                logger.info("No git changes found, creating fallback plan")
                items.append(
                    PlanItem(
                        id="FALLBACK-1",
                        title="Run basic tests to verify system",
                        action="run_tests",
                        target="tests/",
                        diff_hint="",
                        tests_to_run=["tests/"],
                        risk="low",
                    )
                )

            result_items = items[:max_items]
            # Cache the result
            self.plan_cache[cache_key] = (current_time, result_items)
            return result_items

        except Exception as e:
            logger.error(f"Plan building failed: {e}")
            # Return minimal fallback plan
            fallback_items = [
                PlanItem(
                    id="EMERGENCY-1",
                    title="Emergency fallback: Run basic tests",
                    action="run_tests",
                    target="tests/",
                    diff_hint="",
                    tests_to_run=["tests/"],
                    risk="low",
                )
            ]
            # Cache the fallback too
            self.plan_cache[cache_key] = (current_time, fallback_items)
            return fallback_items

        # b) pytest last-failed cache
        try:
            cache_path = Path(".pytest_cache/v/cache/lastfailed")
            if cache_path.exists():
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                # data keys are nodeids like tests/test_foo.py::TestCls::test_x
                for nodeid in data.keys():
                    file_path = nodeid.split("::")[0]
                    if file_path.endswith(".py"):
                        items.append(
                            PlanItem(
                                id=f"PYT-{len(items)+1}",
                                title=f"Re-run and fix failing: {nodeid}",
                                action="run_tests",
                                target=file_path,
                                tests_to_run=[nodeid],
                                risk="high",
                            )
                        )
                        if len(items) >= max_items:
                            return items
        except Exception:
            pass

        # c) BugMemory priority
        try:
            stats = self.bugmem.stats_by_file()
            for file_path, _cnt in sorted(
                stats.items(), key=lambda kv: kv[1], reverse=True
            ):
                if file_path and file_path.endswith(".py"):
                    test_guess = f"tests/test_{Path(file_path).stem}.py"
                    items.append(
                        PlanItem(
                            id=f"BM-{len(items)+1}",
                            title=f"Address recurring failures in {file_path}",
                            action="edit_file",
                            target=file_path,
                            tests_to_run=[test_guess],
                            risk="high",
                        )
                    )
                    if len(items) >= max_items:
                        return items
        except Exception:
            pass

        # d) fallback at least 2 items using repo roots
        if len(items) < 2:
            items.append(
                PlanItem(
                    id=f"FB-{len(items)+1}",
                    title="Run focused tests",
                    action="run_tests",
                    tests_to_run=["tests/"],
                )
            )
        if len(items) < 2:
            items.append(
                PlanItem(
                    id=f"FB-{len(items)+1}",
                    title="Lint key files",
                    action="command",
                    tests_to_run=["tests/"],
                )
            )
        return items[:max_items]

    def plan(
        self,
        problem_description: str,
        problem_file: str | None = None,
        error_type: str | None = None,
        previous_plan_feedback: str | None = None,
        current_attempt: int = 1,
    ) -> dict[str, Any] | None:
        prompt = self._build_prompt(
            problem_description=problem_description,
            problem_file=problem_file,
            previous_feedback=previous_plan_feedback,
            current_attempt=current_attempt,
        )
        return self.create_plan(prompt, error_type, problem_file=problem_file)

    def _build_prompt(
        self,
        problem_description: str,
        problem_file: str | None = None,
        previous_feedback: str | None = None,
        current_attempt: int = 1,
    ) -> str:
        prompt = f"[AgentDev Planning Request - Attempt {current_attempt}]\n\n"
        prompt += f"❖ Mô tả vấn đề:\n{problem_description}\n\n"

        if problem_file:
            prompt += f"📄 File liên quan: {problem_file}\n\n"
        if previous_feedback:
            prompt += f"🔁 Phản hồi từ lần trước:\n{previous_feedback}\n\n"

        prompt += "🎯 Yêu cầu:\n"
        prompt += (
            "1. Phân tích nguyên nhân\n2. Đề xuất giải pháp\n3. Code mẫu (nếu cần)\n"
        )
        return prompt
