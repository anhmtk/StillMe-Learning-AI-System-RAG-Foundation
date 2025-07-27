#!/usr/bin/env python3
"""
agent_dev.py - AI DevOps Agent for Automated Testing and Fixing
Phiên bản SafeMode: bổ sung sandbox execution (Docker), diff-check, JSON Schema validation,
tích hợp Git nâng cao, lập kế hoạch đa bước, tự phản chiếu,
+ Detect xung đột logic giữa các module,
+ Tự động merge code fix vào framework.py nếu mọi test pass.
"""

import json
import logging
import re
import subprocess
import sys
import difflib # Để tạo diff
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any, Callable, Union
import openai
import ollama
from cryptography.fernet import Fernet # Lưu ý: Fernet key cần được quản lý an toàn trong môi trường production
import os 
from collections import defaultdict
import shutil # Thêm để xóa thư mục .git
from dataclasses import dataclass
from jsonschema import validate, ValidationError # Thêm để validate JSON Schema

# --- Constants ---
BACKUP_DIR = Path("backup_legacy") # Thư mục lưu trữ các bản backup file trước khi sửa đổi
MEMORY_FILE = Path("agent_memory.json") # File database ghi nhớ các lỗi và cách fix
LOG_FILE = Path("agent_dev.log") # File log của Agent
FRAMEWORK_FILE = Path("framework.py") # File chính của StillMe Framework
FRAMEWORK_BACKUP = Path("framework_backup.py") # Bản backup của framework.py
MODULES_DIR = Path("modules") # Thư mục chứa các module của StillMe Framework

# Git Constants
AGENT_WORKING_BRANCH_PREFIX = "agent-fix-" # Tiền tố cho branch mà Agent sẽ làm việc trên đó
MAIN_BRANCH = "main" # Tên branch chính của dự án

# AI Model Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434") # URL mặc định của Ollama
DEFAULT_AI_MODEL_CODE = "deepseek-coder:6.7b" # Model ưu tiên cho tác vụ sinh code/sửa code
DEFAULT_AI_MODEL_REASONING = "gpt-4o" # Model ưu tiên cho tác vụ suy luận/lập kế hoạch/đánh giá

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO, # Mặc định là INFO, có thể thay đổi thành DEBUG để xem chi tiết hơn
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'), # Ghi log vào file
        logging.StreamHandler(sys.stdout) # Hiển thị log ra console
    ]
)
logger = logging.getLogger("AgentDev-SafeMode")

# --- JSON SCHEMA for AI Plan Validation ---
# Định nghĩa schema cho kế hoạch hành động từ AI
# Điều này đảm bảo AI trả về dữ liệu có cấu trúc và đáng tin cậy
AI_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string", "description": "Phân tích nguyên nhân gốc rễ của lỗi."},
        "fix_strategy_summary": {"type": "string", "description": "Tóm tắt chiến lược sửa lỗi tổng thể."},
        "plan": {
            "type": "array",
            "description": "Danh sách các bước hành động cụ thể.",
            "items": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Hành động cần thực hiện (ví dụ: modify_code, run_pylint, add_test, run_tests, review_diff, check_imports, install_deps).",
                        "enum": ["modify_code", "run_pylint", "add_test", "run_tests", "review_diff", "check_imports", "install_deps"] # Các hành động được hỗ trợ
                    },
                    "file": {"type": "string", "description": "Đường dẫn tương đối đến file bị ảnh hưởng (nếu có)."},
                    "description": {"type": "string", "description": "Mô tả chi tiết bước hành động này."}
                },
                "required": ["action", "description"] # action và description là bắt buộc
            }
        }
    },
    "required": ["root_cause", "fix_strategy_summary", "plan"]
}

# --- Custom Exceptions ---
class AgentError(Exception):
    """Base exception for AgentDev errors."""
    pass

class EthicsViolation(AgentError):
    """Lỗi vi phạm nguyên tắc đạo đức."""
    pass

class StillMeFrameworkError(AgentError):
    """Lỗi liên quan đến StillMe Framework."""
    pass

class GitError(AgentError):
    """Lỗi liên quan đến các thao tác Git."""
    pass

class SandboxError(AgentError):
    """Lỗi liên quan đến môi trường sandbox."""
    pass

# --- Agent Context for State Management ---
# Sử dụng dataclass để quản lý trạng thái của Agent trong suốt quá trình hoạt động
@dataclass
class AgentContext:
    """Stores current context and state for the Agent's operations."""
    problem_file: Optional[Path] = None # File đang gặp vấn đề
    error_log: Optional[str] = None # Log lỗi đầy đủ
    original_code_before_fix: Optional[str] = None # Code gốc trước khi sửa
    error_type: Optional[str] = None # Loại lỗi (ví dụ: NameError, ImportError)
    error_msg: Optional[str] = None # Thông điệp lỗi
    root_cause: Optional[str] = None # Nguyên nhân gốc rễ của lỗi (do AI phân tích)
    fix_strategy: Optional[str] = None # Chiến lược sửa lỗi tổng thể (do AI đề xuất)
    ai_plan: Optional[List[Dict[str, Any]]] = None # Kế hoạch hành động đa bước từ AI
    current_attempt: int = 0 # Số lần thử hiện tại
    current_branch: Optional[str] = None # Tên branch Git hiện tại mà Agent đang làm việc

# --- Simplified StillMe Framework components for EthicsChecker integration ---
# Để tránh phụ thuộc vòng tròn hoặc cần cài đặt toàn bộ framework StillMe
# chúng ta sẽ định nghĩa lại một số thành phần cần thiết ở đây.
class StillMeFramework:
    """A simplified framework to host EthicsChecker."""
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ethics = EthicsChecker(level=self.config.get("security_level", "medium"))
        logger.info("StillMeFramework (simplified) initialized for ethics checks.")

