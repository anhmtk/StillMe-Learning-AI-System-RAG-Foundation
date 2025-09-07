# stillme_core/ai_manager.py
"""
AI Manager – lớp mỏng điều phối giữa StillMe và Dev Agent Bridge.
Các chế độ:
- fast  : text-only (REST nhanh)  -> bridge mode="fast" (mặc định llama3:8b)
- think : suy luận sâu (text)     -> bridge mode="safe" (mặc định gpt-oss:20b hoặc cấu hình .env)
- code  : model sinh code + sandbox -> giữ nguyên OpenInterpreterController
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
import asyncio
import time
import json
import os
import httpx
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from .config_defaults import try_load_dotenv, DEFAULT_MODE
from .plan_types import PlanItem
from .bug_memory import BugMemory

# 1) Bridge (Dev Agent)
from stillme_core.provider_router import ask  # async def ask(...)

# 2) Code path (giữ như cũ)
from oi_adapter.interpreter_controller import OpenInterpreterController as C

# =======================
# Enhanced AI Manager with Context-Aware Planning
# =======================

@dataclass
class ContextInfo:
    """Context information for AI planning"""
    file_dependencies: List[str]
    recent_changes: List[str]
    test_failures: List[str]
    similar_bugs: List[Dict[str, Any]]
    code_complexity: float
    risk_factors: List[str]

@dataclass
class LearningEntry:
    """Learning entry from previous bugs and solutions"""
    bug_type: str
    solution: str
    success_rate: float
    context: Dict[str, Any]
    timestamp: float

class ContextAnalyzer:
    """Analyzes code context for better AI planning"""
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.dependency_cache = {}
        self.change_history = deque(maxlen=100)
    
    def analyze_file_dependencies(self, file_path: str) -> List[str]:
        """Analyze file dependencies using import statements"""
        if file_path in self.dependency_cache:
            return self.dependency_cache[file_path]
        
        dependencies = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple import analysis
            import re
            imports = re.findall(r'from\s+(\S+)\s+import|import\s+(\S+)', content)
            for imp in imports:
                dep = imp[0] or imp[1]
                if dep and not dep.startswith('.'):
                    dependencies.append(dep)
                    
        except Exception:
            pass
            
        self.dependency_cache[file_path] = dependencies
        return dependencies
    
    def analyze_code_complexity(self, file_path: str) -> float:
        """Simple code complexity analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic metrics
            lines = len(content.splitlines())
            functions = content.count('def ')
            classes = content.count('class ')
            imports = content.count('import ')
            
            # Simple complexity score
            complexity = (functions * 2 + classes * 3 + imports * 0.5) / max(lines, 1)
            return min(complexity, 10.0)  # Cap at 10
            
        except Exception:
            return 1.0
    
    def get_context_info(self, file_path: str) -> ContextInfo:
        """Get comprehensive context information for a file"""
        dependencies = self.analyze_file_dependencies(file_path)
        complexity = self.analyze_code_complexity(file_path)
        
        # Get recent changes
        recent_changes = list(self.change_history)[-10:]
        
        # Risk factors
        risk_factors = []
        if complexity > 5:
            risk_factors.append("high_complexity")
        if len(dependencies) > 10:
            risk_factors.append("many_dependencies")
        if file_path.endswith('__init__.py'):
            risk_factors.append("init_file")
            
        return ContextInfo(
            file_dependencies=dependencies,
            recent_changes=recent_changes,
            test_failures=[],
            similar_bugs=[],
            code_complexity=complexity,
            risk_factors=risk_factors
        )

