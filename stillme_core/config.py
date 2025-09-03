import os

def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "fast")
WARMUP_ON_START = _get_bool("WARMUP_ON_START", True)
