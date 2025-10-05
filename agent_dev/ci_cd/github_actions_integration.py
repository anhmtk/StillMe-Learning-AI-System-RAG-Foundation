#!/usr/bin/env python3
"""
StillMe AgentDev - GitHub Actions Integration
Enterprise-grade CI/CD integration with automated workflows
"""

import asyncio
import hashlib
import hmac
import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
import yaml


class WorkflowStatus(Enum):
    """GitHub Actions workflow status"""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class JobStatus(Enum):
    """GitHub Actions job status"""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EventType(Enum):
    """GitHub webhook event types"""

    PUSH = "push"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    WORKFLOW_RUN = "workflow_run"
    CHECK_RUN = "check_run"
    DEPLOYMENT = "deployment"


@dataclass
class GitHubWorkflow:
    """GitHub Actions workflow definition"""

    workflow_id: str
    name: str
    path: str
    state: str
    created_at: str
    updated_at: str
    url: str
    html_url: str
    badge_url: str


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run"""

    run_id: int
    workflow_id: int
    status: WorkflowStatus
    conclusion: str | None
    head_branch: str
    head_sha: str
    created_at: str
    updated_at: str
    run_started_at: str
    jobs_url: str
    logs_url: str
    check_suite_url: str
    artifacts_url: str
    cancel_url: str
    rerun_url: str
    workflow_url: str
    head_commit: dict[str, Any]
    repository: dict[str, Any]
    head_repository: dict[str, Any]


@dataclass
class Job:
    """GitHub Actions job"""

    job_id: int
    run_id: int
    name: str
    status: JobStatus
    conclusion: str | None
    started_at: str
    completed_at: str | None
    steps: list[dict[str, Any]]
    check_run_url: str
    labels: list[str]
    runner_id: int
    runner_name: str
    runner_group_id: int
    runner_group_name: str


class GitHubActionsIntegration:
    """Enterprise GitHub Actions integration"""

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.github_token = self.config.get("github_token")
        self.webhook_secret = self.config.get("webhook_secret")
        self.repository = self.config.get("repository")
        self.owner = self.config.get("owner")
        self.base_url = "https://api.github.com"
        self.webhook_handlers: dict[EventType, list[Callable[..., Any]]] = {}
        self.session: aiohttp.ClientSession | None = None

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load GitHub Actions configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/github_actions.yaml")

        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                "github_token": None,
                "webhook_secret": None,
                "repository": "stillme_ai",
                "owner": "your_username",
                "workflows": {
                    "agentdev_deploy": {
                        "enabled": True,
                        "trigger_on": ["push", "pull_request"],
                        "branches": ["main", "develop"],
                    },
                    "agentdev_test": {
                        "enabled": True,
                        "trigger_on": ["push", "pull_request"],
                        "branches": ["*"],
                    },
                    "agentdev_security_scan": {
                        "enabled": True,
                        "trigger_on": ["push"],
                        "branches": ["main"],
                    },
                },
                "notifications": {
                    "slack": {"enabled": False, "webhook_url": None},
                    "email": {"enabled": False, "recipients": []},
                },
            }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self.session:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "StillMe-AgentDev/1.0",
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def get_workflows(self) -> list[GitHubWorkflow]:
        """Get all workflows for the repository"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/workflows"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                workflows: list[GitHubWorkflow] = []
                for workflow_data in data.get("workflows", []):
                    workflow = GitHubWorkflow(
                        workflow_id=workflow_data["id"],
                        name=workflow_data["name"],
                        path=workflow_data["path"],
                        state=workflow_data["state"],
                        created_at=workflow_data["created_at"],
                        updated_at=workflow_data["updated_at"],
                        url=workflow_data["url"],
                        html_url=workflow_data["html_url"],
                        badge_url=workflow_data["badge_url"],
                    )
                    workflows.append(workflow)

                return workflows

        except Exception as e:
            print(f"⚠️ Failed to get workflows: {e}")
            return []

    async def get_workflow_runs(
        self, workflow_id: str, status: WorkflowStatus | None = None, limit: int = 10
    ) -> list[WorkflowRun]:
        """Get workflow runs"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/workflows/{workflow_id}/runs"

        params: dict[str, Any] = {"per_page": limit}
        if status:
            params["status"] = status.value

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                runs: list[WorkflowRun] = []
                for run_data in data.get("workflow_runs", []):
                    run = WorkflowRun(
                        run_id=run_data["id"],
                        workflow_id=run_data["workflow_id"],
                        status=WorkflowStatus(run_data["status"]),
                        conclusion=run_data.get("conclusion"),
                        head_branch=run_data["head_branch"],
                        head_sha=run_data["head_sha"],
                        created_at=run_data["created_at"],
                        updated_at=run_data["updated_at"],
                        run_started_at=run_data["run_started_at"],
                        jobs_url=run_data["jobs_url"],
                        logs_url=run_data["logs_url"],
                        check_suite_url=run_data["check_suite_url"],
                        artifacts_url=run_data["artifacts_url"],
                        cancel_url=run_data["cancel_url"],
                        rerun_url=run_data["rerun_url"],
                        workflow_url=run_data["workflow_url"],
                        head_commit=run_data["head_commit"],
                        repository=run_data["repository"],
                        head_repository=run_data["head_repository"],
                    )
                    runs.append(run)

                return runs

        except Exception as e:
            print(f"⚠️ Failed to get workflow runs: {e}")
            return []

    async def get_jobs(self, run_id: int) -> list[Job]:
        """Get jobs for a workflow run"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/runs/{run_id}/jobs"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                jobs: list[Job] = []
                for job_data in data.get("jobs", []):
                    job = Job(
                        job_id=job_data["id"],
                        run_id=job_data["run_id"],
                        name=job_data["name"],
                        status=JobStatus(job_data["status"]),
                        conclusion=job_data.get("conclusion"),
                        started_at=job_data["started_at"],
                        completed_at=job_data.get("completed_at"),
                        steps=job_data.get("steps", []),
                        check_run_url=job_data["check_run_url"],
                        labels=job_data.get("labels", []),
                        runner_id=job_data["runner_id"],
                        runner_name=job_data["runner_name"],
                        runner_group_id=job_data["runner_group_id"],
                        runner_group_name=job_data["runner_group_name"],
                    )
                    jobs.append(job)

                return jobs

        except Exception as e:
            print(f"⚠️ Failed to get jobs: {e}")
            return []

    async def trigger_workflow(
        self,
        workflow_id: str,
        ref: str = "main",
        inputs: dict[str, Any] | None = None,
    ) -> bool:
        """Trigger a workflow run"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/workflows/{workflow_id}/dispatches"

        payload = {"ref": ref, "inputs": inputs or {}}

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 204:
                    print(f"✅ Workflow {workflow_id} triggered successfully")
                    return True
                else:
                    print(f"⚠️ Failed to trigger workflow: {response.status}")
                    return False

        except Exception as e:
            print(f"⚠️ Failed to trigger workflow: {e}")
            return False

    async def cancel_workflow_run(self, run_id: int) -> bool:
        """Cancel a workflow run"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/runs/{run_id}/cancel"

        try:
            async with session.post(url) as response:
                if response.status == 202:
                    print(f"✅ Workflow run {run_id} cancelled")
                    return True
                else:
                    print(f"⚠️ Failed to cancel workflow run: {response.status}")
                    return False

        except Exception as e:
            print(f"⚠️ Failed to cancel workflow run: {e}")
            return False

    async def rerun_workflow(self, run_id: int) -> bool:
        """Rerun a workflow"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/runs/{run_id}/rerun"

        try:
            async with session.post(url) as response:
                if response.status == 201:
                    print(f"✅ Workflow run {run_id} rerun triggered")
                    return True
                else:
                    print(f"⚠️ Failed to rerun workflow: {response.status}")
                    return False

        except Exception as e:
            print(f"⚠️ Failed to rerun workflow: {e}")
            return False

    async def get_workflow_logs(self, run_id: int) -> str | None:
        """Get workflow run logs"""
        session = await self._get_session()
        url = f"{self.base_url}/repos/{self.owner}/{self.repository}/actions/runs/{run_id}/logs"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    logs = await response.text()
                    return logs
                else:
                    print(f"⚠️ Failed to get logs: {response.status}")
                    return None

        except Exception as e:
            print(f"⚠️ Failed to get logs: {e}")
            return None

    def register_webhook_handler(self, event_type: EventType, handler: Callable[..., Any]):
        """Register webhook event handler"""
        if event_type not in self.webhook_handlers:
            self.webhook_handlers[event_type] = []
        self.webhook_handlers[event_type].append(handler)

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not self.webhook_secret:
            return False

        expected_signature = (
            "sha256="
            + hmac.new(
                self.webhook_secret.encode(), payload.encode(), hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature, expected_signature)

    async def handle_webhook(
        self, event_type: str, payload: dict[str, Any], signature: str | None = None
    ) -> bool:
        """Handle GitHub webhook event"""
        # Verify signature if provided
        if signature:
            payload_str = json.dumps(payload)
            if not self.verify_webhook_signature(payload_str, signature):
                print("⚠️ Invalid webhook signature")
                return False

        # Get event type enum
        try:
            event_enum = EventType(event_type)
        except ValueError:
            print(f"⚠️ Unknown event type: {event_type}")
            return False

        # Call registered handlers
        handlers = self.webhook_handlers.get(event_enum, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                print(f"⚠️ Webhook handler error: {e}")

        return True

    async def create_agentdev_workflow(
        self, workflow_name: str, workflow_content: str
    ) -> bool:
        """Create AgentDev workflow file"""
        workflow_path = Path(f".github/workflows/{workflow_name}.yml")
        workflow_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(workflow_path, "w") as f:
                f.write(workflow_content)

            print(f"✅ Created workflow: {workflow_path}")
            return True

        except Exception as e:
            print(f"⚠️ Failed to create workflow: {e}")
            return False

    async def get_workflow_status_summary(self) -> dict[str, Any]:
        """Get comprehensive workflow status summary"""
        workflows = await self.get_workflows()

        summary: dict[str, Any] = {
            "total_workflows": len(workflows),
            "active_workflows": len([w for w in workflows if w.state == "active"]),
            "workflow_status": {},
            "recent_runs": {},
            "failed_runs": 0,
            "success_rate": 0.0,
        }

        total_runs = 0
        successful_runs = 0

        for workflow in workflows:
            runs = await self.get_workflow_runs(workflow.workflow_id, limit=5)
            summary["recent_runs"][workflow.name] = len(runs)

            for run in runs:
                total_runs += 1
                if (
                    run.status == WorkflowStatus.COMPLETED
                    and run.conclusion == "success"
                ):
                    successful_runs += 1
                elif run.status == WorkflowStatus.FAILED or run.conclusion == "failure":
                    summary["failed_runs"] += 1

            # Get workflow status
            if runs:
                latest_run = runs[0]
                summary["workflow_status"][workflow.name] = {
                    "status": latest_run.status.value,
                    "conclusion": latest_run.conclusion,
                    "last_run": latest_run.created_at,
                }

        if total_runs > 0:
            summary["success_rate"] = successful_runs / total_runs

        return summary


# Global GitHub Actions integration instance
github_actions = GitHubActionsIntegration()


# Convenience functions
async def trigger_agentdev_workflow(
    workflow_name: str, inputs: dict[str, Any] | None = None
) -> bool:
    """Trigger AgentDev workflow"""
    # Map workflow names to IDs (this would need to be configured)
    workflow_mapping = {
        "deploy": "agentdev_deploy.yml",
        "test": "agentdev_test.yml",
        "security_scan": "agentdev_security_scan.yml",
    }

    workflow_id = workflow_mapping.get(workflow_name)
    if not workflow_id:
        print(f"⚠️ Unknown workflow: {workflow_name}")
        return False

    return await github_actions.trigger_workflow(workflow_id, inputs=inputs)


async def get_ci_status() -> dict[str, Any]:
    """Get CI/CD status summary"""
    return await github_actions.get_workflow_status_summary()


def register_ci_webhook_handler(event_type: EventType, handler: Callable[..., Any]):
    """Register CI/CD webhook handler"""
    github_actions.register_webhook_handler(event_type, handler)


# Example workflow templates
AGENTDEV_DEPLOY_WORKFLOW = """
name: AgentDev Deploy

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  agentdev-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r agent-dev/requirements.txt

    - name: Run AgentDev CLI
      run: |
        python agent-dev/cli/agentdev_cli.py init-task deploy_edge
        python agent-dev/cli/agentdev_cli.py plan --task task.config.json
        python agent-dev/cli/agentdev_cli.py dry-run --task task.config.json
        python agent-dev/cli/agentdev_cli.py execute --task task.config.json

    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: agentdev-deploy-results
        path: |
          task.config.json
          .agentdev/
