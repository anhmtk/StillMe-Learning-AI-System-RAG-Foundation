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
import difflib
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any, Callable, Union
import openai
import ollama
from cryptography.fernet import Fernet
import os 
from collections import defaultdict
import shutil
from dataclasses import dataclass
from jsonschema import validate, ValidationError
from dotenv import load_dotenv
load_dotenv()

BACKUP_DIR = Path("backup_legacy")
MEMORY_FILE = Path("agent_memory.json")
LOG_FILE = Path("agent_dev.log")
FRAMEWORK_FILE = Path("framework.py")
FRAMEWORK_BACKUP = Path("framework_backup.py")
MODULES_DIR = Path("modules")

AGENT_WORKING_BRANCH_PREFIX = "agent-fix-"
MAIN_BRANCH = "main"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
DEFAULT_AI_MODEL_CODE = "deepseek-coder:6.7b"
DEFAULT_AI_MODEL_REASONING = "gpt-4o"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AgentDev-SafeMode")

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
                        "enum": ["modify_code", "run_pylint", "add_test", "run_tests", "review_diff", "check_imports", "install_deps"]
                    },
                    "file": {"type": "string", "description": "Đường dẫn tương đối đến file bị ảnh hưởng (nếu có)."},
                    "description": {"type": "string", "description": "Mô tả chi tiết bước hành động này."}
                },
                "required": ["action", "description"]
            }
        }
    },
    "required": ["root_cause", "fix_strategy_summary", "plan"]
}

class AgentError(Exception):
    pass

class EthicsViolation(AgentError):
    pass

class StillMeFrameworkError(AgentError):
    pass

class GitError(AgentError):
    pass

class SandboxError(AgentError):
    pass

@dataclass
class AgentContext:
    problem_file: Optional[Path] = None
    error_log: Optional[str] = None
    original_code_before_fix: Optional[str] = None
    error_type: Optional[str] = None
    error_msg: Optional[str] = None
    root_cause: Optional[str] = None
    fix_strategy: Optional[str] = None
    ai_plan: Optional[List[Dict[str, Any]]] = None
    current_attempt: int = 0
    current_branch: Optional[str] = None
class StillMeFramework:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ethics = EthicsChecker(level=self.config.get("security_level", "medium"))
        logger.info("StillMeFramework (simplified) initialized for ethics checks.")

class EthicsChecker:
    def __init__(self, level="medium"):
        self.level = level
        self.rules = {
            "low": [
                self._check_explicit_content
            ],
            "medium": [
                self._check_explicit_content,
                self._check_hate_speech,
                self._check_length
            ],
            "high": [
                self._check_explicit_content,
                self._check_hate_speech,
                self._check_length,
                self._check_pii_leakage
            ]
        }.get(level, [])
        logger.info(f"EthicsChecker initialized with level: {self.level}")

    def validate(self, content: str) -> bool:
        for rule in self.rules:
            if not rule(content):
                logger.warning(f"Ethics violation: {rule.__name__} for content.")
                return False
        return True

    def validate_module_code(self, code_content: str) -> bool:
        return self.validate(code_content)

    def _check_explicit_content(self, content: str) -> bool:
        return "bad_word" not in content.lower()

    def _check_hate_speech(self, content: str) -> bool:
        return "hate_speech_term" not in content.lower()

    def _check_length(self, content: str) -> bool:
        return 10 < len(content) < 5000

    def _check_pii_leakage(self, content: str) -> bool:
        return not (re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', content) or
                    re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content))

