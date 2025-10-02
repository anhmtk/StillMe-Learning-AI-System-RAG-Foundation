#!/usr/bin/env python3
"""
StillMe AgentDev - DAG Engine
Enterprise-grade workflow orchestration with DAG execution and complex dependencies
"""

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import networkx as nx
import yaml


class NodeStatus(Enum):
    """DAG node status"""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class DAGStatus(Enum):
    """DAG execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionStrategy(Enum):
    """Execution strategies"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class DAGNode:
    """DAG node definition"""

    node_id: str
    name: str
    description: str
    task_type: str
    command: str
    working_directory: Optional[str]
    environment: dict[str, str]
    dependencies: list[str]
    retry_count: int
    timeout: int
    priority: int
    condition: Optional[str]
    on_success: Optional[str]
    on_failure: Optional[str]
    resources: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class DAGExecution:
    """DAG execution instance"""

    execution_id: str
    dag_id: str
    status: DAGStatus
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    nodes_status: dict[str, NodeStatus]
    nodes_output: dict[str, Any]
    nodes_errors: dict[str, str]
    execution_log: list[dict[str, Any]]
    variables: dict[str, Any]
    context: dict[str, Any]


@dataclass
class ExecutionResult:
    """Node execution result"""

    node_id: str
    status: NodeStatus
    start_time: float
    end_time: float
    duration: float
    output: Any
    error: Optional[str]
    retry_count: int
    resources_used: dict[str, Any]