class EthicsChecker:
    """Kiểm tra nội dung theo nguyên tắc đạo đức với nhiều mức độ"""
    def __init__(self, level="medium"):
        self.level = level
        self.rules = {
            "low": [
                self._check_explicit_content
            ],
            "medium": [
                self._check_explicit_content,
                self._check_hate_speech,
                self._check_length # Ví dụ: kiểm tra độ dài code/comment
            ],
            "high": [
                self._check_explicit_content,
                self._check_hate_speech,
                self._check_length,
                self._check_pii_leakage # Kiểm tra rò rỉ thông tin cá nhân
            ]
        }.get(level, [])
        logger.info(f"EthicsChecker initialized with level: {self.level}")
        
    def validate(self, content: str) -> bool:
        """Kiểm tra nội dung text"""
        for rule in self.rules:
            if not rule(content):
                logger.warning(f"Ethics violation: {rule.__name__} for content.")
                return False
        return True
        
    def validate_module_code(self, code_content: str) -> bool:
        """Kiểm tra code content theo nguyên tắc đạo đức"""
        return self.validate(code_content)
            
    # --- Ethics Rules (Example Stubs) ---
    def _check_explicit_content(self, content: str) -> bool:
        """Stub: Kiểm tra nội dung tục tĩu/nhạy cảm"""
        # Trong thực tế, cần tích hợp mô hình NLP chuyên biệt hoặc danh sách từ khóa
        # Ví dụ: kiểm tra từ khóa "bad_word"
        return "bad_word" not in content.lower() 
    
    def _check_hate_speech(self, content: str) -> bool:
        """Stub: Kiểm tra ngôn ngữ thù địch"""
        # Ví dụ: kiểm tra từ khóa "hate_speech_term"
        return "hate_speech_term" not in content.lower() 
        
    def _check_length(self, content: str) -> bool:
        """Stub: Kiểm tra độ dài (ví dụ: không quá ngắn/dài bất thường)"""
        # Code quá ngắn có thể là code độc hại, quá dài có thể là spam
        return 10 < len(content) < 5000 
        
    def _check_pii_leakage(self, content: str) -> bool:
        """Stub: Kiểm tra rò rỉ thông tin cá nhân (PII)"""
        # Trong thực tế, cần dùng regex phức tạp hoặc mô hình NLP
        # Ví dụ: kiểm tra số điện thoại hoặc email
        return not (re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', content) or # Phone number
                    re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)) # Email

# --- Core Components ---
class AIManager:
    """Handles AI model interactions for code fixes and advanced reasoning"""
    
    def __init__(self):
        # Key chỉ được tạo ra mỗi lần khởi tạo, không lưu trữ (chỉ cho mục đích demo)
        # Trong production, cần quản lý key an toàn hơn (ví dụ: biến môi trường, Key Vault)
        self.encryption_key = Fernet.generate_key() 
        self.cipher = Fernet(self.encryption_key)
        self.ollama_base_url = OLLAMA_API_URL
        openai.api_key = OPENAI_API_KEY
        
    def _call_ollama(self, model: str, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Call Ollama model."""
        try:
            client = ollama.Client(host=self.ollama_base_url)
            response = client.generate(
                model=model,
                prompt=prompt,
                options={"temperature": temperature}
            )
            return response["response"]
        except Exception as e:
            logger.warning(f"Ollama call failed for {model}: {str(e)}")
            return None
    
    def _call_openai(self, model: str, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Call OpenAI model."""
        if not openai.api_key:
            logger.error("OpenAI API key is not set. Cannot call OpenAI models.")
            return None
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI call failed for {model}: {str(e)}")
            return None
            
    def get_ai_response(self, prompt: str, preferred_model: str = DEFAULT_AI_MODEL_REASONING) -> Optional[str]:
        """Get AI response with fallback logic for general tasks and reasoning."""
        response = None
        if preferred_model == DEFAULT_AI_MODEL_REASONING: # Thường là GPT-4o
            response = self._call_openai(preferred_model, prompt)
            if not response: # Fallback sang model code nếu model reasoning thất bại
                logger.warning(f"Preferred model {preferred_model} failed. Falling back to {DEFAULT_AI_MODEL_CODE}.")
                response = self._call_ollama(DEFAULT_AI_MODEL_CODE, prompt)
        elif preferred_model == DEFAULT_AI_MODEL_CODE: # Thường là DeepSeek-coder
            response = self._call_ollama(preferred_model, prompt)
            if not response: # Fallback sang model reasoning nếu model code thất bại
                logger.warning(f"Preferred model {preferred_model} failed. Falling back to {DEFAULT_AI_MODEL_REASONING}.")
                response = self._call_openai(DEFAULT_AI_MODEL_REASONING, prompt)
        
        if not response:
            logger.error(f"Failed to get AI response from any model for prompt: {prompt[:100]}...")
        return response

    def get_ai_fix(self, prompt: str) -> Optional[str]:
        """Get code fix from AI with fallback logic, specifically for code generation."""
        # Ưu tiên các model code-focused
        response = self._call_ollama(DEFAULT_AI_MODEL_CODE, prompt, temperature=0.2)
        model_used = DEFAULT_AI_MODEL_CODE
        
        if not response or "sorry" in response.lower() or "I cannot help" in response.lower():
            logger.warning(f"Code model {DEFAULT_AI_MODEL_CODE} failed or gave unhelpful response. Falling back to {DEFAULT_AI_MODEL_REASONING}.")
            response = self._call_openai(DEFAULT_AI_MODEL_REASONING, prompt, temperature=0.2)
            model_used = DEFAULT_AI_MODEL_REASONING
        
        if response:
            logger.info(f"AI fix generated by {model_used}")
            return response
        return None

class BugMemory:
    """Manages bug memory database with richer context and potential for semantic search."""
    
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self._ensure_memory_file()
        
    def _ensure_memory_file(self):
        if not self.memory_file.exists():
            with open(self.memory_file, "w", encoding='utf-8') as f:
                json.dump({"bugs": []}, f)
    
    def add_bug(self, context: AgentContext, fix_code: str):
        """Record a bug and its fix with more context from AgentContext."""
        with open(self.memory_file, "r+", encoding='utf-8') as f:
            f.seek(0) # Đảm bảo đọc từ đầu file
            data = json.load(f)
            data["bugs"].append({
                "timestamp": str(datetime.now()),
                "error_type": context.error_type,
                "error_msg": context.error_msg,
                "root_cause_analysis": context.root_cause,
                "fix_strategy_suggested": context.fix_strategy,
                "original_code": context.original_code_before_fix,
                "fixed_code": fix_code,
                "file_path": str(context.problem_file),
                "ai_plan_executed": context.ai_plan # Lưu lại kế hoạch đã thực thi
            })
            f.seek(0) # Đảm bảo ghi từ đầu file
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate() # Cắt bỏ phần còn lại nếu file cũ lớn hơn
        logger.info(f"Bug '{context.error_type}' in {context.problem_file.name} recorded in memory.")
            
    def get_fix(self, context: AgentContext) -> Optional[str]:
        """Retrieve a fix from memory, potentially using semantic search (stub)."""
        with open(self.memory_file, "r", encoding='utf-8') as f:
            data = json.load(f)
            
            # Simple exact match first based on error type and message snippet
            for bug in data["bugs"]:
                if bug["error_type"] == context.error_type and \
                   context.error_msg[:50] in bug["error_msg"]:
                    logger.info(f"Found exact match fix in memory for {context.error_type}.")
                    return bug["fixed_code"]
            
            # TODO: Implement semantic search using LLM if no exact match
            # This would involve:
            # 1. Prompting an LLM to compare current error/code/context with stored bugs' error/code/context
            # 2. Asking LLM if a stored fix is applicable or can be adapted
            logger.info("No exact fix found in memory. Semantic search (if implemented) would run here.")
            return None

class Planner:
    """Analyzes errors, plans fix strategies, and leverages AI for deeper insights and multi-step plans."""
    
    def __init__(self, ai_manager: AIManager):
        self.ai = ai_manager
        
    def analyze_and_plan(self, context: AgentContext) -> AgentContext:
        """Identify error, root cause, and generate a multi-step fix plan using AI."""
        error_log = context.error_log
        file_path = context.problem_file
        
        # Bước 1: Phân tích lỗi cơ bản bằng regex (nhanh)
        error_type = "UnknownError"
        error_msg = "Unknown error"
        
        # Cải thiện regex để bắt dòng và cột nếu có
        traceback_lines = error_log.splitlines()
        for line in reversed(traceback_lines): # Tìm từ dưới lên để lấy lỗi cuối cùng
            match_file_line = re.search(r'File "([^"]+)", line (\d+)', line)
            if match_file_line:
                file_path_detected = match_file_line.group(1)
                line_info = match_file_line.group(2)
                # Ưu tiên file_path được truyền vào nếu nó khớp với file_path_detected
                # Hoặc cập nhật file_path nếu nó là "unknown"
                if file_path == Path("unknown") or Path(file_path_detected).name == file_path.name:
                    file_path = Path(file_path_detected)
                break
        
        # Tìm loại lỗi và thông điệp lỗi
        error_line_match = re.search(r'([A-Za-z]+Error): (.*)', error_log.splitlines()[-1])
        if error_line_match:
            error_type = error_line_match.group(1)
            error_msg = error_line_match.group(2)
        else:
            error_msg = traceback_lines[-1] # Lấy dòng cuối cùng nếu không khớp pattern
        
        context.error_type = error_type
        context.error_msg = error_msg
        context.problem_file = file_path # Cập nhật lại file_path nếu tìm thấy từ log
        logger.info(f"Basic error analysis: Type={error_type}, Msg='{error_msg}', File={file_path}")

        # Bước 2: Phân tích nguyên nhân gốc rễ và lập kế hoạch đa bước bằng AI
        full_code = file_path.read_text(encoding='utf-8') if file_path.exists() else "Code not available."
        
        prompt = f"""
You are an expert AI DevOps Agent. Your task is to analyze a Python error and create a detailed, multi-step plan to fix it.
The plan should be a list of actionable steps, each step specifying an "action" (e.g., "modify_code", "run_pylint", "add_test", "run_tests", "review_diff", "check_imports", "install_deps") and relevant "details".
Prioritize fixing the root cause and ensuring code quality.

Error Log:
```
{error_log}
```

File Path: {file_path}
Code Content:
```python
{full_code}
```

Provide your response in JSON format, with keys "root_cause", "fix_strategy_summary", and "plan".
Ensure the JSON strictly adheres to the following schema:
{json.dumps(AI_PLAN_SCHEMA, indent=2)}
"""
        ai_plan_json_str = self.ai.get_ai_response(prompt, preferred_model=DEFAULT_AI_MODEL_REASONING)
        
        if ai_plan_json_str:
            try:
                ai_response = json.loads(ai_plan_json_str)
                # Validate AI's response against the schema
                validate(instance=ai_response, schema=AI_PLAN_SCHEMA)
                
                context.root_cause = ai_response.get("root_cause", "AI analysis failed.")
                context.fix_strategy = ai_response.get("fix_strategy_summary", "No specific strategy suggested.")
                context.ai_plan = ai_response.get("plan", [])
                logger.info(f"AI Root Cause Analysis: {context.root_cause}")
                logger.info(f"AI Fix Strategy Summary: {context.fix_strategy}")
                logger.info(f"AI Plan (validated): {json.dumps(context.ai_plan, indent=2)}")
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"AI plan invalid or failed schema validation: {e}. Raw response: {ai_plan_json_str[:500]}...")
                context.root_cause = f"AI plan invalid: {e}" 
                context.fix_strategy = "Fallback to direct fix due to invalid AI plan."
                context.ai_plan = [{"action": "modify_code", "file": str(file_path), "description": "Attempt a direct fix as AI plan was invalid."}] # Kế hoạch mặc định
        else:
            logger.error("AI failed to generate a plan. Using default fix strategy.")
            context.root_cause = "AI analysis failed."
            context.fix_strategy = "Default fix strategy."
            context.ai_plan = [{"action": "modify_code", "file": str(file_path), "description": "Attempt a direct fix."}] # Kế hoạch mặc định

        return context