class LearningManager:
    """Manages learning from previous bugs and solutions"""
    
    def __init__(self, max_entries: int = 1000):
        self.learning_entries: deque = deque(maxlen=max_entries)
        self.bug_patterns: Dict[str, List[LearningEntry]] = defaultdict(list)
        self.success_rates: Dict[str, float] = {}
    
    def add_learning_entry(self, bug_type: str, solution: str, success: bool, context: Dict[str, Any]):
        """Add a new learning entry"""
        entry = LearningEntry(
            bug_type=bug_type,
            solution=solution,
            success_rate=1.0 if success else 0.0,
            context=context,
            timestamp=time.time()
        )
        
        self.learning_entries.append(entry)
        self.bug_patterns[bug_type].append(entry)
        
        # Update success rate
        if bug_type in self.success_rates:
            current_rate = self.success_rates[bug_type]
            new_rate = (current_rate * 0.9) + (1.0 if success else 0.0) * 0.1
            self.success_rates[bug_type] = new_rate
        else:
            self.success_rates[bug_type] = 1.0 if success else 0.0
    
    def get_similar_solutions(self, bug_type: str, context: Dict[str, Any]) -> List[LearningEntry]:
        """Get similar solutions for a bug type"""
        if bug_type not in self.bug_patterns:
            return []
        
        # Simple similarity based on context keys
        similar = []
        for entry in self.bug_patterns[bug_type]:
            if entry.success_rate > 0.7:  # Only successful solutions
                similar.append(entry)
        
        return sorted(similar, key=lambda x: x.success_rate, reverse=True)[:5]
    
    def get_best_solution_strategy(self, bug_type: str) -> str:
        """Get the best solution strategy for a bug type"""
        if bug_type not in self.success_rates:
            return "standard"
        
        success_rate = self.success_rates[bug_type]
        if success_rate > 0.8:
            return "proven"
        elif success_rate > 0.5:
            return "cautious"
        else:
            return "experimental"

class FallbackStrategy:
    """Intelligent fallback strategies for AI failures"""
    
    def __init__(self):
        self.fallback_chain = [
            "fast",      # Try fast mode first
            "think",     # Then think mode
            "code",      # Then code mode
            "cached",    # Finally use cached response
        ]
        self.cache: Dict[str, str] = {}
        self.failure_counts: Dict[str, int] = defaultdict(int)
    
    def get_fallback_mode(self, original_mode: str, failure_reason: str) -> str:
        """Get next fallback mode based on failure"""
        self.failure_counts[original_mode] += 1
        
        # If too many failures, skip to next mode
        if self.failure_counts[original_mode] > 3:
            current_index = self.fallback_chain.index(original_mode)
            if current_index < len(self.fallback_chain) - 1:
                return self.fallback_chain[current_index + 1]
        
        return original_mode
    
    def get_cached_response(self, prompt_hash: str) -> Optional[str]:
        """Get cached response if available"""
        return self.cache.get(prompt_hash)
    
    def cache_response(self, prompt_hash: str, response: str):
        """Cache a successful response"""
        self.cache[prompt_hash] = response

# =======================
# Singleton controller cho nhánh "code"
# =======================
_CTL: Optional[C] = None

def controller() -> C:
    global _CTL
    if _CTL is None:
        _CTL = C()
    return _CTL

# =======================
# Tiện ích mapping mode
# =======================
_TEXT_MODE_MAP = {
    "fast": "fast",
    "think": "safe",
}

# Load .env if available
try_load_dotenv()

# =======================
# Public API cũ (giữ tương thích)
# =======================
def set_mode(mode: str) -> str:
    """
    (Giữ để tương thích) – Trước đây set model trực tiếp.
    Hiện tại: với text-mode, model do Bridge quyết định theo .env; với code-mode vẫn dùng controller.
    """
    if mode == "code":
        ctl = controller()
        try:
            return ctl.set_model("deepseek-coder:6.7b")
        except Exception:
            return "[AIManager] controller: set_model('deepseek-coder:6.7b') failed or not required"
    return "[AIManager] text-mode uses Dev Agent Bridge; no local set_model needed."

def warmup(model: Optional[str] = None) -> Dict[str, Any]:
    """Warmup cho nhánh code (tuỳ controller)."""
    try:
        return controller().warmup(model=model)
    except Exception:
        return {"ok": False, "msg": "warmup not supported for controller or failed"}

