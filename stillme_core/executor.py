import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import os
from .config_defaults import SANDBOX_DIR, REPO_ROOT
from .sandbox import prepare_sandbox, run_tests_in_sandbox
import re
import shutil
import time
import httpx


class ExecResult:
    def __init__(self, ok: bool, stdout: str = "", stderr: str = ""):
        self.ok = ok
        self.stdout = stdout
        self.stderr = stderr


def _run(cmd: List[str], cwd: str | None = None) -> ExecResult:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return ExecResult(p.returncode == 0, p.stdout, p.stderr)


class PatchExecutor:
    def __init__(self, repo_root: str | Path = "."):
        self.repo_root = str(repo_root)
        self._sandbox_path: str | None = None
        self._current_branch: str | None = None

    def create_feature_branch(self, name: str) -> ExecResult:
        self._current_branch = name
        return _run(["git", "checkout", "-b", name], cwd=self._ensure_sandbox())

    def apply_unified_diff(self, diff_text: str) -> ExecResult:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".patch") as tmp:
            tmp.write(diff_text)
            tmp_path = tmp.name
        target_cwd = self._ensure_sandbox()
        res = _run(["git", "apply", "--index", tmp_path], cwd=target_cwd)
        return res

    def apply_patch_and_test(self, plan_item) -> Dict[str, Any]:
        """
        Apply patch from plan_item and run tests.
        Returns dict with 'ok' boolean and execution details.
        """
        try:
            # Apply patch if available
            if hasattr(plan_item, 'patch') and plan_item.patch:
                patch_result = self.apply_unified_diff(plan_item.patch)
                if not patch_result.ok:
                    return {
                        "ok": False,
                        "error": f"Patch application failed: {patch_result.stderr}",
                        "stdout": patch_result.stdout,
                        "stderr": patch_result.stderr
                    }
            
            # Run tests
            tests_to_run = getattr(plan_item, 'tests_to_run', None)
            test_result = self.run_pytest(tests_to_run)
            
            return {
                "ok": test_result.ok,
                "stdout": test_result.stdout,
                "stderr": test_result.stderr,
                "tests_run": tests_to_run or []
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }

    def run_pytest(self, tests: List[str] | None = None) -> ExecResult:
        args = ["python", "-m", "pytest", "-v", "--tb=short"]
        if tests:
            args.extend(tests)
        else:
            # Default to running all tests if none specified
            args.append("tests/")
        
        sandbox_path = self._ensure_sandbox()
        if sandbox_path:
            ok, out, err = run_tests_in_sandbox(args, sandbox_path)
            return ExecResult(ok, out, err)
        return _run(args, cwd=self.repo_root)

    def commit(self, message: str) -> ExecResult:
        target_cwd = self._ensure_sandbox()
        add_res = _run(["git", "add", "-A"], cwd=target_cwd)
        if not add_res.ok:
            return add_res
        return _run(["git", "commit", "-m", message], cwd=target_cwd)

    def rollback(self) -> ExecResult:
        target_cwd = self._ensure_sandbox()
        return _run(["git", "reset", "--hard"], cwd=target_cwd)

    def _ensure_sandbox(self) -> str:
        if os.getenv("SANDBOX_DIR"):
            if not self._sandbox_path:
                self._sandbox_path = str(prepare_sandbox(self.repo_root, os.getenv("SANDBOX_DIR")))
            return self._sandbox_path
        return self.repo_root

    @property
    def current_branch(self) -> str | None:
        return self._current_branch

    # ---------------- Full suite & PR helpers ----------------
    def run_pytest_all(self, tests_dir: str = "tests") -> tuple[bool, int, int, int, str | None]:
        start = time.perf_counter()
        args = ["pytest", "-q", tests_dir]
        cwd = self._ensure_sandbox()
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        dur_ms = int((time.perf_counter() - start) * 1000)
        out = p.stdout + "\n" + p.stderr
        collected = None
        failed = None
        try:
            m = re.search(r"collected\s+(\d+)\s+items", out)
            if m:
                collected = int(m.group(1))
            m2 = re.search(r"=+\s*(\d+)\s+failed", out)
            if m2:
                failed = int(m2.group(1))
            else:
                m3 = re.search(r"=+\s*.*\s(\d+)\s+failed", out)
                if m3:
                    failed = int(m3.group(1))
        except Exception:
            pass
        # dump raw output
        ts = time.strftime("%Y%m%d_%H%M%S")
        log_dir = Path(cwd) / "logs" / "executor"
        log_dir.mkdir(parents=True, exist_ok=True)
        raw_path = log_dir / f"pytest_full_{ts}.log"
        try:
            raw_path.write_text(out, encoding="utf-8")
        except Exception:
            raw_path = None
        return (p.returncode == 0, collected or 0, failed if failed is not None else 0, dur_ms, str(raw_path) if raw_path else None)

    def push_branch(self, remote: str = "origin") -> tuple[bool, str]:
        try:
            branch = self._current_branch
            if not branch:
                return (False, "no_current_branch")
            res = _run(["git", "push", "-u", remote, branch], cwd=self._ensure_sandbox())
            return (res.ok, res.stderr if not res.ok else "")
        except Exception as e:
            return (False, str(e))

    def _parse_remote(self, remote: str = "origin") -> tuple[bool, str | None, str | None, str | None]:
        try:
            p = subprocess.run(["git", "remote", "get-url", remote], cwd=self._ensure_sandbox(), capture_output=True, text=True)
            if p.returncode != 0:
                return (False, None, None, p.stderr.strip())
            url = p.stdout.strip()
            # https://github.com/owner/repo.git or git@github.com:owner/repo.git
            m = re.search(r"github.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
            if not m:
                return (False, None, None, "unsupported_remote")
            return (True, m.group("owner"), m.group("repo"), None)
        except Exception as e:
            return (False, None, None, str(e))

    def create_pull_request(self, title: str, body: str, base: str = "main", remote: str = "origin", draft: bool = True) -> dict:
        attempted = True
        try:
            if os.getenv("ALLOW_PR", "false").lower() != "true":
                return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": None, "error": "disabled"}
            branch = self._current_branch
            if not branch:
                return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": None, "error": "no_branch"}
            ok, owner, repo, err = self._parse_remote(remote)
            if not ok or not owner or not repo:
                return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": None, "error": err or "remote_unavailable"}

            # Prefer gh CLI
            if shutil.which("gh"):
                args = ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body]
                if draft:
                    args.append("--draft")
                p = subprocess.run(args, cwd=self._ensure_sandbox(), capture_output=True, text=True)
                if p.returncode == 0:
                    # gh usually prints URL
                    url = p.stdout.strip().split()[-1]
                    num = None
                    m = re.search(r"/pull/(\d+)", url)
                    if m:
                        num = int(m.group(1))
                    return {"attempted": attempted, "ok": True, "url": url, "number": num, "provider": "gh", "error": None}
                else:
                    return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": "gh", "error": p.stderr.strip()}

            # Fallback GitHub REST
            token = os.getenv("GITHUB_TOKEN", "")
            if not token:
                return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": "github_api", "error": "no_token"}
            api = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            try:
                r = httpx.post(api, headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}, json={"title": title, "head": branch, "base": base, "body": body, "draft": draft}, timeout=30)
                if r.status_code in (200, 201):
                    data = r.json()
                    return {"attempted": attempted, "ok": True, "url": data.get("html_url"), "number": data.get("number"), "provider": "github_api", "error": None}
                return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": "github_api", "error": f"status={r.status_code}"}
            except Exception as e:
                return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": "github_api", "error": str(e)}
        except Exception as e:
            return {"attempted": attempted, "ok": False, "url": None, "number": None, "provider": None, "error": str(e)}