"""

AGENTDEV_TEST_WORKFLOW = """
name: AgentDev Test

on:
  push:
    branches: [ '*' ]
  pull_request:
    branches: [ main, develop ]

jobs:
  agentdev-test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r agent-dev/requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest agent-dev/tests/ -v --cov=agent-dev --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
"""

AGENTDEV_SECURITY_WORKFLOW = """
name: AgentDev Security Scan

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r agent-dev/requirements.txt
        pip install bandit safety pip-audit

    - name: Run security scans
      run: |
        bandit -r agent-dev/ -f json -o bandit-report.json
        safety check --json --output safety-report.json
        pip-audit --format=json --output=pip-audit-report.json

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
          pip-audit-report.json
"""

if __name__ == "__main__":

    async def main():
        # Example usage
        github = GitHubActionsIntegration()

        # Get workflows
        workflows = await github.get_workflows()
        print(f"Found {len(workflows)} workflows")

        # Get workflow status
        status = await github.get_workflow_status_summary()
        print(f"CI Status: {status}")

        # Create example workflows
        await github.create_agentdev_workflow(
            "agentdev_deploy", AGENTDEV_DEPLOY_WORKFLOW
        )
        await github.create_agentdev_workflow("agentdev_test", AGENTDEV_TEST_WORKFLOW)
        await github.create_agentdev_workflow(
            "agentdev_security", AGENTDEV_SECURITY_WORKFLOW
        )

        await github.close()

    asyncio.run(main())
