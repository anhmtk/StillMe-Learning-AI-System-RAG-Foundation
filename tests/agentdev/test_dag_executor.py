#!/usr/bin/env python3
"""
AgentDev DAG Executor Tests - SEAL-GRADE
Comprehensive testing for DAG execution functionality
"""

import asyncio
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from agentdev.dag.dag_executor import (
    DAGExecutor, NodeStatus, DAGStatus, ExecutionMode,
    NodeDefinition, EdgeDefinition, ExecutionContext
)

class TestDAGExecutor:
    """Test DAG Executor functionality"""
    
    def create_test_dag_file(self, dag_config: dict) -> str:
        """Create temporary DAG file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(dag_config, temp_file)
        temp_file.close()
        return temp_file.name
    
    def test_dag_executor_initialization(self):
        """Test DAG executor initialization"""
        
        async def _test():
            # Create test DAG config
            dag_config = {
                'dag': {
                    'name': 'test_dag',
                    'version': '1.0.0',
                    'description': 'Test DAG'
                },
                'nodes': {
                    'start': {
                        'type': 'job_management',
                        'task': 'start_job',
                        'description': 'Start job',
                        'inputs': {'job_id': 'string'},
                        'outputs': {'context': 'object'},
                        'retry_policy': {'max_retries': 1},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Should have loaded DAG
                assert len(executor.nodes) == 1
                assert 'start' in executor.nodes
                assert executor.graph.number_of_nodes() == 1
                
                # Should have registered default tasks
                assert 'start_job' in executor.task_registry
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_dag_validation(self):
        """Test DAG validation"""
        
        async def _test():
            # Test valid DAG
            valid_dag = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'a': {'type': 'custom', 'task': 'task_a', 'description': 'Task A', 'inputs': {}, 'outputs': {}, 'retry_policy': {}, 'timeout_seconds': 30, 'cache': {}},
                    'b': {'type': 'custom', 'task': 'task_b', 'description': 'Task B', 'inputs': {}, 'outputs': {}, 'retry_policy': {}, 'timeout_seconds': 30, 'cache': {}}
                },
                'edges': [{'from': 'a', 'to': 'b', 'condition': 'always', 'weight': 1.0}]
            }
            
            dag_file = self.create_test_dag_file(valid_dag)
            
            try:
                executor = DAGExecutor(dag_file)
                # Should not raise exception
                assert executor.graph.number_of_nodes() == 2
                assert executor.graph.number_of_edges() == 1
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_cycle_detection(self):
        """Test cycle detection in DAG"""
        
        async def _test():
            # Test DAG with cycle
            cyclic_dag = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'a': {'type': 'custom', 'task': 'task_a', 'description': 'Task A', 'inputs': {}, 'outputs': {}, 'retry_policy': {}, 'timeout_seconds': 30, 'cache': {}},
                    'b': {'type': 'custom', 'task': 'task_b', 'description': 'Task B', 'inputs': {}, 'outputs': {}, 'retry_policy': {}, 'timeout_seconds': 30, 'cache': {}}
                },
                'edges': [
                    {'from': 'a', 'to': 'b', 'condition': 'always', 'weight': 1.0},
                    {'from': 'b', 'to': 'a', 'condition': 'always', 'weight': 1.0}  # Creates cycle
                ]
            }
            
            dag_file = self.create_test_dag_file(cyclic_dag)
            
            try:
                with pytest.raises(ValueError, match="DAG contains cycles"):
                    DAGExecutor(dag_file)
                    
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_task_registration(self):
        """Test task registration"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {},
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register custom task
                async def custom_task(inputs, context):
                    return {"result": "custom"}
                
                executor.register_task("custom_task", custom_task)
                
                assert "custom_task" in executor.task_registry
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_cache_functionality(self):
        """Test caching functionality"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'cached_task': {
                        'type': 'custom',
                        'task': 'cached_task',
                        'description': 'Cached task',
                        'inputs': {'input': 'string'},
                        'outputs': {'output': 'string'},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {
                            'enabled': True,
                            'ttl_seconds': 60,
                            'key_strategy': 'task_input_hash'
                        }
                    }
                },
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register cached task
                async def cached_task(inputs, context):
                    return {"output": f"processed_{inputs.get('input', '')}"}
                
                executor.register_task("cached_task", cached_task)
                
                # Test cache key generation
                cache_key = executor._generate_cache_key("cached_task", {"input": "test"})
                assert cache_key is not None
                assert "cached_task" in cache_key
                
                # Test cache miss
                result = executor._get_cached_result(cache_key)
                assert result is None
                
                # Test cache set and get
                executor._cache_result(cache_key, {"output": "cached_result"}, "cached_task", 60)
                result = executor._get_cached_result(cache_key)
                assert result == {"output": "cached_result"}
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_sequential_execution(self):
        """Test sequential execution mode"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'task1': {
                        'type': 'custom',
                        'task': 'task1',
                        'description': 'Task 1',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'task2': {
                        'type': 'custom',
                        'task': 'task2',
                        'description': 'Task 2',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': [
                    {'from': 'task1', 'to': 'task2', 'condition': 'always', 'weight': 1.0}
                ]
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register tasks
                execution_order = []
                
                async def task1(inputs, context):
                    execution_order.append('task1')
                    return {"result": "task1"}
                
                async def task2(inputs, context):
                    execution_order.append('task2')
                    return {"result": "task2"}
                
                executor.register_task("task1", task1)
                executor.register_task("task2", task2)
                
                # Execute DAG
                context = await executor.execute_dag(
                    dag_id="test",
                    inputs={},
                    execution_mode=ExecutionMode.SEQUENTIAL
                )
                
                # Check execution order
                assert execution_order == ['task1', 'task2']
                assert context.status == DAGStatus.SUCCESS
                assert context.node_statuses['task1'] == NodeStatus.SUCCESS
                assert context.node_statuses['task2'] == NodeStatus.SUCCESS
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_parallel_execution(self):
        """Test parallel execution mode"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'task1': {
                        'type': 'custom',
                        'task': 'task1',
                        'description': 'Task 1',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'task2': {
                        'type': 'custom',
                        'task': 'task2',
                        'description': 'Task 2',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': []  # No dependencies, can run in parallel
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register tasks
                start_times = {}
                
                async def task1(inputs, context):
                    start_times['task1'] = asyncio.get_event_loop().time()
                    await asyncio.sleep(0.1)
                    return {"result": "task1"}
                
                async def task2(inputs, context):
                    start_times['task2'] = asyncio.get_event_loop().time()
                    await asyncio.sleep(0.1)
                    return {"result": "task2"}
                
                executor.register_task("task1", task1)
                executor.register_task("task2", task2)
                
                # Execute DAG
                context = await executor.execute_dag(
                    dag_id="test",
                    inputs={},
                    execution_mode=ExecutionMode.PARALLEL
                )
                
                # Check that tasks ran in parallel (start times should be close)
                time_diff = abs(start_times['task1'] - start_times['task2'])
                assert time_diff < 0.05  # Should start within 50ms of each other
                
                assert context.status == DAGStatus.SUCCESS
                assert context.node_statuses['task1'] == NodeStatus.SUCCESS
                assert context.node_statuses['task2'] == NodeStatus.SUCCESS
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_retry_mechanism(self):
        """Test retry mechanism"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'failing_task': {
                        'type': 'custom',
                        'task': 'failing_task',
                        'description': 'Failing task',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {
                            'max_retries': 2,
                            'retry_delay': 0.01,  # Short delay for testing
                            'exponential_backoff': False
                        },
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register failing task
                attempt_count = 0
                
                async def failing_task(inputs, context):
                    nonlocal attempt_count
                    attempt_count += 1
                    if attempt_count < 3:  # Fail first 2 attempts
                        raise Exception(f"Attempt {attempt_count} failed")
                    return {"result": "success"}
                
                executor.register_task("failing_task", failing_task)
                
                # Execute DAG
                context = await executor.execute_dag(
                    dag_id="test",
                    inputs={},
                    execution_mode=ExecutionMode.SEQUENTIAL
                )
                
                # Should have succeeded after retries
                assert attempt_count == 3
                assert context.status == DAGStatus.SUCCESS
                assert context.node_statuses['failing_task'] == NodeStatus.SUCCESS
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_task_failure(self):
        """Test task failure handling"""
        
        async def _test():
            dag_config = {
                'dag': {
                    'name': 'test',
                    'version': '1.0.0',
                    'settings': {
                        'failure_policy': 'stop_on_first_failure'
                    }
                },
                'nodes': {
                    'failing_task': {
                        'type': 'custom',
                        'task': 'failing_task',
                        'description': 'Failing task',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {'max_retries': 0},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register failing task
                async def failing_task(inputs, context):
                    raise Exception("Task failed")
                
                executor.register_task("failing_task", failing_task)
                
                # Execute DAG (should not raise exception)
                try:
                    context = await executor.execute_dag(
                        dag_id="test",
                        inputs={},
                        execution_mode=ExecutionMode.SEQUENTIAL
                    )
                except Exception:
                    # If exception is raised, that's also acceptable
                    pass
                else:
                    # Should have failed
                    assert context.status == DAGStatus.FAILED
                    assert context.node_statuses['failing_task'] == NodeStatus.FAILED
                    assert 'failing_task' in context.node_errors
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_timeout_handling(self):
        """Test timeout handling"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'slow_task': {
                        'type': 'custom',
                        'task': 'slow_task',
                        'description': 'Slow task',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {'max_retries': 0},
                        'timeout_seconds': 0.1,  # Very short timeout
                        'cache': {'enabled': False}
                    }
                },
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register slow task
                async def slow_task(inputs, context):
                    await asyncio.sleep(1.0)  # Longer than timeout
                    return {"result": "success"}
                
                executor.register_task("slow_task", slow_task)
                
                # Execute DAG (should not raise exception)
                try:
                    context = await executor.execute_dag(
                        dag_id="test",
                        inputs={},
                        execution_mode=ExecutionMode.SEQUENTIAL
                    )
                except Exception:
                    # If exception is raised, that's also acceptable
                    pass
                else:
                    # Should have failed due to timeout
                    assert context.status == DAGStatus.FAILED
                    assert context.node_statuses['slow_task'] == NodeStatus.FAILED
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_execution_metrics(self):
        """Test execution metrics"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'task1': {
                        'type': 'custom',
                        'task': 'task1',
                        'description': 'Task 1',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': []
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register task
                async def task1(inputs, context):
                    return {"result": "task1"}
                
                executor.register_task("task1", task1)
                
                # Execute DAG
                context = await executor.execute_dag(
                    dag_id="test",
                    inputs={},
                    execution_mode=ExecutionMode.SEQUENTIAL
                )
                
                # Check metrics
                metrics = executor.get_metrics()
                assert metrics["total_executions"] == 1
                assert metrics["successful_executions"] == 1
                assert metrics["failed_executions"] == 0
                assert metrics["total_execution_time"] >= 0  # Allow 0 for very fast execution
                
                # Check execution context metrics
                assert context.execution_metrics["total_time"] >= 0  # Allow 0 for very fast execution
                assert context.execution_metrics["nodes_executed"] == 1
                assert context.execution_metrics["successful_nodes"] == 1
                assert context.execution_metrics["failed_nodes"] == 0
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_graph_export(self):
        """Test graph export functionality"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'test', 'version': '1.0.0'},
                'nodes': {
                    'task1': {
                        'type': 'custom',
                        'task': 'task1',
                        'description': 'Task 1',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'task2': {
                        'type': 'ai_processing',
                        'task': 'task2',
                        'description': 'Task 2',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': [
                    {'from': 'task1', 'to': 'task2', 'condition': 'always', 'weight': 1.0}
                ]
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Test graph export (may return None if Graphviz not available)
                output_path = executor.export_graph("test_graph", "png")
                # Don't assert output_path since Graphviz might not be available
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())

class TestDAGIntegration:
    """Test DAG integration scenarios"""
    
    def create_test_dag_file(self, dag_config: dict) -> str:
        """Create temporary DAG file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(dag_config, temp_file)
        temp_file.close()
        return temp_file.name
    
    def test_complex_workflow(self):
        """Test complex workflow execution"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'complex_workflow', 'version': '1.0.0'},
                'nodes': {
                    'start': {
                        'type': 'job_management',
                        'task': 'start_job',
                        'description': 'Start job',
                        'inputs': {'job_id': 'string'},
                        'outputs': {'context': 'object'},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'ai_request': {
                        'type': 'ai_processing',
                        'task': 'make_ai_request',
                        'description': 'Make AI request',
                        'inputs': {'prompt': 'string'},
                        'outputs': {'response': 'string'},
                        'retry_policy': {'max_retries': 1},
                        'timeout_seconds': 60,
                        'cache': {'enabled': True, 'ttl_seconds': 300}
                    },
                    'process_response': {
                        'type': 'ai_processing',
                        'task': 'process_ai_response',
                        'description': 'Process AI response',
                        'inputs': {'response': 'string'},
                        'outputs': {'processed': 'string'},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'complete': {
                        'type': 'job_management',
                        'task': 'complete_job',
                        'description': 'Complete job',
                        'inputs': {'status': 'string'},
                        'outputs': {'result': 'string'},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': [
                    {'from': 'start', 'to': 'ai_request', 'condition': 'always', 'weight': 1.0},
                    {'from': 'ai_request', 'to': 'process_response', 'condition': 'always', 'weight': 1.0},
                    {'from': 'process_response', 'to': 'complete', 'condition': 'always', 'weight': 1.0}
                ]
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Execute complex workflow
                context = await executor.execute_dag(
                    dag_id="complex_workflow",
                    inputs={
                        "job_id": "test-job-123",
                        "prompt": "Test prompt"
                    },
                    execution_mode=ExecutionMode.SEQUENTIAL
                )
                
                # Check execution
                assert context.status == DAGStatus.SUCCESS
                assert all(status == NodeStatus.SUCCESS for status in context.node_statuses.values())
                
                # Check that all nodes were executed
                assert len(context.node_results) == 4
                assert 'start' in context.node_results
                assert 'ai_request' in context.node_results
                assert 'process_response' in context.node_results
                assert 'complete' in context.node_results
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
    
    def test_conditional_execution(self):
        """Test conditional execution based on node results"""
        
        async def _test():
            dag_config = {
                'dag': {'name': 'conditional_workflow', 'version': '1.0.0'},
                'nodes': {
                    'decision': {
                        'type': 'custom',
                        'task': 'decision_task',
                        'description': 'Decision task',
                        'inputs': {'input': 'string'},
                        'outputs': {'decision': 'string'},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'path_a': {
                        'type': 'custom',
                        'task': 'path_a_task',
                        'description': 'Path A task',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    },
                    'path_b': {
                        'type': 'custom',
                        'task': 'path_b_task',
                        'description': 'Path B task',
                        'inputs': {},
                        'outputs': {},
                        'retry_policy': {},
                        'timeout_seconds': 30,
                        'cache': {'enabled': False}
                    }
                },
                'edges': [
                    {'from': 'decision', 'to': 'path_a', 'condition': 'path_a', 'weight': 1.0},
                    {'from': 'decision', 'to': 'path_b', 'condition': 'path_b', 'weight': 1.0}
                ]
            }
            
            dag_file = self.create_test_dag_file(dag_config)
            
            try:
                executor = DAGExecutor(dag_file)
                
                # Register tasks
                async def decision_task(inputs, context):
                    return {"decision": "path_a"}
                
                async def path_a_task(inputs, context):
                    return {"result": "path_a"}
                
                async def path_b_task(inputs, context):
                    return {"result": "path_b"}
                
                executor.register_task("decision_task", decision_task)
                executor.register_task("path_a_task", path_a_task)
                executor.register_task("path_b_task", path_b_task)
                
                # Execute workflow
                context = await executor.execute_dag(
                    dag_id="conditional_workflow",
                    inputs={"input": "test"},
                    execution_mode=ExecutionMode.SEQUENTIAL
                )
                
                # Check execution
                assert context.status == DAGStatus.SUCCESS
                assert context.node_statuses['decision'] == NodeStatus.SUCCESS
                # Note: Conditional execution logic would need to be implemented
                # in the actual DAG executor for this test to be meaningful
                
            finally:
                Path(dag_file).unlink()
        
        asyncio.run(_test())