def health(model: Optional[str] = None) -> Dict[str, Any]:
    """Health-check nhanh cho nhánh code (controller)."""
    try:
        return controller().health(model=model)
    except Exception:
        return {"ok": False, "msg": "health not supported for controller or failed"}
# --- add to stillme_core/ai_manager.py ---

def _gpt5_ping() -> Dict[str, Any]:
    """
    Ping thật GPT-5 bằng một chat mini 'ping' → 'pong'.
    Trả: {"enabled": bool, "ok": bool, "error": "...?"}
    """
    enabled = os.getenv("ALLOW_GPT5", "true").lower() == "true"
    base_url = os.getenv("GPT5_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("GPT5_MODEL_FAST", "gpt-5-mini")
    out: Dict[str, Any] = {"enabled": enabled, "ok": False}

    if not enabled:
        return out
    if not api_key:
        out["error"] = "missing OPENAI_API_KEY"
        return out

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        # LƯU Ý: đừng set temperature=0 vì một số model không cho override
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
        )
        _ = r.choices[0].message.content or ""
        out["ok"] = True
        return out
    except Exception as e:
        out["error"] = str(e)[:300]
        return out


def _ollama_ping() -> Dict[str, Any]:
    """
    Ping nhanh Ollama bằng /api/tags.
    Trả: {"ok": bool, "error": "...?"}
    """
    url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    try:
        r = httpx.get(f"{url}/api/tags", timeout=2)
        r.raise_for_status()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

# =======================
# Bridge helpers (đÃ SỬA: tránh tạo coroutine khi loop đang chạy)
# =======================
def _bridge_sync_ask(prompt: str, mode: str = "fast", **params: Any) -> str:
    """
    Helper ĐỒNG BỘ gọi bridge.
    - Nếu KHÔNG có event loop đang chạy: dùng asyncio.run(ask(...))
    - Nếu ĐANG có event loop: KHÔNG tạo coroutine -> raise RuntimeError để caller chọn đường async
    """
    # Quan trọng: kiểm tra loop trước, tránh tạo coroutine bị bỏ rơi
    try:
        asyncio.get_running_loop()  # có loop -> báo lên
        raise RuntimeError("event loop is running")
    except RuntimeError as no_loop:
        # Không có loop đang chạy -> an toàn để run
        if str(no_loop) != "event loop is running":
            return asyncio.run(ask(prompt, mode=mode, **params))
        # Có loop -> rơi xuống except phía dưới
        pass
    # Có loop đang chạy -> báo cho caller dùng async API
    raise RuntimeError("Event loop is running; use aget_ai_response()")

async def _bridge_async_ask(prompt: str, mode: str = "fast", **params: Any) -> str:
    return await ask(prompt, mode=mode, **params)

# =======================
# Router tác vụ “dev_agent”
# =======================
def dev_agent(task: str, mode: str = DEFAULT_MODE, **params: Any) -> str:
    """
    Router tác vụ:
      - fast  : text-only -> bridge mode="fast"
      - think : text-only -> bridge mode="safe"
      - code  : deepseek-coder:6.7b + python sandbox
    """
    mode_lower = (mode or "fast").lower()

    if mode_lower == "code":
        ctl = controller()
        try:
            ctl.set_model("deepseek-coder:6.7b")
        except Exception:
            pass
        try:
            return ctl.run_python_via_model(task)
        except Exception as e:
            return f"[AIManager][code] error: {e}"

    bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
    try:
        return _bridge_sync_ask(task, mode=bridge_mode, **params)
    except RuntimeError as re:
        # Không cố gọi async từ đây để tránh warning; trả hướng dẫn rõ ràng
        return f"[AIManager][{bridge_mode}] cannot run sync in running loop; use aget_ai_response(). Detail: {re}"
    except Exception as e:
        # Fallback sang fast (nếu safe lỗi)
        try:
            return _bridge_sync_ask(task, mode="fast", **params)
        except Exception:
            return f"[AIManager][{bridge_mode}] error: {e}"

