#!/usr/bin/env python3
# Copyright: StillMe Project - Enterprise Edition
__author__ = "StillMe Framework Team"
__license__ = "Commercial License"
__version__ = "2.1.0"

import asyncio
import importlib
import importlib.util
import inspect
import json
import logging
import logging.handlers
import subprocess
import sys
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import yaml
import psutil
from RestrictedPython import compile_restricted

# ------------------- CONSTANTS -------------------
DEFAULT_CONFIG = {
    "modules_dir": "modules",
    "auto_load": True,
    "strict_mode": False,
    "max_module_load_time": 30,
    "allowed_imports": ["math", "datetime", "json"],
    "security_level": "high"
}

# ------------------- JSON LOGGER -------------------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        return json.dumps(log_entry, ensure_ascii=False)

# ------------------- CORE FRAMEWORK -------------------
class StillMeFramework:
    def __init__(self, config: Dict[str, Any] = None):
        self._modules: Dict[str, object] = {}
        self._dependency_graph = defaultdict(list)
        self._api_endpoints = {}
        self._middlewares = []
        self._security_policies = {}
        self._setup_framework(config or {})
        self._metrics = FrameworkMetrics()
        self._setup_heartbeat()
        self._register_graceful_shutdown()

    def _setup_framework(self, config: Dict[str, Any]):
        self.config = {**DEFAULT_CONFIG, **config}
        self.logger = self._init_logger()
        self.memory = SecureMemoryManager()
        self.ethics = EthicsChecker(level=self.config["security_level"])
        self._api_docs = OpenAPIGenerator()

        if self.config["auto_load"]:
            asyncio.run(self._auto_discover_modules())

    def _init_logger(self):
        logger = logging.getLogger("StillMe")
        logger.setLevel(logging.INFO)
        json_formatter = JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S')

        file_handler = logging.handlers.RotatingFileHandler(
            'stillme.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setFormatter(json_formatter)
        syslog_handler = logging.StreamHandler(sys.stdout)
        syslog_handler.setFormatter(json_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(syslog_handler)

        self.audit_logger = logging.getLogger("StillMe.Audit")
        audit_handler = logging.FileHandler('audit.log')
        audit_handler.setFormatter(json_formatter)
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.propagate = False

        return logger

    async def _auto_discover_modules(self):
        modules_dir = Path(self.config["modules_dir"])
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, self.load_module, module_path.parent.name)
                for module_path in modules_dir.glob("*/main.py")
            ]
            await asyncio.gather(*tasks)

    # ------------ MODULE MANAGEMENT ------------
    def load_module(self, module_name: str) -> Optional[object]:
        self.audit_logger.info(f"Attempting to load module: {module_name}")
        if module_name in self._modules:
            self.logger.warning(f"Module {module_name} already loaded")
            return self._modules[module_name]

        try:
            if not self._validate_module_name(module_name):
                raise SecurityViolation(f"Invalid module name: {module_name}")

            with self._metrics.track(f"module_load:{module_name}"):
                module = self._import_module_with_sandbox(module_name)
                self._validate_module_structure(module)

                if not self.ethics.validate_module(module):
                    raise EthicsViolation(f"Module {module_name} failed ethics check")

                self._modules[module_name] = module
                self._resolve_dependencies(module)
                self._register_apis(module)
                self._install_module_requirements(module)

                if hasattr(module, "on_load"):
                    self._execute_lifecycle_hook(module.on_load)

                self.audit_logger.info(f"Successfully loaded module: {module_name}")
                self.logger.info(f"✅ Module {module_name} loaded successfully")
                return module

        except Exception as e:
            self.logger.error(f"❌ Error loading {module_name}: {str(e)}")
            self.audit_logger.error(f"Module load failed: {module_name} - {str(e)}")
            if self.config["strict_mode"]:
                raise
            return None

    def _import_module_with_sandbox(self, module_name: str) -> object:
        module_path = f"{self.config['modules_dir']}/{module_name}/main.py"
        with open(module_path, 'r', encoding='utf-8') as f:
            code = f.read()
        try:
            compile_restricted(code, filename=module_path, mode='exec')
        except SyntaxError as e:
            raise SecurityViolation(f"Restricted syntax in {module_name}: {str(e)}")

        spec = importlib.util.spec_from_file_location(
            f"modules.{module_name}",
            module_path,
            loader=RestrictedLoader(module_path)
        )
        module = importlib.util.module_from_spec(spec)
        module.__dict__['__builtins__'] = self._get_safe_builtins()
        spec.loader.exec_module(module)
        return module

    def _get_safe_builtins(self) -> dict:
        safe_builtins = {
            'None': None, 'False': False, 'True': True,
            'bool': bool, 'int': int, 'float': float, 'str': str,
            'list': list, 'tuple': tuple, 'dict': dict, 'set': set,
            'frozenset': frozenset, 'len': len, 'range': range,
            'min': min, 'max': max, 'sum': sum, 'abs': abs
        }
        return safe_builtins

    def _validate_module_name(self, module_name: str) -> bool:
        return module_name.isidentifier()

    def _validate_module_structure(self, module: object):
        if not hasattr(module, "ModuleMeta"):
            raise InvalidModuleError("Module missing class ModuleMeta")
        meta = module.ModuleMeta
        required_attrs = [('version', str), ('description', str)]
        for attr, attr_type in required_attrs:
            if not hasattr(meta, attr):
                raise InvalidModuleError(f"ModuleMeta missing {attr}")
            if not isinstance(getattr(meta, attr), attr_type):
                raise TypeError(f"{attr} must be {attr_type.__name__}")

    def _install_module_requirements(self, module: object):
        if hasattr(module.ModuleMeta, 'requirements'):
            requirements = module.ModuleMeta.requirements
            if isinstance(requirements, list) and requirements:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install"] + requirements,
                        check=True, capture_output=True, timeout=300
                    )
                except subprocess.SubprocessError as e:
                    raise DependencyError(f"Failed to install requirements: {str(e)}")

    def _resolve_dependencies(self, module: object):
        if not hasattr(module.ModuleMeta, "dependencies"):
            return
        for dep_spec in module.ModuleMeta.dependencies:
            dep_name = dep_spec if isinstance(dep_spec, str) else dep_spec['name']
            if dep_name not in self._modules:
                self.load_module(dep_name)

    # ------------ API MANAGEMENT ------------
    def _register_apis(self, module: object):
        if not hasattr(module.ModuleMeta, "api_prefix"):
            return
        prefix = module.ModuleMeta.api_prefix.rstrip('/')
        api_spec = {'paths': {}, 'components': {'schemas': {}, 'securitySchemes': {}}}
        for name, method in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("api_"):
                endpoint = f"{prefix}/{name[4:]}"
                self._api_endpoints[endpoint] = self._wrap_with_middleware(method)
                api_spec['paths'][endpoint] = self._generate_openapi_spec(method)
        self._api_docs.update(api_spec)

    def _generate_openapi_spec(self, func: Callable) -> dict:
        spec = {
            'summary': func.__doc__ or "No description",
            'responses': {'200': {'description': 'Successful operation'}}
        }
        sig = inspect.signature(func)
        if sig.parameters:
            spec['parameters'] = []
            for name, param in sig.parameters.items():
                spec['parameters'].append({
                    'name': name,
                    'in': 'query' if param.default != inspect.Parameter.empty else 'path',
                    'required': param.default == inspect.Parameter.empty,
                    'schema': {'type': self._map_python_type(param.annotation)}
                })
        return spec

    def _map_python_type(self, py_type) -> str:
        type_map = {int: 'integer', float: 'number', str: 'string', bool: 'boolean'}
        return type_map.get(py_type, 'string')

    def _wrap_with_middleware(self, func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapped(*args, **kwargs):
            for middleware in self._middlewares:
                args, kwargs = middleware.process_request(*args, **kwargs)
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            for middleware in reversed(self._middlewares):
                result = middleware.process_response(result)
            return result
        return async_wrapped

    # ------------ UTILITIES ------------
    def health_check(self) -> Dict[str, Any]:
        status = {
            "status": "OPERATIONAL",
            "version": __version__,
            "uptime": self._metrics.get_uptime(),
            "resources": {
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('/').percent
            },
            "modules": {name: {"status": "ACTIVE"} for name in self._modules}
        }
        return status

    def _setup_heartbeat(self):
        async def heartbeat():
            while True:
                self._metrics.record_heartbeat()
                await asyncio.sleep(60)
        asyncio.create_task(heartbeat())

    def _execute_lifecycle_hook(self, hook: Callable):
        try:
            asyncio.run(hook(self)) if asyncio.iscoroutinefunction(hook) else hook(self)
        except Exception as e:
            self.logger.error(f"Lifecycle hook failed: {str(e)}")

    def _register_graceful_shutdown(self):
        def shutdown_handler(signum, frame):
            self.logger.warning("Graceful shutdown triggered")
            sys.exit(0)
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

    async def run(self):
        self.logger.info("🚀 StillMe Framework started")
        await asyncio.gather(self._monitor_resources(), self._cleanup_tasks())

    async def _monitor_resources(self):
        while True:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            if cpu > 90 or mem > 90:
                self.logger.warning(f"High resource usage - CPU: {cpu}%, MEM: {mem}%")
            await asyncio.sleep(300)

    async def _cleanup_tasks(self):
        while True:
            self.memory.cleanup()
            await asyncio.sleep(3600)

# ------------------- SECURITY CLASSES -------------------
class SecurityViolation(Exception): pass
class EthicsViolation(Exception): pass
class InvalidModuleError(Exception): pass
class DependencyError(Exception): pass

class RestrictedLoader(importlib.abc.Loader):
    def __init__(self, path): self.path = path
    def exec_module(self, module):
        with open(self.path, 'r', encoding='utf-8') as f:
            code = f.read()
        restricted_globals = {'__builtins__': {}}
        exec(compile_restricted(code, self.path, 'exec'), restricted_globals)
        module.__dict__.update(restricted_globals)

# ------------------- CORE UTILITIES -------------------
class SecureMemoryManager:
    def __init__(self, file_path: str = "memory.enc"):
        self.file_path = Path(file_path)
        self._cache = {}
        self._load()
        self._lock = asyncio.Lock()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, 'rb') as f:
                    decrypted = f.read().decode('utf-8')
                    self._cache = json.loads(decrypted)
            except Exception:
                self._cache = {}

    async def save(self):
        async with self._lock:
            with open(self.file_path, 'wb') as f:
                f.write(json.dumps(self._cache).encode('utf-8'))

    def cleanup(self):
        # Clean expired keys
        pass