class SafeExecutor:
    """Executes fixes, manages Git operations, and applies changes with safety/ethics checks."""
    
    def __init__(self, ai: AIManager, memory: BugMemory, ethics_checker: EthicsChecker):
        self.ai = ai
        self.memory = memory
        self.ethics = ethics_checker
        self._ensure_framework_backup() # Đảm bảo backup framework ban đầu

    def _run_git_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Helper to run git commands."""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True # Raise exception for non-zero exit codes
            )
            logger.debug(f"Git command {' '.join(command)} output:\n{result.stdout.strip()}")
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command {' '.join(command)} failed: {e.stderr.strip()}")
            return False, e.stderr.strip()
        except FileNotFoundError:
            logger.error("Git command not found. Please ensure Git is installed and in your PATH.")
            return False, "Git not found."

    def run_command_in_docker_sandbox(self, command: List[str], mount_path: Path = Path("."), timeout: int = 60, docker_image: str = "stillme-dev-env") -> Tuple[bool, str]:
        """
        Runs a command inside a Docker container sandbox.
        The current working directory is mounted into the container.
        """
        try:
            # Đảm bảo không dùng python.exe trong Linux container
            if len(command) > 0 and ("python.exe" in command[0] or "python" in command[0].lower()):
                command[0] = "python3"

            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{mount_path.resolve()}:/app",
                "-w", "/app",
                docker_image
            ] + command

            logger.info(f"[Docker Sandbox] Running: {' '.join(docker_cmd)}")

            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            return (result.returncode == 0), result.stdout + result.stderr
        except Exception as e:
            logger.error(f"Sandbox execution failed: {str(e)}")
            return False, str(e)


    def git_init_and_branch(self, context: AgentContext) -> bool:
        """Initialize git repo if not exists and create/checkout agent branch."""
        if not (Path.cwd() / ".git").exists():
            logger.info("Git repo not found. Initializing...")
            success, msg = self._run_git_command(["init"])
            if not success:
                logger.error(f"Failed to initialize Git repo: {msg}")
                return False
            # Thêm tất cả các file hiện có vào git và commit ban đầu
            self._run_git_command(["add", "."])
            self._run_git_command(["commit", "-m", "Initial commit by AgentDev"])
            logger.info("Initial Git commit created.")
        
        # Chắc chắn đang ở branch chính trước khi tạo branch mới
        success, current_branch = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        if success and current_branch != MAIN_BRANCH:
            logger.info(f"Not on {MAIN_BRANCH}. Checking out {MAIN_BRANCH}...")
            success, msg = self._run_git_command(["checkout", MAIN_BRANCH])
            if not success:
                logger.error(f"Failed to checkout {MAIN_BRANCH}: {msg}")
                return False
        
        # Tạo branch mới cho lần thử hiện tại
        branch_name = f"{AGENT_WORKING_BRANCH_PREFIX}{datetime.now().strftime('%Y%m%d%H%M%S')}-{context.current_attempt}"
        success, msg = self._run_git_command(["checkout", "-b", branch_name])
        if not success:
            logger.error(f"Failed to create and checkout branch {branch_name}: {msg}")
            return False
        
        context.current_branch = branch_name
        logger.info(f"Checked out to new branch: {branch_name}")
        return True

    def git_commit_changes(self, message: str):
        """Commit all staged changes to the current branch."""
        success, _ = self._run_git_command(["add", "."])
        if not success:
            logger.error("Failed to stage changes for commit.")
            return False
        success, _ = self._run_git_command(["commit", "-m", message])
        if success:
            logger.info(f"Changes committed: '{message}'")
        else:
            logger.error(f"Failed to commit changes: '{message}'")
        return success

    def git_revert_current_branch(self, context: AgentContext):
        """Revert all changes in the current branch and switch back to main."""
        logger.warning(f"Reverting all changes on branch {context.current_branch} and deleting it...")
        # Đảm bảo không có thay đổi chưa commit trên branch hiện tại
        self._run_git_command(["reset", "--hard", "HEAD"])
        self._run_git_command(["clean", "-df"]) # Xóa các file không được theo dõi
        
        # Chuyển về branch chính
        success, msg = self._run_git_command(["checkout", MAIN_BRANCH])
        if not success:
            logger.error(f"Failed to checkout {MAIN_BRANCH} for revert: {msg}")
            return
        
        # Xóa branch lỗi
        success, msg = self._run_git_command(["branch", "-D", context.current_branch])
        if success:
            logger.info(f"Branch {context.current_branch} deleted.")
        else:
            logger.error(f"Failed to delete branch {context.current_branch}: {msg}")
        
        logger.info("Changes reverted and branch cleaned up.")

    def _ensure_framework_backup(self):
        """Create framework backup if doesn't exist"""
        if not FRAMEWORK_BACKUP.exists() and FRAMEWORK_FILE.exists():
            FRAMEWORK_BACKUP.write_text(FRAMEWORK_FILE.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info("Initial backup of framework.py created.")
        
    def _backup_file(self, file_path: Path):
        """Create backup of a file before modification"""
        BACKUP_DIR.mkdir(exist_ok=True)
        backup_path = BACKUP_DIR / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"
        try:
            backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
            logger.info(f"Created backup at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path.name}: {str(e)}")

    def ensure_framework_integrity(self):
        """Verify framework.py hasn't been corrupted and restore if needed."""
        if FRAMEWORK_FILE.exists():
            try:
                with open(FRAMEWORK_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    compile(content, FRAMEWORK_FILE.name, 'exec') # Kiểm tra cú pháp
            except (SyntaxError, ValueError) as e:
                logger.warning(f"Framework.py is corrupted or has syntax error ({e})! Restoring from backup...")
                if FRAMEWORK_BACKUP.exists():
                    FRAMEWORK_FILE.write_text(FRAMEWORK_BACKUP.read_text(encoding='utf-8'), encoding='utf-8')
                    logger.info("Framework.py restored from backup.")
                else:
                    logger.critical("No backup available to restore framework.py! Framework might be unrecoverable.")
                    raise StillMeFrameworkError("Framework.py corrupted and no backup available.")
            except Exception as e:
                logger.error(f"Unexpected error checking framework.py integrity: {str(e)}")
        else:
            logger.warning("Framework.py does not exist. Cannot check integrity.")
    
    def apply_code_change(self, file_path: Path, new_code_content: str, commit_message: str) -> bool:
        """Applies a code change to a file, performs ethics check, and commits."""
        self._backup_file(file_path) # Tạo backup trước khi sửa đổi
        original_code = file_path.read_text(encoding='utf-8') if file_path.exists() else ""

        # Bước 1: Kiểm tra đạo đức của code mới
        if not self.ethics.validate_module_code(new_code_content):
            logger.error(f"Ethics violation detected in proposed code change for {file_path}. Aborting.")
            raise EthicsViolation(f"Ethics violation in code change for {file_path.name}")

        # Bước 2: Áp dụng thay đổi (ghi đè)
        try:
            # TODO: Thay thế bằng apply_patch_safely nếu muốn granular control hơn
            # difflib.unified_diff có thể dùng để tạo patch, nhưng áp dụng patch phức tạp hơn
            # Ví dụ: from patch import fromfile, apply_patch
            # diff = difflib.unified_diff(original_code.splitlines(), new_code_content.splitlines(), lineterm='')
            # with open(f"{file_path}.patch", "w") as f: f.write('\n'.join(diff))
            # apply_patch(f"{file_path}", f"{file_path}.patch")
            
            file_path.write_text(new_code_content, encoding='utf-8')
            logger.info(f"Successfully applied code change to {file_path}")
            # Bước 3: Commit thay đổi
            self.git_commit_changes(commit_message)
            return True
        except Exception as e:
            logger.error(f"Failed to write code change to {file_path}: {str(e)}")
            return False

    def execute_plan_step(self, step: Dict[str, Any], context: AgentContext) -> bool:
        """Executes a single step from the AI-generated plan."""
        action = step.get("action")
        file = Path(step.get("file")) if step.get("file") else None # File có thể không có nếu action là run_tests
        description = step.get("description", "No description provided.")

        logger.info(f"Executing plan step: {action} - {description} (File: {file.name if file else 'N/A'})")

        if action == "modify_code":
            if not file or not file.exists():
                logger.error(f"File not specified or does not exist for 'modify_code' action: {file}")
                return False
            current_code = file.read_text(encoding='utf-8')
            prompt = f"""
You are an expert Python developer. Your task is to modify the provided code according to the following description:
Description: {description}
Error Type: {context.error_type}
Error Message: {context.error_msg}
Root Cause: {context.root_cause}
Fix Strategy: {context.fix_strategy}

Provide ONLY the complete, corrected Python code block for {file.name}. Do NOT include any explanations or extra text outside the code block.
Ensure the code is clean, follows best practices, and includes necessary imports.

Current code of {file.name}:
```python
{current_code}
```
"""
            ai_generated_code = self.ai.get_ai_fix(prompt)
            if ai_generated_code:
                # Extract just the code block from AI response
                code_match = re.search(r"```python\n(.*?)\n```", ai_generated_code, re.DOTALL)
                if code_match:
                    clean_code = code_match.group(1)
                else:
                    logger.warning("AI response didn't contain a valid code block. Attempting to use full response as code.")
                    clean_code = ai_generated_code
                
                return self.apply_code_change(file, clean_code, f"Plan Step: {description} for {file.name}")
            else:
                logger.error(f"Failed to generate code for action '{action}'.")
                return False

        elif action == "run_pylint":
            if file:
                success, output = Critic(self.ethics).run_code_quality_checks(file, self) # Truyền self (Executor) để Critic có thể dùng sandbox
                if not success:
                    logger.warning(f"Pylint issues detected in {file}. Output:\n{output}")
                    # TODO: Agent có thể tự động yêu cầu AI fix lại code nếu Pylint thất bại
                return success
            else:
                logger.error("File not specified for 'run_pylint' action.")
                return False

        elif action == "add_test":
            # TODO: Triển khai logic để AI tạo test mới và thêm vào thư mục tests
            logger.warning(f"Action '{action}' not fully implemented. Skipping.")
            return True # Tạm thời coi là thành công để không chặn luồng

        elif action == "run_tests":
            # Gọi Critic để chạy test trong sandbox
            return Critic(self.ethics).run_tests(self)[0] # Truyền self (Executor)

        elif action == "review_diff":
            # TODO: Triển khai logic để AI tự review diff hoặc hiển thị diff cho người dùng
            logger.info("AI is reviewing changes (conceptual step).")
            # Có thể gọi AI để phân tích diff và đưa ra nhận xét
            # diff_output = self._run_git_command(["diff", "HEAD^", "HEAD"])[1]
            # ai_review_prompt = f"Review the following code diff for quality and potential issues:\n{diff_output}"
            # ai_review = self.ai.get_ai_response(ai_review_prompt)
            # logger.info(f"AI Diff Review: {ai_review}")
            return True # Tạm thời coi là thành công

        elif action == "check_imports":
            # TODO: Implement logic to check and add missing imports
            logger.warning(f"Action '{action}' not fully implemented. Skipping.")
            return True
        
        elif action == "install_deps":
            # TODO: Implement logic to install dependencies (e.g., pip install -r requirements.txt)
            logger.warning(f"Action '{action}' not fully implemented. Skipping.")
            return True

        else:
            logger.error(f"Unknown action in AI plan: {action}")
            return False

    def merge_modules_into_framework(self):
        """
        Gộp tất cả code từ các module trong thư mục 'modules' vào framework.py.
        Sử dụng AI để đảm bảo cấu trúc sạch và không trùng lặp import.
        """
        logger.info("Merging all modules into framework.py...")
        
        # Backup framework.py hiện tại trước khi merge
        if FRAMEWORK_FILE.exists():
            backup_code = FRAMEWORK_FILE.read_text(encoding="utf-8")
            BACKUP_DIR.mkdir(exist_ok=True)
            (BACKUP_DIR / f"framework_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py").write_text(backup_code, encoding='utf-8')
            logger.info(f"Backed up framework.py to {BACKUP_DIR / f'framework_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py'}")

        all_module_code = []
        # Đọc nội dung của từng module
        for module_file in MODULES_DIR.glob("*.py"):
            all_module_code.append(f"\n# --- Start Module: {module_file.name} ---\n" + module_file.read_text(encoding="utf-8") + f"\n# --- End Module: {module_file.name} ---\n")

        current_framework_code = FRAMEWORK_FILE.read_text(encoding='utf-8') if FRAMEWORK_FILE.exists() else ""

        prompt = f"""
You are an expert Python architect. Your task is to merge the provided Python module code into the existing framework.py file.
Ensure the merged code is clean, well-structured, avoids duplicate imports, and maintains overall code quality.
Place the merged module code logically within the framework (e.g., after initial imports and before the main application class).

Current framework.py content:
```python
{current_framework_code}
```

Module codes to merge:
```python
{''.join(all_module_code)}
```
Provide ONLY the complete, merged Python code for framework.py. Do NOT include any explanations or extra text outside the code block.
"""
        merged_result = self.ai.get_ai_fix(prompt) # Sử dụng get_ai_fix vì đây là tác vụ sinh code

        if merged_result:
            code_match = re.search(r"```python\n(.*?)\n```", merged_result, re.DOTALL)
            final_code = code_match.group(1) if code_match else merged_result # Lấy code từ block hoặc toàn bộ response

            # Kiểm tra đạo đức của code framework đã merge
            if not self.ethics.validate_module_code(final_code):
                logger.error("Ethics violation detected in AI-generated merged framework code. Aborting merge.")
                raise EthicsViolation("Ethics violation in merged framework code.")
            
            # Ghi code đã merge vào framework.py
            try:
                FRAMEWORK_FILE.write_text(final_code, encoding="utf-8")
                logger.info("Framework merged successfully with AI assistance.")
                self.git_commit_changes("Feat: AI merged modules into framework.py")
                return True
            except Exception as e:
                logger.error(f"Failed to write merged framework code: {str(e)}")
                return False
        else:
            logger.error("AI failed to generate merged framework code.")
            return False

class Critic:
    """Runs tests, framework validation, and evaluates code quality and fix quality."""
    
    def __init__(self, ethics_checker: EthicsChecker):
        self.ethics = ethics_checker

    def run_tests(self, executor: SafeExecutor) -> Tuple[bool, str]:
        """Run pytest in a sandbox and return results."""
        logger.info("Running unit tests with pytest in sandbox...")
        # Lệnh chạy pytest trong Docker sandbox
        # Cần đảm bảo pytest và các dependencies của dự án được cài đặt trong Docker image
        success, output = executor.run_command_in_docker_sandbox(
            command=["pytest", "-v", str(MODULES_DIR)], # Chạy test trong thư mục modules
            mount_path=Path("."), # Mount thư mục gốc của dự án
            timeout=120 # Tăng timeout cho test
        )
        if not success:
            logger.warning(f"Tests failed in sandbox. Output:\n{output}")
        else:
            logger.info("All tests passed in sandbox.")
        return success, output
            
    def run_framework(self, executor: SafeExecutor) -> Tuple[bool, str]:
        """Run framework.py in a sandbox to verify it works and capture output/errors."""
        if not FRAMEWORK_FILE.exists():
            logger.error(f"Framework file not found: {FRAMEWORK_FILE}")
            return False, f"Framework file not found: {FRAMEWORK_FILE}"
            
        logger.info(f"Running framework file: {FRAMEWORK_FILE} in sandbox...")
        # Lệnh chạy framework.py trong Docker sandbox
        success, output = executor.run_command_in_docker_sandbox(
            command=[sys.executable, str(FRAMEWORK_FILE)],
            mount_path=Path("."),
            timeout=60 # Timeout cho framework run
        )
        if not success:
            logger.warning(f"Framework execution failed in sandbox. Output:\n{output}")
        else:
            logger.info("Framework execution passed in sandbox.")
        return success, output

    def run_code_quality_checks(self, file_path: Path, executor: SafeExecutor) -> Tuple[bool, str]:
        """Run Pylint on a specific file in a sandbox and return result."""
        logger.info(f"Running code quality checks (Pylint) on {file_path} in sandbox...")
        # Lệnh chạy pylint trong Docker sandbox
        success, output = executor.run_command_in_docker_sandbox(
            command=[sys.executable, "-m", "pylint", str(file_path)],
            mount_path=Path("."),
            timeout=60
        )
        # Pylint return code 0 for no issues, 1 for fatal error, 2 for error, 4 for warning, 8 for refactor, 16 for convention
        # We consider it "passed" if no errors (code < 2)
        # Pylint output thường có dòng "Your code has been rated at X.XX/10"
        quality_ok = success and ("Your code has been rated at 10.00/10" in output or "no score" in output) # Heuristic for success
        if not quality_ok:
            logger.warning(f"Pylint issues detected in {file_path}:\n{output}")
        else:
            logger.info(f"Pylint passed for {file_path}.")
        return quality_ok, output

    def evaluate_fix_quality_with_ai(self, original_code: str, fixed_code: str, error_log: str, ai_manager: AIManager) -> Dict[str, Any]:
        """Evaluate the quality of the fix using AI."""
        logger.info("Evaluating fix quality with AI...")
        prompt = f"""
I applied a fix to a Python code. I need you to evaluate the quality of the fix based on the original code, the error log, and the fixed code.
Consider factors like: correctness, readability, adherence to best practices, potential side effects, and if it truly addresses the root cause.
Provide a score from 1-10 for overall quality and a brief explanation for your score.
Return your evaluation in JSON format with keys: "score", "explanation", "suggestions_for_improvement".

Original Code:
```python
{original_code}
```

Error Log:
```
{error_log}
```

Fixed Code:
```python
{fixed_code}
```
"""
        ai_evaluation_json = ai_manager.get_ai_response(prompt, preferred_model=DEFAULT_AI_MODEL_REASONING)
        
        if ai_evaluation_json:
            try:
                ai_evaluation = json.loads(ai_evaluation_json)
                # TODO: Validate AI evaluation JSON against a schema if needed
                logger.info(f"AI Fix Evaluation (Score: {ai_evaluation.get('score', 'N/A')}/10): {ai_evaluation.get('explanation', '')}")
                return ai_evaluation
            except json.JSONDecodeError:
                logger.warning(f"AI evaluation not in valid JSON format: {ai_evaluation_json[:200]}...")
        return {"score": 0, "explanation": "AI evaluation failed or invalid format.", "suggestions_for_improvement": []}

    def detect_module_conflicts(self, ai_manager: AIManager) -> List[str]:
        """
        Detects potential logical conflicts between modules using AI.
        This is a heuristic check, not a formal static analysis.
        """
        logger.info("Detecting module conflicts using AI...")
        conflict_warnings = []
        try:
            module_files = list(MODULES_DIR.glob("*.py"))
            if not module_files:
                logger.info("No modules found to check for conflicts.")
                return []

            module_contents = {}
            for f in module_files:
                module_contents[f.name] = f.read_text(encoding='utf-8')

            prompt = f"""
Analyze the following Python modules for potential logical conflicts.
Look for issues like:
-   Duplicate function or class names that would cause runtime errors.
-   Variables with the same name used globally across modules that might unintentionally overwrite each other.
-   Circular import patterns that could lead to issues.
-   Any other logical inconsistencies or potential runtime conflicts.

Provide a JSON array of conflict descriptions. If no conflicts are found, return an empty array.
Example:
[
  "Duplicate function 'process_data' found in 'module_a.py' and 'module_b.py'.",
  "Global variable 'config_param' is defined in both 'settings.py' and 'main_app.py', leading to potential overwrite issues."
]

Modules and their content:
{json.dumps(module_contents, indent=2)}
"""
            ai_result_str = ai_manager.get_ai_response(prompt, preferred_model=DEFAULT_AI_MODEL_REASONING)
            if ai_result_str:
                try:
                    ai_result = json.loads(ai_result_str)
                    if isinstance(ai_result, list):
                        conflict_warnings = ai_result
                        for warning in conflict_warnings:
                            logger.warning(f"Module Conflict Detected: {warning}")
                    else:
                        logger.warning(f"AI returned non-list for conflicts: {ai_result_str[:200]}...")
                except json.JSONDecodeError:
                    logger.warning(f"AI conflict detection response not valid JSON: {ai_result_str[:200]}...")
            else:
                logger.warning("AI failed to provide conflict detection analysis.")
        except Exception as e:
            logger.error(f"Error detecting module conflicts: {str(e)}")
        return conflict_warnings

class AgentDev:
    """Main AI DevOps Agent class orchestrating the perceive-plan-act-learn cycle."""
    
    def __init__(self):
        # Khởi tạo StillMe Framework (simplified) để lấy EthicsChecker
        self.stillme_framework = StillMeFramework(config={"security_level": "high"})
        self.ethics_checker = self.stillme_framework.ethics

        self.ai = AIManager()
        self.memory = BugMemory()
        # Executor cần AIManager, BugMemory và EthicsChecker để thực thi an toàn
        self.executor = SafeExecutor(self.ai, self.memory, self.ethics_checker) 
        # Critic cần EthicsChecker và AIManager để đánh giá và phát hiện xung đột
        self.critic = Critic(self.ethics_checker) 
        
        self.context = AgentContext() # Sử dụng AgentContext để quản lý trạng thái của Agent

    def _self_heal_agent_components(self):
        """Checks and attempts to fix issues with agent's own dependencies/tools."""
        logger.info("Agent performing self-healing checks for its own dependencies...")
        
        # Helper function for installing packages
        def _install_package(package_name: str):
            try:
                subprocess.run([sys.executable, "-m", "pip", "show", package_name], check=True, capture_output=True)
                logger.info(f"{package_name} is installed.")
                return True
            except subprocess.CalledProcessError:
                logger.warning(f"{package_name} not found. Attempting to install {package_name}...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True, capture_output=True)
                    logger.info(f"{package_name} installed successfully.")
                    return True
                except Exception as e:
                    logger.error(f"Failed to install {package_name}: {str(e)}")
                    return False

        # Kiểm tra và cài đặt các dependencies cần thiết cho Agent
        _install_package("pylint")
        _install_package("pytest")
        _install_package("ollama")
        _install_package("openai")
        _install_package("cryptography")
        _install_package("jsonschema")

        # Kiểm tra Git
        success, _ = self.executor._run_git_command(["--version"])
        if not success:
            logger.critical("Git command not found. Please install Git manually. Agent cannot proceed.")
            sys.exit(1)
        
        # Kiểm tra Docker
        # Chạy một lệnh Docker đơn giản để kiểm tra xem Docker có chạy không
        success, _ = self.executor.run_command_in_docker_sandbox(["echo", "Docker is running"], docker_image="alpine", timeout=10)

        if not success:
            logger.critical("Docker is not running or not accessible. Please ensure Docker is installed and started. Agent cannot proceed in safe mode.")
            sys.exit(1)
        else:
            logger.info("Docker is running and accessible.")

        # TODO: Kiểm tra kết nối API của AI models (AIManager)
        # TODO: Kiểm tra quyền ghi/đọc file cho các thư mục (BACKUP_DIR, MEMORY_FILE, LOG_FILE)

    def main_loop(self, max_attempts=5):
        """Main execution loop for the agent."""
        logger.info("🚀 Starting AgentDev Main Loop in SafeMode")
        
        self._self_heal_agent_components() # Tự kiểm tra và sửa chữa các thành phần của Agent

        # Bước 0: Khởi tạo Git và chuyển sang branch làm việc của Agent
        # Mỗi lần thử sẽ tạo một branch mới để cô lập các thay đổi
        
        while self.context.current_attempt < max_attempts:
            self.context.current_attempt += 1
            logger.info(f"\n--- Attempt {self.context.current_attempt}/{max_attempts} ---")
            
            
            # Tắt cơ chế Git auto-reset vì gây xung đột
            git_ok = self.executor._run_git_command(["status"])
            if not git_ok[0]:
                logger.warning("Git not initialized or error detected, but skipping auto-checkout to avoid data loss.")


            # Bước 1: Chạy test và framework để nhận thức môi trường (Perceive)
            logger.info("Perceiving environment: Running tests and framework check in sandbox...")
            test_ok, test_log = self.critic.run_tests(self.executor) # Truyền executor cho critic
            framework_ok_status, framework_log = self.critic.run_framework(self.executor) # Truyền executor cho critic
            
            if test_ok and framework_ok_status:
                logger.info("All tests passed and Framework verification passed. Mission accomplished for this branch!")
                
                # Bước bổ sung: Phát hiện xung đột logic giữa các module
                conflicts = self.critic.detect_module_conflicts(self.ai)
                if conflicts:
                    logger.warning("Conflicts detected between modules. Attempting to resolve by merging with AI.")
                    # TODO: Có thể thêm logic để AI tự động giải quyết xung đột trước khi merge
                    # Hiện tại, merge_modules_into_framework sẽ cố gắng giải quyết khi merge.
                
                # Bước cuối cùng của Act: Tự động merge code fix vào framework.py
                if self.executor.merge_modules_into_framework():
                    logger.info(f"Successfully merged modules into framework.py.")
                    self.executor.git_commit_changes(f"Feat: All tests passed and framework merged successfully after {self.context.current_attempt} attempts.")
                    logger.info(f"Changes committed to {self.context.current_branch}. Please review and merge to {MAIN_BRANCH}.")
                    break # Thoát vòng lặp chính nếu mọi thứ OK
                else:
                    logger.error("Failed to merge modules into framework.py. Reverting branch.")
                    self.executor.git_revert_current_branch(self.context)
            elif not framework_ok_status:
                logger.warning("Framework verification failed. Attempting to fix framework integrity.")
                self._handle_framework_failure(framework_log)
            else: # Tests failed
                logger.warning("Tests failed. Analyzing errors and attempting to fix...")
                self._handle_test_failure(test_log)
            
            # Sau mỗi lần thử, nếu chưa thành công, revert branch hiện tại để bắt đầu lại từ trạng thái sạch
            # (Logic này đã được xử lý ở đầu vòng lặp chính, sau khi tạo branch mới)
            # Nếu một attempt thất bại, branch hiện tại sẽ bị xóa và một branch mới sẽ được tạo cho attempt tiếp theo.
            
        if not (test_ok and framework_ok_status): # Kiểm tra lại trạng thái cuối cùng
            logger.error(f"Failed to fix all issues after maximum attempts ({max_attempts}).")
            logger.info("Please manually inspect the code and logs.")
            sys.exit(1)
        
        # Bước cuối cùng: Tự phản chiếu và cải thiện (Learn)
        self._self_reflect_and_improve()

    def _handle_test_failure(self, test_log: str):
        """Process test failures: analyze, plan, execute, criticize."""
        self.context.error_log = test_log
        
        # Tìm file path từ test_log một cách thông minh hơn
        file_path_match = re.search(r"File \"([^\"]+)\"", test_log)
        self.context.problem_file = Path(file_path_match.group(1)) if file_path_match else Path("unknown")

        # Bước 2: Lập kế hoạch (Plan)
        self.context = self.planner.analyze_and_plan(self.context) # Cập nhật context với root_cause, fix_strategy, ai_plan
        
        logger.info(f"Detected {self.context.error_type} in {self.context.problem_file.name}: {self.context.error_msg}")
        logger.info(f"Root Cause: {self.context.root_cause}")
        logger.info(f"AI Plan: {json.dumps(self.context.ai_plan, indent=2)}")

        self.context.original_code_before_fix = self.context.problem_file.read_text(encoding='utf-8') if self.context.problem_file.exists() else ""

        if not self.context.problem_file.exists():
            logger.error(f"File not found for fixing: {self.context.problem_file}. Cannot proceed with fix plan.")
            return

        # Bước 3: Thực thi kế hoạch từng bước (Act)
        plan_success = True
        for step in self.context.ai_plan:
            try:
                # Mỗi bước trong kế hoạch sẽ được thực thi bởi Executor
                step_result = self.executor.execute_plan_step(step, self.context)
                if not step_result:
                    logger.error(f"Plan step '{step.get('action')}' failed. Aborting plan execution.")
                    plan_success = False
                    break
            except EthicsViolation as e:
                logger.critical(f"Ethics violation during plan execution: {str(e)}. Aborting this attempt.")
                plan_success = False
                break
            except Exception as e:
                logger.error(f"An unexpected error occurred during plan step '{step.get('action')}': {str(e)}")
                plan_success = False
                break
        
        if not plan_success:
            logger.error("Failed to execute AI plan.")
            # Không revert ở đây vì vòng lặp chính sẽ revert nếu attempt thất bại
            return

        # Bước 4: Đánh giá chất lượng fix (Critic)
        if plan_success and self.context.problem_file.exists():
            fixed_code_content = self.context.problem_file.read_text(encoding='utf-8')
            if self.context.original_code_before_fix: # Chỉ đánh giá nếu có code gốc
                ai_eval = self.critic.evaluate_fix_quality_with_ai(
                    self.context.original_code_before_fix,
                    fixed_code_content,
                    self.context.error_log,
                    self.ai
                )
                logger.info(f"Fix Quality Score: {ai_eval.get('score')}/10. Explanation: {ai_eval.get('explanation')}")
                if ai_eval.get('score', 0) < 5: # Nếu điểm thấp, có thể cân nhắc lại
                    logger.warning("AI evaluated fix quality as low. This might indicate an incomplete or suboptimal fix.")
                    # TODO: Logic để quyết định có nên thử lại với chiến lược khác hay không dựa trên điểm chất lượng
                
    def _handle_framework_failure(self, framework_log: str):
        """Handle framework.py issues: integrity check, and AI-based fix."""
        self.executor.ensure_framework_integrity()
        
        framework_code = FRAMEWORK_FILE.read_text(encoding='utf-8') if FRAMEWORK_FILE.exists() else ""
        
        logger.warning("Framework failed. Requesting AI for analysis and fix.")
        prompt = f"""
The StillMe Framework (framework.py) failed to run.
Here is the error log from its execution:
```
{framework_log}
```
Here is the current content of framework.py:
```python
{framework_code}
```
Analyze the error log and the code. Identify the root cause of the framework failure and provide the corrected, complete framework.py code.
Return ONLY the complete, corrected Python code block. Do NOT include any explanations or extra text outside the code block.
"""
        ai_fix_response = self.ai.get_ai_fix(prompt)
        if ai_fix_response:
            code_match = re.search(r"```python\n(.*?)\n```", ai_fix_response, re.DOTALL)
            if code_match:
                new_framework_code = code_match.group(1)
                if self.ethics_checker.validate_module_code(new_framework_code):
                    self.executor._backup_file(FRAMEWORK_FILE)
                    FRAMEWORK_FILE.write_text(new_framework_code, encoding='utf-8')
                    logger.info("AI-generated fix applied to framework.py.")
                    self.executor.git_commit_changes("Fix: AI applied fix to framework.py")
                else:
                    logger.error("AI-generated fix for framework.py failed ethics check. Not applying.")
            else:
                logger.warning("AI response for framework.py fix didn't contain a valid code block.")
        else:
            logger.error("AI failed to generate a fix for framework.py.")
        
    def _self_reflect_and_improve(self):
        """Agent reflects on its performance and suggests improvements."""
        logger.info("\n--- Agent Self-Reflection ---")
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            full_log = f.read()
        
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            bug_history = json.load(f)["bugs"]

        prompt = f"""
I am an AI DevOps Agent. I just completed a cycle of testing and fixing code.
Here is my full operational log (last 5000 characters):
```
{full_log[-5000:]}
```
And here is a summary of bugs I have encountered and fixed (or attempted to fix):
```json
{json.dumps(bug_history[-10:], indent=2, ensure_ascii=False)} # Chỉ lấy 10 lỗi gần nhất
```
Based on my performance, identify:
1.  What types of errors did I struggle with the most (e.g., took many attempts, failed to fix, low AI fix quality score)?
2.  What aspects of my current strategy (analysis, planning, execution, criticism) could be improved?
3.  Suggest concrete ways I can improve my intelligence or efficiency (e.g., "use a different AI model for planning", "add a new tool for X", "refine error parsing regex", "improve prompt for code generation").
4.  Are there any patterns in the errors or my fixes that I should be aware of?

Provide your reflection in a structured text format.
"""
        reflection = self.ai.get_ai_response(prompt, preferred_model=DEFAULT_AI_MODEL_REASONING)
        if reflection:
            logger.info("\n--- AI Agent Self-Reflection Report ---")
            logger.info(reflection)
            # TODO: Lưu báo cáo tự phản chiếu vào một file riêng (ví dụ: reflection_reports/YYYYMMDD_HHMMSS.md)
            # TODO: Dựa vào báo cáo này, Agent có thể tự điều chỉnh các tham số,
            # hoặc tạo ra các task mới để cải thiện chính mình trong tương lai (meta-learning).
            # Ví dụ: nếu AI báo cáo rằng nó gặp khó khăn với một loại lỗi cụ thể, Agent có thể
            # tự động tạo ra một spec mới để huấn luyện một module chuyên biệt cho loại lỗi đó.
        else:
            logger.warning("Failed to generate self-reflection report.")


if __name__ == "__main__":
    # --- Hướng dẫn thiết lập môi trường để chạy thử ---
    # 1. Cài đặt Docker: Đảm bảo Docker Desktop đang chạy hoặc Docker Engine đã được cài đặt và chạy.
    # 2. Tạo một Dockerfile cơ bản trong thư mục gốc của dự án của bạn (nơi agent_dev.py đang chạy):
    #    Ví dụ: Dockerfile
    #    ```dockerfile
    #    FROM python:3.9-slim-buster
    #    WORKDIR /app
    #    COPY requirements.txt .
    #    RUN pip install --no-cache-dir -r requirements.txt
    #    COPY . /app
    #    ```
    # 3. Tạo file requirements.txt trong thư mục gốc, chứa các dependencies của dự án StillMe và của AgentDev:
    #    ```
    #    pytest
    #    pylint
    #    ollama
    #    openai
    #    cryptography
    #    jsonschema
    #    # Thêm các dependencies khác của StillMe Framework và các module của bạn
    #    ```
    # 4. Build Docker image (chỉ cần làm 1 lần hoặc khi có thay đổi trong Dockerfile/requirements.txt):
    #    Chạy lệnh trong terminal tại thư mục gốc của dự án:
    #    `docker build -t stillme-dev-env .`
    #    Sau đó, trong SafeExecutor.run_command_in_docker_sandbox, `docker_image` đã được đặt mặc định là "stillme-dev-env".
    # 5. Thiết lập API Keys: Tạo file .env trong cùng thư mục với agent_dev.py:
    #    ```
    #    OPENAI_API_KEY="your_openai_api_key_here"
    #    OLLAMA_API_URL="http://localhost:11434" # Hoặc URL Ollama của bạn
    #    ```
    # 6. Tạo cấu trúc thư mục và file để thử nghiệm:
    #    - Tạo thư mục `modules/`
    #    - Tạo thư mục `tests/`
    #    - Tạo một file `framework.py` (có thể là code framework từ các phiên bản trước)
    #    - Tạo một file module lỗi trong `modules/` và một test file tương ứng trong `tests/`
    #      Ví dụ:
    #      modules/example_module.py:
    #      ```python
    #      def faulty_function():
    #          # Lỗi cố ý: biến chưa khai báo
    #          print(undeclared_variable)
    #      ```
    #      tests/test_example_module.py:
    #      ```python
    #      import pytest
    #      from modules.example_module import faulty_function
    #      def test_faulty_function_raises_name_error():
    #          with pytest.raises(NameError):
    #              faulty_function()
    #      ```
    # 7. Xóa thư mục .git để khởi tạo lại repo mỗi lần chạy nếu cần cho thử nghiệm mới:
    #    (Chỉ dùng cho mục đích thử nghiệm, không dùng trong môi trường thực tế)
    #    # if Path(".git").exists():
    #    #     logger.warning("Removing existing .git directory for fresh start...")
    #    #     shutil.rmtree(".git")

    agent = AgentDev()
    agent.main_loop(max_attempts=3) # Số lần thử tối đa để fix lỗi