class AIManager:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.ollama_base_url = OLLAMA_API_URL
        openai.api_key = OPENAI_API_KEY

    def _call_ollama(self, model: str, prompt: str, temperature: float = 0.3) -> Optional[str]:
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
        response = None
        if preferred_model == DEFAULT_AI_MODEL_REASONING:
            response = self._call_openai(preferred_model, prompt)
            if not response:
                logger.warning(f"Preferred model {preferred_model} failed. Falling back to {DEFAULT_AI_MODEL_CODE}.")
                response = self._call_ollama(DEFAULT_AI_MODEL_CODE, prompt)
        elif preferred_model == DEFAULT_AI_MODEL_CODE:
            response = self._call_ollama(preferred_model, prompt)
            if not response:
                logger.warning(f"Preferred model {preferred_model} failed. Falling back to {DEFAULT_AI_MODEL_REASONING}.")
                response = self._call_openai(DEFAULT_AI_MODEL_REASONING, prompt)
        if not response:
            logger.error(f"Failed to get AI response from any model for prompt: {prompt[:100]}...")
        return response

    def get_ai_fix(self, prompt: str) -> Optional[str]:
        response = self._call_ollama(DEFAULT_AI_MODEL_CODE, prompt, temperature=0.2)
        model_used = DEFAULT_AI_MODEL_CODE

        if not response or (isinstance(response, str) and ("sorry" in response.lower() or "i cannot help" in response.lower())):
            logger.warning(f"Code model {DEFAULT_AI_MODEL_CODE} failed or gave unhelpful response. Falling back to {DEFAULT_AI_MODEL_REASONING}.")
            response = self._call_openai(DEFAULT_AI_MODEL_REASONING, prompt, temperature=0.2)
            model_used = DEFAULT_AI_MODEL_REASONING
        if response:
            logger.info(f"AI fix generated by {model_used}")
            return response
        return None
        
class BugMemory:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self._ensure_memory_file()
    def _ensure_memory_file(self):
        if not self.memory_file.exists():
            with open(self.memory_file, "w", encoding='utf-8') as f:
                json.dump({"bugs": []}, f)

    def add_bug(self, context: AgentContext, fix_code: str):
        with open(self.memory_file, "r+", encoding='utf-8') as f:
            f.seek(0)
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
                "ai_plan_executed": context.ai_plan
            })
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
        logger.info(f"Bug '{context.error_type}' in {context.problem_file.name} recorded in memory.")

    def get_fix(self, context: AgentContext) -> Optional[str]:
        with open(self.memory_file, "r", encoding='utf-8') as f:
            data = json.load(f)
            for bug in data["bugs"]:
                if bug["error_type"] == context.error_type and \
                   context.error_msg[:50] in bug["error_msg"]:
                    logger.info(f"Found exact match fix in memory for {context.error_type}.")
                    return bug["fixed_code"]
            logger.info("No exact fix found in memory. Semantic search (if implemented) would run here.")
            return None

class Planner:
    def __init__(self, ai_manager: AIManager):
        self.ai = ai_manager

    def analyze_and_plan(self, context: AgentContext) -> AgentContext:
        error_log = context.error_log
        file_path = context.problem_file

        error_type = "UnknownError"
        error_msg = "Unknown error"

        traceback_lines = error_log.splitlines()
        for line in reversed(traceback_lines):
            match_file_line = re.search(r'File "([^"]+)", line (\d+)', line)
            if match_file_line:
                file_path_detected = match_file_line.group(1)
                line_info = match_file_line.group(2)
                if file_path == Path("unknown") or Path(file_path_detected).name == file_path.name:
                    file_path = Path(file_path_detected)
                break

        error_line_match = re.search(r'([A-Za-z]+Error): (.*)', error_log.splitlines()[-1]) if error_log.splitlines() else None
        if error_line_match:
            error_type = error_line_match.group(1)
            error_msg = error_line_match.group(2)
        else:
            error_msg = traceback_lines[-1] if traceback_lines else ""

        context.error_type = error_type
        context.error_msg = error_msg
        context.problem_file = file_path
        logger.info(f"Basic error analysis: Type={error_type}, Msg='{error_msg}', File={file_path}")

        full_code = file_path.read_text(encoding='utf-8') if file_path and file_path.exists() else "Code not available."

        prompt = f"""
You are an expert AI DevOps Agent. Your task is to analyze a Python error and create a detailed, multi-step plan to fix it.
The plan should be a list of actionable steps, each step specifying an "action" (e.g., "modify_code", "run_pylint", "add_test", "run_tests", "review_diff", "check_imports", "install_deps") and relevant "details".
Prioritize fixing the root cause and ensuring code quality.

Error Log:
"""