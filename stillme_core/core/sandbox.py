import shutil
import subprocess
from pathlib import Path


def prepare_sandbox(repo_root: str | Path, sandbox_dir: str | Path) -> Path:
    repo_root = Path(repo_root).resolve()
    sandbox_dir = Path(sandbox_dir).resolve()
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir, ignore_errors=True)
    shutil.copytree(
        repo_root,
        sandbox_dir,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    return sandbox_dir


def run_tests_in_sandbox(cmd: list[str], sandbox_dir: str | Path):
    p = subprocess.run(cmd, cwd=str(sandbox_dir), capture_output=True, text=True)
    return p.returncode == 0, p.stdout, p.stderr