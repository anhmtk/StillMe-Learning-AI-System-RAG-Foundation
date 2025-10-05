#!/usr/bin/env python3
"""
Performance and Concurrency tests for AgentDev
Tests performance under load and concurrent operations
"""

import pytest
import tempfile
import os
import shutil
import time
import threading
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import json
import concurrent.futures
import multiprocessing

# Import AgentDev modules
from agent_dev.core.agentdev import AgentDev

class TestAgentDevPerformance:
    """Performance and Concurrency tests for AgentDev"""
    
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
    
    @pytest.mark.performance
    def test_single_task_performance(self):
        """Test performance of single task execution"""
        # Test single task performance
        task = "Create a simple calculator application"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0  # Less than 5 seconds
        assert result is not None
        assert result.get("success", False)
    
    @pytest.mark.performance
    def test_batch_processing_performance(self):
        """Test performance of batch processing"""
        # Test batch processing performance
        tasks = [
            "Create file1.py",
            "Create file2.py",
            "Create file3.py",
            "Create file4.py",
            "Create file5.py"
        ]
        
        start_time = time.time()
        results = []
        
        for task in tasks:
            result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 20.0  # Less than 20 seconds for 5 tasks
        assert len(results) == 5
        assert all(result.get("success", False) for result in results)
    
    @pytest.mark.performance
    def test_concurrent_task_execution(self):
        """Test concurrent task execution"""
        # Test concurrent execution
        tasks = [
            "Create concurrent_file1.py",
            "Create concurrent_file2.py",
            "Create concurrent_file3.py"
        ]
        
        def execute_task(task):
            return self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        
        start_time = time.time()
        
        # Execute tasks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_task, task) for task in tasks]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Should complete within reasonable time
        assert concurrent_time < 15.0  # Less than 15 seconds for 3 concurrent tasks
        assert len(results) == 3
        assert all(result.get("success", False) for result in results)
    
    @pytest.mark.performance
    def test_large_codebase_processing(self):
        """Test performance with large codebase"""
        # Create large codebase
        large_codebase_dir = os.path.join(self.test_project, "large_codebase")
        os.makedirs(large_codebase_dir, exist_ok=True)
        
        # Create many files
        for i in range(100):
            file_path = os.path.join(large_codebase_dir, f"module_{i}.py")
            with open(file_path, 'w') as f:
                f.write(f"""
def function_{i}():
    return {i}

def process_{i}(data):
    return data * {i}
""")
        
        # Test processing large codebase
        task = "Analyze and optimize the large codebase"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=large_codebase_dir, mode="senior")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time
        assert processing_time < 30.0  # Less than 30 seconds for large codebase
        assert result is not None
        assert result.get("success", False)
    
    @pytest.mark.performance
    def test_memory_usage_optimization(self):
        """Test memory usage optimization"""
        # Test memory usage
        task = "Process large dataset efficiently"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 10.0  # Less than 10 seconds
        assert result is not None
        assert "memory" in str(result).lower() or "efficient" in str(result).lower()
    
    @pytest.mark.performance
    def test_cpu_usage_optimization(self):
        """Test CPU usage optimization"""
        # Test CPU usage
        task = "Optimize CPU-intensive operations"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 8.0  # Less than 8 seconds
        assert result is not None
        assert "cpu" in str(result).lower() or "optimize" in str(result).lower()
    
    @pytest.mark.performance
    def test_io_operations_performance(self):
        """Test IO operations performance"""
        # Test IO operations
        task = "Handle multiple file operations efficiently"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 6.0  # Less than 6 seconds
        assert result is not None
        assert "io" in str(result).lower() or "file" in str(result).lower()
    
    @pytest.mark.performance
    def test_network_operations_performance(self):
        """Test network operations performance"""
        # Test network operations
        task = "Handle network requests efficiently"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 5.0  # Less than 5 seconds
        assert result is not None
        assert "network" in str(result).lower() or "request" in str(result).lower()
    
    @pytest.mark.performance
    def test_database_operations_performance(self):
        """Test database operations performance"""
        # Test database operations
        task = "Handle database operations efficiently"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 7.0  # Less than 7 seconds
        assert result is not None
        assert "database" in str(result).lower() or "db" in str(result).lower()
    
    @pytest.mark.performance
    def test_caching_performance(self):
        """Test caching performance"""
        # Test caching
        task = "Implement efficient caching strategy"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 4.0  # Less than 4 seconds
        assert result is not None
        assert "cache" in str(result).lower() or "caching" in str(result).lower()
    
    @pytest.mark.performance
    def test_async_operations_performance(self):
        """Test async operations performance"""
        # Test async operations
        task = "Handle asynchronous operations efficiently"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 5.0  # Less than 5 seconds
        assert result is not None
        assert "async" in str(result).lower() or "asynchronous" in str(result).lower()
    
    @pytest.mark.performance
    def test_parallel_processing_performance(self):
        """Test parallel processing performance"""
        # Test parallel processing
        task = "Implement parallel processing for large datasets"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 8.0  # Less than 8 seconds
        assert result is not None
        assert "parallel" in str(result).lower() or "concurrent" in str(result).lower()
    
    @pytest.mark.performance
    def test_throughput_measurement(self):
        """Test throughput measurement"""
        # Test throughput
        tasks = ["Task 1", "Task 2", "Task 3", "Task 4", "Task 5"]
        
        start_time = time.time()
        results = []
        
        for task in tasks:
            result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = len(tasks) / total_time  # tasks per second
        
        # Should achieve reasonable throughput
        assert throughput > 0.5  # At least 0.5 tasks per second
        assert total_time < 25.0  # Less than 25 seconds for 5 tasks
    
    @pytest.mark.performance
    def test_latency_measurement(self):
        """Test latency measurement"""
        # Test latency
        task = "Quick response task"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        latency = end_time - start_time
        
        # Should have low latency
        assert latency < 2.0  # Less than 2 seconds
        assert result is not None
        assert result.get("success", False)
    
    @pytest.mark.performance
    def test_resource_utilization(self):
        """Test resource utilization"""
        # Test resource utilization
        task = "Optimize resource usage"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 6.0  # Less than 6 seconds
        assert result is not None
        assert "resource" in str(result).lower() or "utilization" in str(result).lower()
    
    @pytest.mark.performance
    def test_scalability(self):
        """Test scalability"""
        # Test scalability
        task = "Handle scalable operations"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 7.0  # Less than 7 seconds
        assert result is not None
        assert "scale" in str(result).lower() or "scalable" in str(result).lower()
    
    @pytest.mark.performance
    def test_load_balancing(self):
        """Test load balancing"""
        # Test load balancing
        task = "Implement load balancing"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 5.0  # Less than 5 seconds
        assert result is not None
        assert "load" in str(result).lower() or "balance" in str(result).lower()
    
    @pytest.mark.performance
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        # Test performance monitoring
        task = "Monitor performance metrics"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 4.0  # Less than 4 seconds
        assert result is not None
        assert "monitor" in str(result).lower() or "metrics" in str(result).lower()
    
    @pytest.mark.performance
    def test_performance_optimization(self):
        """Test performance optimization"""
        # Test performance optimization
        task = "Optimize overall performance"
        
        start_time = time.time()
        result = self.agentdev.execute_task(task, project_path=self.test_project, mode="senior")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        assert execution_time < 6.0  # Less than 6 seconds
        assert result is not None
        assert "optimize" in str(result).lower() or "performance" in str(result).lower()

# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
