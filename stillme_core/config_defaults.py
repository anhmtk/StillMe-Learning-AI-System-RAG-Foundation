import os
from typing import Optional


def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


# Core envs
KEEP_WARM_SEC: int = int(os.getenv("KEEP_WARM_SEC", "600"))
DEFAULT_MODE: str = os.getenv("DEFAULT_MODE", "fast")
MODEL_CHOOSER: str = os.getenv("MODEL_CHOOSER", "auto")
REPO_ROOT: str = os.getenv("REPO_ROOT", os.getcwd())
SANDBOX_DIR: str = os.getenv("SANDBOX_DIR", os.path.join(REPO_ROOT, ".sandbox"))
GIT_USER: str = os.getenv("GIT_USER", "agentdev")
GIT_EMAIL: str = os.getenv("GIT_EMAIL", "agentdev@example.com")


def try_load_dotenv() -> None:
    """Load .env if python-dotenv is installed; otherwise ignore silently."""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()  # load default .env in cwd
    except Exception:
        pass