class DAGEngine:
    """Enterprise DAG execution engine"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.dags: dict[str, nx.DiGraph] = {}
        self.executions: dict[str, DAGExecution] = {}
        self.node_handlers: dict[str, Callable] = {}
        self.resource_pools: dict[str, dict[str, Any]] = {}
        self.running = False

    def _load_config(self, config_path: Optional[str] = None) -> dict[str, Any]:
        """Load DAG engine configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/dag_engine.yaml")

        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                "max_concurrent_nodes": 10,
                "default_timeout": 3600,
                "default_retry_count": 3,
                "execution_strategy": "adaptive",
                "resource_management": {
                    "enabled": True,
                    "cpu_limit": 4,
                    "memory_limit": "8GB",
                    "disk_limit": "100GB",
                },
                "monitoring": {
                    "enabled": True,
                    "metrics_interval": 30,
                    "log_level": "INFO",
                },
                "persistence": {
                    "enabled": True,
                    "checkpoint_interval": 60,
                    "max_execution_history": 1000,
                },
            }

    def load_dag(self, dag_file: str) -> str:
        """Load DAG from YAML file"""
        try:
            dag_path = Path(dag_file)

            if not dag_path.exists():
                raise FileNotFoundError(f"DAG file not found: {dag_path}")

            with open(dag_path) as f:
                dag_data = yaml.safe_load(f)

            dag_id = dag_data["id"]
            dag_graph = nx.DiGraph()

            # Add nodes
            for node_data in dag_data.get("nodes", []):
                node = DAGNode(
                    node_id=node_data["id"],
                    name=node_data["name"],
                    description=node_data.get("description", ""),
                    task_type=node_data.get("task_type", "command"),
                    command=node_data["command"],
                    working_directory=node_data.get("working_directory"),
                    environment=node_data.get("environment", {}),
                    dependencies=node_data.get("dependencies", []),
                    retry_count=node_data.get(
                        "retry_count", self.config["default_retry_count"]
                    ),
                    timeout=node_data.get("timeout", self.config["default_timeout"]),
                    priority=node_data.get("priority", 0),
                    condition=node_data.get("condition"),
                    on_success=node_data.get("on_success"),
                    on_failure=node_data.get("on_failure"),
                    resources=node_data.get("resources", {}),
                    metadata=node_data.get("metadata", {}),
                )

                dag_graph.add_node(node.node_id, node=node)

            # Add edges based on dependencies
            for node_data in dag_data.get("nodes", []):
                node_id = node_data["id"]
                for dep in node_data.get("dependencies", []):
                    if dep in dag_graph.nodes:
                        dag_graph.add_edge(dep, node_id)

            # Validate DAG (no cycles)
            if not nx.is_directed_acyclic_graph(dag_graph):
                raise ValueError(f"DAG contains cycles: {dag_id}")

            self.dags[dag_id] = dag_graph
            print(f"✅ DAG loaded: {dag_id} with {len(dag_graph.nodes)} nodes")
            return dag_id

        except Exception as e:
            print(f"⚠️ Failed to load DAG {dag_file}: {e}")
            raise

    def register_node_handler(self, task_type: str, handler: Callable):
        """Register custom node handler"""
        self.node_handlers[task_type] = handler
        print(f"✅ Node handler registered: {task_type}")

    def execute_dag(
        self,
        dag_id: str,
        variables: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Execute a DAG"""
        if dag_id not in self.dags:
            raise ValueError(f"DAG not found: {dag_id}")

        execution_id = str(uuid.uuid4())
        dag_graph = self.dags[dag_id]

        # Initialize execution
        execution = DAGExecution(
            execution_id=execution_id,
            dag_id=dag_id,
            status=DAGStatus.PENDING,
            start_time=time.time(),
            end_time=None,
            duration=None,
            nodes_status=dict.fromkeys(dag_graph.nodes, NodeStatus.PENDING),
            nodes_output={},
            nodes_errors={},
            execution_log=[],
            variables=variables or {},
            context=context or {},
        )

        self.executions[execution_id] = execution

        # Start execution
        asyncio.create_task(self._execute_dag_async(execution))

        print(f"🚀 DAG execution started: {execution_id}")
        return execution_id

    async def _execute_dag_async(self, execution: DAGExecution):
        """Execute DAG asynchronously"""
        try:
            execution.status = DAGStatus.RUNNING
            dag_graph = self.dags[execution.dag_id]

            # Get execution strategy
            strategy = ExecutionStrategy(
                self.config.get("execution_strategy", "adaptive")
            )

            if strategy == ExecutionStrategy.SEQUENTIAL:
                await self._execute_sequential(execution, dag_graph)
            elif strategy == ExecutionStrategy.PARALLEL:
                await self._execute_parallel(execution, dag_graph)
            else:  # ADAPTIVE
                await self._execute_adaptive(execution, dag_graph)

            # Determine final status
            if any(
                status == NodeStatus.FAILED
                for status in execution.nodes_status.values()
            ):
                execution.status = DAGStatus.FAILED
            else:
                execution.status = DAGStatus.COMPLETED

        except Exception as e:
            execution.status = DAGStatus.FAILED
            self._log_execution(execution, f"DAG execution failed: {e}")

        finally:
            execution.end_time = time.time()
            execution.duration = execution.end_time - execution.start_time

            # Save execution
            await self._save_execution(execution)

            print(
                f"🏁 DAG execution completed: {execution.execution_id} - {execution.status.value}"
            )

    async def _execute_sequential(self, execution: DAGExecution, dag_graph: nx.DiGraph):
        """Execute DAG nodes sequentially"""
        # Topological sort for sequential execution
        try:
            topo_order = list(nx.topological_sort(dag_graph))
        except nx.NetworkXError:
            raise ValueError("DAG contains cycles")

        for node_id in topo_order:
            if execution.status == DAGStatus.CANCELLED:
                break

            node = dag_graph.nodes[node_id]["node"]
            await self._execute_node(execution, node)

    async def _execute_parallel(self, execution: DAGExecution, dag_graph: nx.DiGraph):
        """Execute DAG nodes in parallel where possible"""
        completed_nodes = set()
        running_tasks = {}

        while len(completed_nodes) < len(dag_graph.nodes):
            # Find ready nodes
            ready_nodes = []
            for node_id in dag_graph.nodes:
                if (
                    node_id not in completed_nodes
                    and node_id not in running_tasks
                    and execution.nodes_status[node_id] == NodeStatus.PENDING
                ):
                    # Check if all dependencies are completed
                    dependencies = list(dag_graph.predecessors(node_id))
                    if all(dep in completed_nodes for dep in dependencies):
                        ready_nodes.append(node_id)

            # Execute ready nodes
            for node_id in ready_nodes:
                if len(running_tasks) >= self.config["max_concurrent_nodes"]:
                    break

                node = dag_graph.nodes[node_id]["node"]
                task = asyncio.create_task(self._execute_node(execution, node))
                running_tasks[node_id] = task

            # Wait for at least one task to complete
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.values(), return_when=asyncio.FIRST_COMPLETED
                )

                # Update completed nodes
                for task in done:
                    for node_id, node_task in running_tasks.items():
                        if node_task == task:
                            completed_nodes.add(node_id)
                            del running_tasks[node_id]
                            break

            # Check for failures
            if any(
                status == NodeStatus.FAILED
                for status in execution.nodes_status.values()
            ):
                break

    async def _execute_adaptive(self, execution: DAGExecution, dag_graph: nx.DiGraph):
        """Execute DAG with adaptive strategy"""
        # Start with parallel execution, fall back to sequential if needed
        try:
            await self._execute_parallel(execution, dag_graph)
        except Exception as e:
            self._log_execution(
                execution, f"Parallel execution failed, falling back to sequential: {e}"
            )
            await self._execute_sequential(execution, dag_graph)

    async def _execute_node(
        self, execution: DAGExecution, node: DAGNode
    ) -> ExecutionResult:
        """Execute a single DAG node"""
        start_time = time.time()
        execution.nodes_status[node.node_id] = NodeStatus.RUNNING

        self._log_execution(execution, f"Starting node: {node.name}")

        try:
            # Check condition
            if node.condition and not self._evaluate_condition(
                node.condition, execution
            ):
                execution.nodes_status[node.node_id] = NodeStatus.SKIPPED
                self._log_execution(
                    execution, f"Node skipped due to condition: {node.name}"
                )
                return ExecutionResult(
                    node_id=node.node_id,
                    status=NodeStatus.SKIPPED,
                    start_time=start_time,
                    end_time=time.time(),
                    duration=time.time() - start_time,
                    output=None,
                    error=None,
                    retry_count=0,
                    resources_used={},
                )

            # Execute node
            result = await self._run_node_task(execution, node)

            if result.status == NodeStatus.COMPLETED:
                execution.nodes_status[node.node_id] = NodeStatus.COMPLETED
                execution.nodes_output[node.node_id] = result.output
                self._log_execution(execution, f"Node completed: {node.name}")

                # Execute on_success action
                if node.on_success:
                    await self._execute_action(execution, node.on_success)
            else:
                execution.nodes_status[node.node_id] = NodeStatus.FAILED
                execution.nodes_errors[node.node_id] = result.error or "Unknown error"
                self._log_execution(
                    execution, f"Node failed: {node.name} - {result.error}"
                )

                # Execute on_failure action
                if node.on_failure:
                    await self._execute_action(execution, node.on_failure)

            return result

        except Exception as e:
            execution.nodes_status[node.node_id] = NodeStatus.FAILED
            execution.nodes_errors[node.node_id] = str(e)
            self._log_execution(execution, f"Node error: {node.name} - {e}")

            return ExecutionResult(
                node_id=node.node_id,
                status=NodeStatus.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration=time.time() - start_time,
                output=None,
                error=str(e),
                retry_count=0,
                resources_used={},
            )

    async def _run_node_task(
        self, execution: DAGExecution, node: DAGNode
    ) -> ExecutionResult:
        """Run the actual task for a node"""
        start_time = time.time()

        # Check if custom handler exists
        if node.task_type in self.node_handlers:
            handler = self.node_handlers[node.task_type]
            try:
                output = await handler(node, execution)
                return ExecutionResult(
                    node_id=node.node_id,
                    status=NodeStatus.COMPLETED,
                    start_time=start_time,
                    end_time=time.time(),
                    duration=time.time() - start_time,
                    output=output,
                    error=None,
                    retry_count=0,
                    resources_used={},
                )
            except Exception as e:
                return ExecutionResult(
                    node_id=node.node_id,
                    status=NodeStatus.FAILED,
                    start_time=start_time,
                    end_time=time.time(),
                    duration=time.time() - start_time,
                    output=None,
                    error=str(e),
                    retry_count=0,
                    resources_used={},
                )

        # Default command execution
        try:
            # Prepare environment
            env = {**execution.variables, **node.environment}

            # Set working directory
            cwd = node.working_directory or Path.cwd()

            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                node.command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=node.timeout
                )

                output = {
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "return_code": process.returncode,
                }

                if process.returncode == 0:
                    return ExecutionResult(
                        node_id=node.node_id,
                        status=NodeStatus.COMPLETED,
                        start_time=start_time,
                        end_time=time.time(),
                        duration=time.time() - start_time,
                        output=output,
                        error=None,
                        retry_count=0,
                        resources_used={},
                    )
                else:
                    return ExecutionResult(
                        node_id=node.node_id,
                        status=NodeStatus.FAILED,
                        start_time=start_time,
                        end_time=time.time(),
                        duration=time.time() - start_time,
                        output=output,
                        error=f"Command failed with return code {process.returncode}",
                        retry_count=0,
                        resources_used={},
                    )

            except asyncio.TimeoutError:
                process.kill()
                return ExecutionResult(
                    node_id=node.node_id,
                    status=NodeStatus.FAILED,
                    start_time=start_time,
                    end_time=time.time(),
                    duration=time.time() - start_time,
                    output=None,
                    error=f"Command timed out after {node.timeout}s",
                    retry_count=0,
                    resources_used={},
                )

        except Exception as e:
            return ExecutionResult(
                node_id=node.node_id,
                status=NodeStatus.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration=time.time() - start_time,
                output=None,
                error=str(e),
                retry_count=0,
                resources_used={},
            )

    def _evaluate_condition(self, condition: str, execution: DAGExecution) -> bool:
        """Evaluate node condition"""
        try:
            # Simple condition evaluation
            # In a real implementation, you'd use a proper expression evaluator
            context = {
                "execution": execution,
                "variables": execution.variables,
                "context": execution.context,
            }
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            self._log_execution(execution, f"Condition evaluation error: {e}")
            return False

    async def _execute_action(self, execution: DAGExecution, action: str):
        """Execute post-node action"""
        try:
            # Simple action execution
            # In a real implementation, you'd have a proper action system
            self._log_execution(execution, f"Executing action: {action}")
        except Exception as e:
            self._log_execution(execution, f"Action execution error: {e}")

    def _log_execution(self, execution: DAGExecution, message: str):
        """Log execution message"""
        log_entry = {"timestamp": time.time(), "message": message}
        execution.execution_log.append(log_entry)
        print(f"[{execution.execution_id}] {message}")

    async def _save_execution(self, execution: DAGExecution):
        """Save execution to disk"""
        try:
            if not self.config["persistence"]["enabled"]:
                return

            executions_dir = Path(".agentdev/executions")
            executions_dir.mkdir(parents=True, exist_ok=True)

            execution_file = executions_dir / f"{execution.execution_id}.json"

            # Convert to serializable format
            execution_data = asdict(execution)
            execution_data["status"] = execution.status.value
            execution_data["nodes_status"] = {
                node_id: status.value
                for node_id, status in execution.nodes_status.items()
            }

            with open(execution_file, "w") as f:
                json.dump(execution_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Failed to save execution: {e}")

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel DAG execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False

        if execution.status in [DAGStatus.PENDING, DAGStatus.RUNNING]:
            execution.status = DAGStatus.CANCELLED

            # Cancel running nodes
            for node_id, status in execution.nodes_status.items():
                if status == NodeStatus.RUNNING:
                    execution.nodes_status[node_id] = NodeStatus.CANCELLED

            self._log_execution(execution, "Execution cancelled")
            return True

        return False

    def get_execution_status(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Get execution status"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None

        return {
            "execution_id": execution.execution_id,
            "dag_id": execution.dag_id,
            "status": execution.status.value,
            "start_time": execution.start_time,
            "end_time": execution.end_time,
            "duration": execution.duration,
            "nodes_status": {
                node_id: status.value
                for node_id, status in execution.nodes_status.items()
            },
            "progress": self._calculate_progress(execution),
            "failed_nodes": [
                node_id
                for node_id, status in execution.nodes_status.items()
                if status == NodeStatus.FAILED
            ],
        }

    def _calculate_progress(self, execution: DAGExecution) -> float:
        """Calculate execution progress"""
        total_nodes = len(execution.nodes_status)
        if total_nodes == 0:
            return 0.0

        completed_nodes = len(
            [
                status
                for status in execution.nodes_status.values()
                if status in [NodeStatus.COMPLETED, NodeStatus.SKIPPED]
            ]
        )

        return completed_nodes / total_nodes

    def get_dag_statistics(self, dag_id: str) -> dict[str, Any]:
        """Get DAG statistics"""
        if dag_id not in self.dags:
            return {}

        dag_graph = self.dags[dag_id]
        executions = [e for e in self.executions.values() if e.dag_id == dag_id]

        # Calculate statistics
        total_executions = len(executions)
        successful_executions = len(
            [e for e in executions if e.status == DAGStatus.COMPLETED]
        )
        failed_executions = len([e for e in executions if e.status == DAGStatus.FAILED])

        success_rate = (
            successful_executions / total_executions if total_executions > 0 else 0
        )

        # Get recent executions
        recent_executions = sorted(
            executions, key=lambda x: x.start_time, reverse=True
        )[:5]

        return {
            "dag_id": dag_id,
            "node_count": len(dag_graph.nodes),
            "edge_count": len(dag_graph.edges),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": success_rate,
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "status": e.status.value,
                    "start_time": e.start_time,
                    "duration": e.duration,
                }
                for e in recent_executions
            ],
        }


# Global DAG engine instance
dag_engine = DAGEngine()


# Convenience functions
def load_dag(dag_file: str) -> str:
    """Load DAG from file"""
    return dag_engine.load_dag(dag_file)


def execute_dag(dag_id: str, variables: Optional[dict[str, Any]] = None) -> str:
    """Execute DAG"""
    return dag_engine.execute_dag(dag_id, variables)


def get_execution_status(execution_id: str) -> Optional[dict[str, Any]]:
    """Get execution status"""
    return dag_engine.get_execution_status(execution_id)


def cancel_execution(execution_id: str) -> bool:
    """Cancel execution"""
    return dag_engine.cancel_execution(execution_id)


# Example DAG definition
EXAMPLE_DAG = """
id: agentdev_deployment
name: AgentDev Deployment Pipeline
description: Complete deployment pipeline for AgentDev

nodes:
  - id: validate_config
    name: Validate Configuration
    description: Validate deployment configuration
    command: python -m agentdev.config.validator
    timeout: 300
    priority: 10

  - id: run_tests
    name: Run Tests
    description: Execute test suite
    command: pytest tests/ -v --cov=agentdev
    timeout: 1800
    dependencies: [validate_config]
    priority: 9

  - id: security_scan
    name: Security Scan
    description: Run security analysis
    command: python -m agentdev.security.scanner
    timeout: 600
    dependencies: [validate_config]
    priority: 8

  - id: build_artifacts
    name: Build Artifacts
    description: Build deployment artifacts
    command: python -m agentdev.build
    timeout: 1200
    dependencies: [run_tests, security_scan]
    priority: 7

  - id: deploy_staging
    name: Deploy to Staging
    description: Deploy to staging environment
    command: python -m agentdev.deploy --env=staging
    timeout: 1800
    dependencies: [build_artifacts]
    priority: 6

  - id: integration_tests
    name: Integration Tests
    description: Run integration tests on staging
    command: python -m agentdev.test.integration --env=staging
    timeout: 2400
    dependencies: [deploy_staging]
    priority: 5

  - id: deploy_production
    name: Deploy to Production
    description: Deploy to production environment
    command: python -m agentdev.deploy --env=production
    timeout: 1800
    dependencies: [integration_tests]
    priority: 4
    condition: "execution.variables.get('auto_deploy', False)"

  - id: notify_team
    name: Notify Team
    description: Send deployment notification
    command: python -m agentdev.notify --type=deployment
    dependencies: [deploy_production]
    priority: 1
"""

if __name__ == "__main__":

    async def main():
        # Example usage
        engine = DAGEngine()

        # Create example DAG file
        dag_file = Path("example_dag.yaml")
        with open(dag_file, "w") as f:
            f.write(EXAMPLE_DAG)

        try:
            # Load DAG
            dag_id = engine.load_dag("example_dag.yaml")

            # Execute DAG
            execution_id = engine.execute_dag(dag_id, {"auto_deploy": True})

            # Monitor execution
            while True:
                status = engine.get_execution_status(execution_id)
                if status:
                    print(
                        f"Progress: {status['progress']:.1%} - Status: {status['status']}"
                    )

                    if status["status"] in ["completed", "failed", "cancelled"]:
                        break

                await asyncio.sleep(5)

            # Get final status
            final_status = engine.get_execution_status(execution_id)
            print(f"Final status: {final_status}")

            # Get DAG statistics
            stats = engine.get_dag_statistics(dag_id)
            print(f"DAG statistics: {stats}")

        finally:
            # Cleanup
            if dag_file.exists():
                dag_file.unlink()

    asyncio.run(main())
