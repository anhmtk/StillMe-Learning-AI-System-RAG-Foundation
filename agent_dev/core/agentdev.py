#!/usr/bin/env python3
"""
AgentDev Core - Main orchestrator
"""

from agent_dev.core.executor import Executor
from agent_dev.core.planner import Planner


class AgentDev:
    """Main AgentDev orchestrator"""

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()