def compute_number(task: str) -> str:
    """Đảm bảo trả về CHỈ CHỮ SỐ cho các phép tính đơn giản (nhánh controller)."""
    ctl = controller()
    try:
        ctl.set_model("llama3:8b")
    except Exception:
        pass
    try:
        warmup()
    except Exception:
        pass
    try:
        return ctl.run_compute_number(task)
    except Exception as e:
        return f"[AIManager][compute_number] error: {e}"

# =========================
# NEW: Lớp AIManager (wrapper)
# =========================
class AIManager:
    """
    Enhanced AI Manager with context-aware planning, learning, and fallback strategies
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self.context_analyzer = ContextAnalyzer(repo_root)
        self.learning_manager = LearningManager()
        self.fallback_strategy = FallbackStrategy()
        self.bugmem = BugMemory()
        
        # Performance tracking
        self.request_times: Dict[str, List[float]] = defaultdict(list)
        self.success_rates: Dict[str, float] = defaultdict(lambda: 1.0)

    # ====== Enhanced Planning Methods ======
    
    def get_context_aware_plan(self, goal: str, max_items: int = 5) -> List[PlanItem]:
        """Generate context-aware plan using AI with enhanced context"""
        try:
            # Analyze current repository state
            context_info = self._analyze_repository_context()
            
            # Get learning insights
            learning_insights = self._get_learning_insights(goal)
            
            # Build enhanced prompt
            prompt = self._build_context_aware_prompt(goal, context_info, learning_insights, max_items)
            
            # Get AI response with fallback
            response = self._get_ai_response_with_fallback(prompt, mode="think")
            
            # Parse and enhance plan
            plan_items = self._parse_enhanced_plan(response, context_info)
            
            return plan_items[:max_items]
            
        except Exception as e:
            # Fallback to basic planning
            return self._get_fallback_plan(goal, max_items)
    
    def _analyze_repository_context(self) -> Dict[str, Any]:
        """Analyze current repository context"""
        context = {
            "git_status": self._get_git_status(),
            "recent_files": self._get_recent_files(),
            "test_status": self._get_test_status(),
            "dependencies": self._get_dependency_info(),
        }
        return context
    
    def _get_git_status(self) -> List[str]:
        """Get git status information"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception:
            pass
        return []
    
    def _get_recent_files(self) -> List[str]:
        """Get recently modified files"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "--name-only", "--oneline", "-10"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                files = []
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith(' '):
                        files.append(line.strip())
                return files[:10]
        except Exception:
            pass
        return []
    
    def _get_test_status(self) -> Dict[str, Any]:
        """Get current test status"""
        try:
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True, text=True, timeout=10
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception:
            return {"status": "unknown", "output": "", "error": ""}
    
    def _get_dependency_info(self) -> Dict[str, Any]:
        """Get dependency information"""
        try:
            requirements_file = Path(self.repo_root) / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                return {"requirements": deps, "count": len(deps)}
        except Exception:
            pass
        return {"requirements": [], "count": 0}
    
    def _get_learning_insights(self, goal: str) -> Dict[str, Any]:
        """Get learning insights from previous similar goals"""
        # Simple keyword matching for now
        keywords = goal.lower().split()
        insights = {
            "similar_bugs": [],
            "success_strategies": [],
            "risk_factors": []
        }
        
        for keyword in keywords:
            if keyword in self.learning_manager.bug_patterns:
                similar = self.learning_manager.get_similar_solutions(keyword, {})
                insights["similar_bugs"].extend(similar[:3])
        
        return insights
    
    def _build_context_aware_prompt(self, goal: str, context: Dict[str, Any], 
                                  learning: Dict[str, Any], max_items: int) -> str:
        """Build enhanced prompt with context and learning"""
        prompt = f"""
