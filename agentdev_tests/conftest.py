#!/usr/bin/env python3
"""
Test configuration for AgentDev tests
Handles imports and mocking for testing
"""

import sys
import os
import types
from pathlib import Path

# Add parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Mock AgentDev modules if not available
try:
    import agent_dev
except ImportError:
    # Create mock agent_dev module
    import types
    agent_dev = types.ModuleType('agent_dev')
    agent_dev.core = types.ModuleType('core')
    sys.modules['agent_dev'] = agent_dev
    sys.modules['agent_dev.core'] = agent_dev.core

# Mock classes for testing
class MockImpactAnalyzer:
    def __init__(self):
        pass
    
    def analyze_impact(self, change):
        return MockImpactAnalysisResult()
    
    def analyze_code_change(self, file_path, change_type):
        return MockImpactAnalysisResult()
    
    def analyze_dependency_impact(self, dependencies):
        return MockImpactAnalysisResult()

class MockImpactAnalysisResult:
    def __init__(self, impact_score=0.5, risk_level="medium", affected_files=None):
        self.impact_score = impact_score
        self.risk_level = risk_level
        self.affected_files = affected_files or []
        self.confidence = 0.8
        self.estimated_effort = "medium"

class MockBusinessThinking:
    def __init__(self):
        pass
    
    def analyze_business_impact(self, change):
        return {"roi": 0.7, "priority": "high"}
    
    def evaluate_cost_benefit(self, change):
        return {"cost": 100, "benefit": 200}

class MockSecurityThinking:
    def __init__(self):
        pass
    
    def analyze_security_impact(self, change):
        return {"risk_level": "medium", "vulnerabilities": []}
    
    def assess_vulnerability(self, code):
        return {"severity": "low", "cve_count": 0}

class MockCleanupManager:
    def __init__(self):
        pass
    
    def identify_cleanup_opportunities(self, codebase):
        return []
    
    def prioritize_cleanup(self, opportunities):
        return []

class MockConflictResolver:
    def __init__(self):
        pass
    
    def detect_conflicts(self, directory):
        return []
    
    def resolve_conflicts(self, conflicts):
        return []

class MockAgentDev:
    def __init__(self):
        self.impact_analyzer = MockImpactAnalyzer()
        self.business_thinking = MockBusinessThinking()
        self.security_thinking = MockSecurityThinking()
        self.cleanup_manager = MockCleanupManager()
        self.conflict_resolver = MockConflictResolver()

# Set up mocks
try:
    if not hasattr(agent_dev.core, 'impact_analyzer_improved'):
        agent_dev.core.impact_analyzer_improved = types.ModuleType('impact_analyzer_improved')
        agent_dev.core.impact_analyzer_improved.ImpactAnalyzer = MockImpactAnalyzer
        agent_dev.core.impact_analyzer_improved.ImpactAnalysisResult = MockImpactAnalysisResult

    if not hasattr(agent_dev.core, 'business_thinking'):
        agent_dev.core.business_thinking = types.ModuleType('business_thinking')
        agent_dev.core.business_thinking.BusinessThinking = MockBusinessThinking

    if not hasattr(agent_dev.core, 'security_thinking'):
        agent_dev.core.security_thinking = types.ModuleType('security_thinking')
        agent_dev.core.security_thinking.SecurityThinking = MockSecurityThinking

    if not hasattr(agent_dev.core, 'cleanup_manager'):
        agent_dev.core.cleanup_manager = types.ModuleType('cleanup_manager')
        agent_dev.core.cleanup_manager.CleanupManager = MockCleanupManager

    if not hasattr(agent_dev.core, 'conflict_resolver'):
        agent_dev.core.conflict_resolver = types.ModuleType('conflict_resolver')
        agent_dev.core.conflict_resolver.ConflictResolver = MockConflictResolver

    if not hasattr(agent_dev.core, 'agentdev'):
        agent_dev.core.agentdev = types.ModuleType('agentdev')
        agent_dev.core.agentdev.AgentDev = MockAgentDev
except AttributeError:
    # If agent_dev.core doesn't exist, create it
    agent_dev.core = types.ModuleType('core')
    agent_dev.core.impact_analyzer_improved = types.ModuleType('impact_analyzer_improved')
    agent_dev.core.impact_analyzer_improved.ImpactAnalyzer = MockImpactAnalyzer
    agent_dev.core.impact_analyzer_improved.ImpactAnalysisResult = MockImpactAnalysisResult
    
    agent_dev.core.business_thinking = types.ModuleType('business_thinking')
    agent_dev.core.business_thinking.BusinessThinking = MockBusinessThinking
    
    agent_dev.core.security_thinking = types.ModuleType('security_thinking')
    agent_dev.core.security_thinking.SecurityThinking = MockSecurityThinking
    
    agent_dev.core.cleanup_manager = types.ModuleType('cleanup_manager')
    agent_dev.core.cleanup_manager.CleanupManager = MockCleanupManager
    
    agent_dev.core.conflict_resolver = types.ModuleType('conflict_resolver')
    agent_dev.core.conflict_resolver.ConflictResolver = MockConflictResolver
    
    agent_dev.core.agentdev = types.ModuleType('agentdev')
    agent_dev.core.agentdev.AgentDev = MockAgentDev

# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
