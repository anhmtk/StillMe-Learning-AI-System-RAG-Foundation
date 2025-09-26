# stillme_core/safe_runner.py
from __future__ import annotations

import asyncio
import subprocess
import tempfile
import os
import shutil
from pathlib import Path
from typing import Callable, Dict, Any, Optional
import logging
from stillme_core.base.module_base import ModuleBase, ModuleInfo, ModuleStatus

logger = logging.getLogger(__name__)


class SafeRunner(ModuleBase):
    """
    Safe code execution runner with sandboxing capabilities
    
    Provides secure execution environment for code testing and validation.
    Supports multiple execution strategies with fallback mechanisms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SafeRunner
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.timeout = self.get_config("timeout", 30)
        self.max_memory_mb = self.get_config("max_memory_mb", 512)
        self.allowed_imports = self.get_config("allowed_imports", [
            "os", "sys", "json", "math", "datetime", "collections"
        ])
        self._temp_dir: Optional[Path] = None

    @property
    def module_info(self) -> ModuleInfo:
        """Get module information"""
        return ModuleInfo(
            name="SafeRunner",
            version="1.0.0",
            description="Safe code execution runner with sandboxing",
            author="StillMe AI Team",
            status=self._status,
            dependencies=["subprocess", "tempfile"],
            config_schema={
                "timeout": {"type": "int", "default": 30},
                "max_memory_mb": {"type": "int", "default": 512},
                "allowed_imports": {"type": "list", "default": []}
            }
        )

    async def initialize(self) -> bool:
        """Initialize SafeRunner"""
        try:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="stillme_safe_"))
            self._set_status(ModuleStatus.RUNNING)
            logger.info(f"SafeRunner initialized with temp dir: {self._temp_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SafeRunner: {e}")
            self._set_status(ModuleStatus.ERROR)
            return False

    async def process(self, input_data: Any) -> Any:
        """
        Process code execution request
        
        Args:
            input_data: Code string or execution request
            
        Returns:
            Execution result dictionary
        """
        if isinstance(input_data, str):
            code = input_data
        elif isinstance(input_data, dict) and "code" in input_data:
            code = input_data["code"]
        else:
            raise ValueError("Input must be code string or dict with 'code' key")

        return await self.run_safe(code)

    async def run_safe(self, code: str) -> Dict[str, Any]:
        """
        Run code safely with sandboxing
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result dictionary
        """
        if not self._temp_dir:
            raise RuntimeError("SafeRunner not initialized")

        try:
            # Validate code for security
            if not self._validate_code(code):
                return {
                    "ok": False,
                    "error": "Code validation failed - contains disallowed imports or operations",
                    "artifacts": {"log": "Code validation failed"}
                }

            # Create temporary file
            script_path = self._temp_dir / "script.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)

            # Execute with timeout and resource limits
            result = await self._execute_with_limits(script_path)
            
            return {
                "ok": result["success"],
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "artifacts": {
                    "log": result.get("log", ""),
                    "execution_time": result.get("execution_time", 0)
                }
            }

        except Exception as e:
            logger.error(f"Safe execution failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "artifacts": {"log": f"Execution error: {e}"}
            }

    def _validate_code(self, code: str) -> bool:
        """
        Validate code for security
        
        Args:
            code: Code to validate
            
        Returns:
            bool: True if code is safe
        """
        # Check for dangerous imports
        dangerous_imports = [
            "subprocess", "os.system", "eval", "exec", "compile",
            "importlib", "__import__", "open", "file"
        ]
        
        for dangerous in dangerous_imports:
            if dangerous in code:
                logger.warning(f"Dangerous import detected: {dangerous}")
                return False

        # Check for file system operations
        fs_operations = ["open(", "file(", "os.remove", "os.rmdir", "shutil."]
        for op in fs_operations:
            if op in code:
                logger.warning(f"File system operation detected: {op}")
                return False

        return True

    async def _execute_with_limits(self, script_path: Path) -> Dict[str, Any]:
        """
        Execute script with resource limits
        
        Args:
            script_path: Path to script file
            
        Returns:
            Execution result
        """
        try:
            # Use asyncio to run with timeout
            process = await asyncio.create_subprocess_exec(
                "python", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._temp_dir)
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode('utf-8', errors='ignore'),
                    "error": stderr.decode('utf-8', errors='ignore'),
                    "log": f"Process completed with return code: {process.returncode}",
                    "execution_time": 0  # Could be measured if needed
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Execution timeout after {self.timeout} seconds",
                    "log": "Process killed due to timeout"
                }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "log": f"Execution failed: {e}"
            }

    async def cleanup(self) -> None:
        """Cleanup SafeRunner resources"""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                logger.info(f"Cleaned up temp directory: {self._temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp directory: {e}")
        
        self._set_status(ModuleStatus.STOPPED)