You are an expert software engineer analyzing a codebase. Generate a detailed plan to achieve: "{goal}"

CONTEXT ANALYSIS:
- Git Status: {context.get('git_status', [])}
- Recent Files: {context.get('recent_files', [])}
- Test Status: {context.get('test_status', {}).get('status', 'unknown')}
- Dependencies: {context.get('dependencies', {}).get('count', 0)} packages

LEARNING INSIGHTS:
- Similar Previous Issues: {len(learning.get('similar_bugs', []))}
- Success Strategies: {learning.get('success_strategies', [])}

REQUIREMENTS:
1. Generate exactly {max_items} plan items
2. Each item should be specific and actionable
3. Consider dependencies between files
4. Include risk assessment for each item
5. Suggest appropriate tests for each change

FORMAT: Return as JSON array of plan items with fields:
- id: unique identifier
- title: descriptive title
- action: action type (fix, add, modify, test)
- target: file or component to work on
- diff_hint: brief description of changes needed
- tests_to_run: list of tests to run
- risk: risk level (low, medium, high)
- dependencies: list of other plan items this depends on
"""
        return prompt
    
    def _parse_enhanced_plan(self, response: str, context: Dict[str, Any]) -> List[PlanItem]:
        """Parse AI response into PlanItem objects"""
        try:
            # Try to parse as JSON first
            import json
            data = json.loads(response)
            if isinstance(data, list):
                items = []
                for item_data in data:
                    if isinstance(item_data, dict):
                        item = PlanItem(
                            id=item_data.get('id', f"AI-{len(items)+1}"),
                            title=item_data.get('title', 'AI Generated Task'),
                            action=item_data.get('action', 'modify'),
                            target=item_data.get('target', ''),
                            diff_hint=item_data.get('diff_hint', ''),
                            tests_to_run=item_data.get('tests_to_run', []),
                            risk=item_data.get('risk', 'medium'),
                        )
                        items.append(item)
                return items
        except Exception:
            pass
        
        # Fallback: parse as text
        return self._parse_text_plan(response)
    
    def _parse_text_plan(self, response: str) -> List[PlanItem]:
        """Parse text response into PlanItem objects"""
        items = []
        lines = response.split('\n')
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_item:
                    items.append(current_item)
                current_item = PlanItem(
                    id=f"AI-{len(items)+1}",
                    title=line[2:].strip(),
                    action="modify",
                    target="",
                    diff_hint="",
                    tests_to_run=[],
                    risk="medium",
                )
            elif current_item and line.startswith('-'):
                # Add details to current item
                detail = line[1:].strip()
                if 'test' in detail.lower():
                    current_item.tests_to_run.append(detail)
                elif 'file' in detail.lower():
                    current_item.target = detail
        
        if current_item:
            items.append(current_item)
        
        return items
    
    def _get_fallback_plan(self, goal: str, max_items: int) -> List[PlanItem]:
        """Generate fallback plan when AI fails"""
        return [
            PlanItem(
                id="FALLBACK-1",
                title=f"Analyze goal: {goal}",
                action="analyze",
                target="",
                diff_hint="",
                tests_to_run=[],
                risk="low",
            ),
            PlanItem(
                id="FALLBACK-2",
                title="Run basic tests to verify system",
                action="test",
                target="tests/",
                diff_hint="",
                tests_to_run=["tests/"],
                risk="low",
            )
        ]
    
    # ====== Enhanced AI Response Methods ======
    
    def _get_ai_response_with_fallback(self, prompt: str, mode: str = "fast") -> str:
        """Get AI response with intelligent fallback"""
        prompt_hash = str(hash(prompt))
        
        # Check cache first
        cached = self.fallback_strategy.get_cached_response(prompt_hash)
        if cached:
            return cached
        
        # Try different modes with fallback
        current_mode = mode
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                start_time = time.time()
                response = self._get_ai_response(prompt, current_mode)
                end_time = time.time()
                
                # Track performance
                self.request_times[current_mode].append(end_time - start_time)
                
                # Cache successful response
                if response and len(response) > 10:
                    self.fallback_strategy.cache_response(prompt_hash, response)
                    return response
                
            except Exception as e:
                # Get next fallback mode
                current_mode = self.fallback_strategy.get_fallback_mode(current_mode, str(e))
                if attempt < max_attempts - 1:
                    continue
        
        # Final fallback: return empty response
        return ""
    
    def _get_ai_response(self, prompt: str, mode: str) -> str:
        """Get AI response using the original method"""
        mode_lower = mode.lower()
        
        if mode_lower == "code":
            ctl = controller()
            try:
                ctl.set_model("deepseek-coder:6.7b")
                return ctl.run_python_via_model(prompt)
            except Exception as e:
                raise Exception(f"Code mode failed: {e}")
        
        bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
        try:
            return _bridge_sync_ask(prompt, mode=bridge_mode)
        except RuntimeError:
            # Try async if sync fails
            try:
                return asyncio.run(_bridge_async_ask(prompt, mode=bridge_mode))
            except Exception as e:
                raise Exception(f"Bridge mode {bridge_mode} failed: {e}")
        except Exception as e:
            raise Exception(f"Bridge mode {bridge_mode} failed: {e}")
    
    # ====== Learning and Feedback Methods ======
    
    def record_success(self, plan_item: PlanItem, success: bool, context: Dict[str, Any]):
        """Record success/failure for learning"""
        bug_type = self._classify_bug_type(plan_item, context)
        solution = plan_item.diff_hint or plan_item.title
        
        self.learning_manager.add_learning_entry(
            bug_type=bug_type,
            solution=solution,
            success=success,
            context=context
        )
    
    def _classify_bug_type(self, plan_item: PlanItem, context: Dict[str, Any]) -> str:
        """Classify the type of bug/issue"""
        title = plan_item.title.lower()
        action = plan_item.action.lower()
        
        if 'test' in title or 'test' in action:
            return 'test_failure'
        elif 'import' in title or 'import' in action:
            return 'import_error'
        elif 'syntax' in title or 'syntax' in action:
            return 'syntax_error'
        elif 'runtime' in title or 'runtime' in action:
            return 'runtime_error'
        else:
            return 'general_issue'
    
    # ====== Original API Methods (for compatibility) ======
    
    def set_mode(self, mode: str) -> str:
        return set_mode(mode)

    def warmup(self, model: Optional[str] = None) -> Dict[str, Any]:
        return warmup(model)

    def health(self, model: Optional[str] = None) -> Dict[str, Any]:
        return health(model)

    def dev_agent(self, task: str, mode: str = "fast", **params: Any) -> str:
        return dev_agent(task, mode, **params)

    def compute_number(self, task: str) -> str:
        return compute_number(task)

    # ====== API Planner kỳ vọng ======
    def get_ai_response(self, prompt: str, mode: str = "fast", **params: Any) -> str:
        """
        BẢN SYNC: dùng khi KHÔNG ở trong event loop (ví dụ test/unit sync).
        Nếu đang ở trong event loop, hàm này trả message hướng dẫn dùng async.
        """
        mode_lower = (mode or "fast").lower()
        if mode_lower == "code":
            return dev_agent(prompt, "code", **params)

        bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
        try:
            return _bridge_sync_ask(prompt, mode=bridge_mode, **params)
        except RuntimeError as re:
            # Không tạo coroutine ở đây -> không còn "coroutine was never awaited"
            return f"[AIManager][{bridge_mode}] cannot run sync in running loop; use aget_ai_response(). Detail: {re}"
        except Exception:
            try:
                return _bridge_sync_ask(prompt, mode="fast", **params)
            except Exception:
                return ""

    async def aget_ai_response(self, prompt: str, mode: str = "fast", **params: Any) -> str:
        """BẢN ASYNC: dùng trong FastAPI handler / async context."""
        mode_lower = (mode or "fast").lower()
        if mode_lower == "code":
            # Nếu thực sự cần gọi controller sync trong async context, cân nhắc chạy bằng thread executor
            return dev_agent(prompt, "code", **params)

        bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
        try:
            return await _bridge_async_ask(prompt, mode=bridge_mode, **params)
        except Exception:
            try:
                return await _bridge_async_ask(prompt, mode="fast", **params)
            except Exception:
                return ""

    def get_ai_response_json(self, prompt: str, mode: str = "fast") -> Dict[str, Any]:
        """Một số chỗ cần JSON; parse mềm."""
        txt = self.get_ai_response(prompt, mode)
        try:
            return json.loads(txt)
        except Exception:
            return {}
    def health_providers(self) -> Dict[str, Any]:
        """
        Trả health chi tiết cho các provider dùng ở dự án.
        """
        return {
            "gpt5": _gpt5_ping(),
            "ollama": _ollama_ping(),
        }
    # ====== NEW: generate unified diff patch ======
    def generate_patch(self, plan_item: PlanItem, context: str = "") -> str:
        """
        Generate unified diff via provider. Providers:
        - OPENAI (default, env OPENAI_API_KEY)
        - LOCAL_HTTP (OpenAI-compatible endpoint via env LOCAL_MODEL_ENDPOINT)
        Returns a string that starts with '--- a/..' and '+++ b/..'.
        """
        provider = os.getenv("PATCH_PROVIDER", "OPENAI").upper()
        model = os.getenv("PATCH_MODEL", "gpt-4o-mini")
        system = (
            "You are a senior software engineer. Return ONLY a unified diff patch."
            " It must include file headers (--- a/... +++ b/...) and valid hunks."
        )
        # Build lightweight file context if not provided
        if not context:
            context = self._build_file_context(plan_item)

        user = {
            "instruction": "Generate a minimal patch to implement the plan item.",
            "plan_item": plan_item.to_dict(),
            "diff_hint": plan_item.diff_hint or "",
            "file_context": context,
            "tests_to_run": plan_item.tests_to_run,
            "constraints": [
                "Output must be plain text unified diff",
                "No markdown code fences",
                "Keep patch minimal and safe",
            ],
        }

        if provider == "LOCAL_HTTP":
            endpoint = os.getenv("LOCAL_MODEL_ENDPOINT", "http://127.0.0.1:8000/v1/chat/completions")
            try:
                r = httpx.post(
                    endpoint,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": json.dumps(user)},
                        ],
                        "temperature": 0.2,
                    },
                    timeout=60,
                )
                r.raise_for_status()
                data = r.json()
                txt = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._ensure_unified_diff(txt)
            except Exception:
                return ""

        # Default: OPENAI
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY", "")
            if not openai.api_key:
                return ""
            resp = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(user)},
                ],
                temperature=0.2,
            )
            txt = resp.choices[0].message.content or ""
            return self._ensure_unified_diff(txt)
        except Exception:
            return ""

    @staticmethod
    def _ensure_unified_diff(text: str) -> str:
        t = (text or "").strip()
        # Strip markdown fences if present
        if t.startswith("```") and t.endswith("```"):
            t = t.strip("`").strip()
            if t.lower().startswith("json") or t.lower().startswith("diff"):
                t = t.split("\n", 1)[1] if "\n" in t else t
        if "--- a/" in t and "+++ b/" in t:
            return t
        return ""

    @staticmethod
    def _build_file_context(item: PlanItem, max_lines: int = 80) -> str:
        """Read up to N lines of the target file as context for patch synthesis."""
        path = (item.target or "").strip()
        if not path:
            return ""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return ""
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
            head = lines[:max_lines]
            tail = lines[-max_lines:] if len(lines) > max_lines else []
            snippet = "\n".join(head + (["\n..."] if tail and head != lines else []) + tail)
            return f"FILE: {path}\n{snippet}"
        except Exception:
            return ""