class EthicsChecker:
    def __init__(self, level="medium", rules_path="ethics_rules.json"):
        self.level = level
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path):
        if Path(rules_path).exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"banned": [], "keywords": []}

    def validate_module(self, module: object) -> bool:
        source = inspect.getsource(module)
        result = self.validate(source)
        return result["valid"]

    def validate(self, content: str) -> Dict[str, Any]:
        violations = [kw for kw in self.rules.get("banned", []) if kw.lower() in content.lower()]
        return {"valid": len(violations) == 0, "violations": violations}

class FrameworkMetrics:
    def __init__(self):
        self._start_time = time.time()
        self._metrics = defaultdict(list)

    def track(self, metric_name: str):
        class Timer:
            def __enter__(self_): self_.start = time.perf_counter(); return self_
            def __exit__(self_, *args): self._metrics[metric_name].append(time.perf_counter() - self_.start)
        return Timer()

    def get_uptime(self): return f"{int(time.time()-self._start_time)}s"
    def record_heartbeat(self): self._metrics['heartbeat'].append(time.time())

class OpenAPIGenerator:
    def __init__(self):
        self.spec = {'openapi': '3.0.0', 'info': {'title': 'StillMe API', 'version': '1.0.0'}, 'paths': {}}
    def update(self, api_spec: dict): self.spec['paths'].update(api_spec.get('paths', {}))
    def to_yaml(self) -> str: return yaml.dump(self.spec)

# ------------------- MAIN ENTRY -------------------
if __name__ == "__main__":
    try:
        framework = StillMeFramework({"modules_dir": "modules", "strict_mode": False, "security_level": "high"})
        asyncio.run(framework.run())
    except Exception as e:
        logging.critical(f"Framework crashed: {str(e)}")
        sys.exit(1)
