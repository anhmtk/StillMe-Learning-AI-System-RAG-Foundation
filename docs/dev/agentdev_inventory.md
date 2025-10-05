## AgentDev Inventory

Scope: `agent_dev.py`, `stillme_core/{planner.py, ai_manager.py, agent_dev_bridge.py, sandbox_manager.py, git_manager.py, provider_router.py, safe_runner.py}`, `api_server.py`.

### Files and roles
- `agent_dev.py`: Orchestrates attempts: plan via bridge → fallback planner → ethics → execute steps → tests → commit.
- `stillme_core/planner.py`: Builds JSON plans (rule-based first, then AI via bridge) with normalization and schema validation.
- `stillme_core/ai_manager.py`: Routes text modes to bridge, code mode to interpreter controller.
- `stillme_core/agent_dev_bridge.py`: HTTP client to `/dev-agent/bridge`.
- `stillme_core/sandbox_manager.py`: Docker sandbox wrapper (run commands, file ops).
- `stillme_core/git_manager.py`: Branch, commit, revert helpers.
- `stillme_core/provider_router.py`: Bridge ask helper.
- `stillme_core/safe_runner.py`: Optional safety check for outputs.
- `api_server.py`: FastAPI app; `/dev-agent/bridge`, `/health/ai`.

### Observations
- Planner returns normalized plan dict; AgentDev expects AI_PLAN_SCHEMA in `agent_dev.py` when using bridge-fast path.
- Bridge forces JSON-only responses and safe-run optional.
- Missing pieces for priority goals: no BugMemory, no unified-diff patch executor, limited loop refinement.

### TODO snapshot
- Planner v2: PlanItem dataclass, git/pytest signal intake, 2–5 actionable items.
- Executor: apply unified diff safely, create feature branch, run pytest subset, commit or rollback.
- BugMemory: persist error fingerprints and attempts.
- Config: centralize defaults, optional .env loading.
- Bridge API: add `/dev-agent/plan`, `/dev-agent/run` endpoints.


