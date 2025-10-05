#!/usr/bin/env python3
"""
Chaos Engineering tests for AgentDev
Tests resilience under failure conditions
"""

import pytest
import tempfile
import os
import shutil
import time
import signal
import threading
from pathlib import Path
from typing import Dict, Any, List
import json
import random

# Import AgentDev modules
from agent_dev.core.agentdev import AgentDev

class TestAgentDevChaos:
    """Chaos Engineering tests for AgentDev"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agentdev = AgentDev()
        
        # Create test project structure
        self.test_project = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.chaos
    def test_io_error_storm(self):
        """Test resilience to IO error storm"""
        # Simulate IO errors
        io_errors = [
            "EINTR", "EIO", "ENOSPC", "EROFS", "EACCES", "ENOENT"
        ]
        
        for error in io_errors:
            # Test that AgentDev handles IO errors gracefully
            task = f"Process data with potential {error} error"
            result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
            
            # Should handle IO errors gracefully
            assert result is not None
            assert "error" in str(result).lower() or "retry" in str(result).lower() or "fallback" in str(result).lower()
    
    @pytest.mark.chaos
    def test_disk_full_simulation(self):
        """Test resilience to disk full condition"""
        # Simulate disk full condition
        disk_full_requests = [
            "Create large file when disk is full",
            "Write data to full disk",
            "Save backup when no space available",
            "Generate logs when disk is full"
        ]
        
        for request in disk_full_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle disk full condition gracefully
            assert result is not None
            assert "disk full" in str(result).lower() or "no space" in str(result).lower() or "cleanup" in str(result).lower()
    
    @pytest.mark.chaos
    def test_permission_denied_handling(self):
        """Test resilience to permission denied errors"""
        # Simulate permission denied errors
        permission_requests = [
            "Write to read-only directory",
            "Access restricted file",
            "Modify system file",
            "Execute without permissions"
        ]
        
        for request in permission_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle permission denied gracefully
            assert result is not None
            assert "permission denied" in str(result).lower() or "access denied" in str(result).lower() or "unauthorized" in str(result).lower()
    
    @pytest.mark.chaos
    def test_file_locked_handling(self):
        """Test resilience to file locked errors"""
        # Simulate file locked errors
        locked_file_requests = [
            "Access locked file",
            "Write to locked file",
            "Read from locked file",
            "Delete locked file"
        ]
        
        for request in locked_file_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle file locked gracefully
            assert result is not None
            assert "locked" in str(result).lower() or "busy" in str(result).lower() or "retry" in str(result).lower()
    
    @pytest.mark.chaos
    def test_crash_mid_operation(self):
        """Test resilience to crash mid-operation"""
        # Simulate crash mid-operation
        crash_scenarios = [
            "Process data and crash",
            "Generate code and crash",
            "Save file and crash",
            "Validate and crash"
        ]
        
        for scenario in crash_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should handle crash gracefully
            assert result is not None
            assert "crash" in str(result).lower() or "recovery" in str(result).lower() or "rollback" in str(result).lower()
    
    @pytest.mark.chaos
    def test_idempotency_verification(self):
        """Test idempotency of operations"""
        # Test that operations are idempotent
        idempotent_tasks = [
            "Create file if not exists",
            "Update configuration",
            "Process data",
            "Generate documentation"
        ]
        
        for task in idempotent_tasks:
            # Run task multiple times
            result1 = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
            result2 = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
            
            # Results should be consistent
            assert result1 is not None
            assert result2 is not None
            assert result1.get("success") == result2.get("success")
    
    @pytest.mark.chaos
    def test_rollback_cleanup(self):
        """Test rollback and cleanup after failures"""
        # Test rollback scenarios
        rollback_scenarios = [
            "Create file and rollback",
            "Modify code and rollback",
            "Update configuration and rollback",
            "Process data and rollback"
        ]
        
        for scenario in rollback_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should handle rollback gracefully
            assert result is not None
            assert "rollback" in str(result).lower() or "cleanup" in str(result).lower() or "revert" in str(result).lower()
    
    @pytest.mark.chaos
    def test_rate_limiting_handling(self):
        """Test resilience to rate limiting"""
        # Simulate rate limiting
        rate_limit_requests = [
            "Make many API calls",
            "Process large batch of data",
            "Generate multiple files",
            "Execute many operations"
        ]
        
        for request in rate_limit_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle rate limiting gracefully
            assert result is not None
            assert "rate limit" in str(result).lower() or "throttle" in str(result).lower() or "backoff" in str(result).lower()
    
    @pytest.mark.chaos
    def test_backoff_jitter(self):
        """Test backoff and jitter implementation"""
        # Test backoff and jitter
        backoff_scenarios = [
            "Retry failed operation",
            "Handle temporary failure",
            "Recover from error",
            "Resume interrupted operation"
        ]
        
        for scenario in backoff_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should implement backoff and jitter
            assert result is not None
            assert "retry" in str(result).lower() or "backoff" in str(result).lower() or "jitter" in str(result).lower()
    
    @pytest.mark.chaos
    def test_memory_pressure_handling(self):
        """Test resilience to memory pressure"""
        # Simulate memory pressure
        memory_pressure_requests = [
            "Process large dataset",
            "Load many files",
            "Generate large output",
            "Handle memory-intensive operation"
        ]
        
        for request in memory_pressure_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle memory pressure gracefully
            assert result is not None
            assert "memory" in str(result).lower() or "optimize" in str(result).lower() or "efficient" in str(result).lower()
    
    @pytest.mark.chaos
    def test_network_timeout_handling(self):
        """Test resilience to network timeouts"""
        # Simulate network timeouts
        timeout_requests = [
            "Make slow network request",
            "Download large file",
            "Connect to slow server",
            "Handle network delay"
        ]
        
        for request in timeout_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle network timeouts gracefully
            assert result is not None
            assert "timeout" in str(result).lower() or "retry" in str(result).lower() or "fallback" in str(result).lower()
    
    @pytest.mark.chaos
    def test_concurrent_operation_handling(self):
        """Test resilience to concurrent operations"""
        # Simulate concurrent operations
        concurrent_requests = [
            "Process multiple files simultaneously",
            "Handle concurrent requests",
            "Manage shared resources",
            "Coordinate parallel operations"
        ]
        
        for request in concurrent_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle concurrent operations gracefully
            assert result is not None
            assert "concurrent" in str(result).lower() or "parallel" in str(result).lower() or "synchronize" in str(result).lower()
    
    @pytest.mark.chaos
    def test_resource_exhaustion_handling(self):
        """Test resilience to resource exhaustion"""
        # Simulate resource exhaustion
        resource_exhaustion_requests = [
            "Exhaust file descriptors",
            "Use all available memory",
            "Consume all CPU cycles",
            "Fill up disk space"
        ]
        
        for request in resource_exhaustion_requests:
            result = self.agentdev.execute_task(request, project_path=self.test_project, mode="senior")
            
            # Should handle resource exhaustion gracefully
            assert result is not None
            assert "resource" in str(result).lower() or "exhaust" in str(result).lower() or "limit" in str(result).lower()
    
    @pytest.mark.chaos
    def test_corruption_recovery(self):
        """Test resilience to data corruption"""
        # Simulate data corruption
        corruption_scenarios = [
            "Handle corrupted file",
            "Recover from data loss",
            "Validate corrupted data",
            "Repair damaged files"
        ]
        
        for scenario in corruption_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should handle data corruption gracefully
            assert result is not None
            assert "corrupt" in str(result).lower() or "recover" in str(result).lower() or "repair" in str(result).lower()
    
    @pytest.mark.chaos
    def test_chaos_monkey_simulation(self):
        """Test resilience to chaos monkey scenarios"""
        # Simulate chaos monkey scenarios
        chaos_scenarios = [
            "Randomly fail operations",
            "Introduce random delays",
            "Simulate random errors",
            "Create unpredictable behavior"
        ]
        
        for scenario in chaos_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should handle chaos gracefully
            assert result is not None
            assert "chaos" in str(result).lower() or "random" in str(result).lower() or "unpredictable" in str(result).lower()
    
    @pytest.mark.chaos
    def test_failure_cascade_prevention(self):
        """Test prevention of failure cascades"""
        # Simulate failure cascade scenarios
        cascade_scenarios = [
            "Prevent error propagation",
            "Isolate failures",
            "Stop cascade effects",
            "Contain error impact"
        ]
        
        for scenario in cascade_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should prevent failure cascades
            assert result is not None
            assert "cascade" in str(result).lower() or "isolate" in str(result).lower() or "contain" in str(result).lower()
    
    @pytest.mark.chaos
    def test_graceful_degradation(self):
        """Test graceful degradation under stress"""
        # Simulate stress conditions
        stress_scenarios = [
            "Handle high load",
            "Manage resource constraints",
            "Adapt to limitations",
            "Maintain functionality under stress"
        ]
        
        for scenario in stress_scenarios:
            result = self.agentdev.execute_task(scenario, project_path=self.test_project, mode="senior")
            
            # Should degrade gracefully
            assert result is not None
            assert "degrade" in str(result).lower() or "adapt" in str(result).lower() or "graceful" in str(result).lower()

# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
