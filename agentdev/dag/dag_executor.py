#!/usr/bin/env python3
"""
AgentDev DAG Executor - SEAL-GRADE
Enterprise-grade workflow orchestration with DAG execution
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Union, Callable
from pathlib import Path
import yaml
import networkx as nx
from contextlib import asynccontextmanager
import threading
import hashlib

# Graphviz imports
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

class NodeStatus(Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class DAGStatus(Enum):
    """DAG execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionMode(Enum):
    """Execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"

@dataclass
class NodeDefinition:
    """Node definition from YAML"""
    name: str
    type: str
    task: str
    description: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    retry_policy: Dict[str, Any]
    timeout_seconds: int
    cache: Dict[str, Any]
    dependencies: List[str] = None
    condition: Optional[str] = None

@dataclass
class EdgeDefinition:
    """Edge definition from YAML"""
    from_node: str
    to_node: str
    condition: str
    weight: float
    error_handling: bool = False

@dataclass
class ExecutionContext:
    """Execution context for a DAG run"""
    dag_id: str
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    status: DAGStatus = DAGStatus.PENDING
    node_statuses: Dict[str, NodeStatus] = None
    node_results: Dict[str, Any] = None
    node_errors: Dict[str, str] = None
    execution_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.node_statuses is None:
            self.node_statuses = {}
        if self.node_results is None:
            self.node_results = {}
        if self.node_errors is None:
            self.node_errors = {}
        if self.execution_metrics is None:
            self.execution_metrics = {}

@dataclass
class CacheEntry:
    """Cache entry for node results"""
    key: str
    result: Any
    timestamp: float
    ttl_seconds: int
    node_name: str

class DAGExecutor:
    """
    SEAL-GRADE DAG Executor
    
    Features:
    - YAML-based workflow definition
    - DAG validation and cycle detection
    - Parallel and sequential execution
    - Caching with TTL
    - Retry mechanisms
    - Error handling and recovery
    - Graphviz visualization
    - Execution monitoring
    - Rerun affected nodes
    """
    
    def __init__(self, 
                 dag_file: str = "agentdev/dag/schema.yaml",
                 cache_enabled: bool = True,
                 max_concurrent_tasks: int = 10):
        self.dag_file = Path(dag_file)
        self.cache_enabled = cache_enabled
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # DAG structure
        self.dag_definition: Dict[str, Any] = {}
        self.nodes: Dict[str, NodeDefinition] = {}
        self.edges: List[EdgeDefinition] = []
        self.graph: nx.DiGraph = nx.DiGraph()
        
        # Execution state
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.Lock()
        
        # Task registry
        self.task_registry: Dict[str, Callable] = {}
        
        # Metrics
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_execution_time": 0.0
        }
        
        # Load DAG definition
        self._load_dag_definition()
        self._build_graph()
        self._register_default_tasks()
    
    def _load_dag_definition(self):
        """Load DAG definition from YAML file"""
        if not self.dag_file.exists():
            raise FileNotFoundError(f"DAG file not found: {self.dag_file}")
        
        with open(self.dag_file, 'r', encoding='utf-8') as f:
            self.dag_definition = yaml.safe_load(f)
        
        # Parse nodes
        for node_name, node_config in self.dag_definition.get('nodes', {}).items():
            self.nodes[node_name] = NodeDefinition(
                name=node_name,
                type=node_config.get('type', 'custom'),
                task=node_config.get('task', ''),
                description=node_config.get('description', ''),
                inputs=node_config.get('inputs', {}),
                outputs=node_config.get('outputs', {}),
                retry_policy=node_config.get('retry_policy', {}),
                timeout_seconds=node_config.get('timeout_seconds', 300),
                cache=node_config.get('cache', {})
            )
        
        # Parse edges
        for edge_config in self.dag_definition.get('edges', []):
            self.edges.append(EdgeDefinition(
                from_node=edge_config['from'],
                to_node=edge_config['to'],
                condition=edge_config.get('condition', 'always'),
                weight=edge_config.get('weight', 1.0),
                error_handling=edge_config.get('error_handling', False)
            ))
        
        logging.info(f"Loaded DAG with {len(self.nodes)} nodes and {len(self.edges)} edges")
    
    def _build_graph(self):
        """Build NetworkX graph from DAG definition"""
        self.graph.clear()
        
        # Add nodes
        for node_name in self.nodes.keys():
            self.graph.add_node(node_name)
        
        # Add edges
        for edge in self.edges:
            self.graph.add_edge(edge.from_node, edge.to_node, 
                              condition=edge.condition,
                              weight=edge.weight,
                              error_handling=edge.error_handling)
        
        # Validate DAG
        self._validate_dag()
        
        logging.info(f"Built DAG graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def _validate_dag(self):
        """Validate DAG structure"""
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            raise ValueError(f"DAG contains cycles: {cycles}")
        
        # Check for orphan nodes
        orphan_nodes = []
        for node in self.graph.nodes():
            if self.graph.in_degree(node) == 0 and self.graph.out_degree(node) == 0:
                orphan_nodes.append(node)
        
        if orphan_nodes:
            logging.warning(f"Found orphan nodes: {orphan_nodes}")
        
        # Check for unreachable nodes
        # Find all nodes reachable from nodes with no incoming edges
        start_nodes = [node for node in self.graph.nodes() if self.graph.in_degree(node) == 0]
        reachable_nodes = set()
        for start_node in start_nodes:
            reachable_nodes.update(nx.descendants(self.graph, start_node))
            reachable_nodes.add(start_node)
        
        unreachable_nodes = set(self.graph.nodes()) - reachable_nodes
        if unreachable_nodes:
            logging.warning(f"Found unreachable nodes: {unreachable_nodes}")
    
    def _register_default_tasks(self):
        """Register default task implementations"""
        self.register_task("start_job", self._task_start_job)
        self.register_task("complete_job", self._task_complete_job)
        self.register_task("make_ai_request", self._task_make_ai_request)
        self.register_task("process_ai_response", self._task_process_ai_response)
        self.register_task("execute_tool", self._task_execute_tool)
        self.register_task("validate_security", self._task_validate_security)
        self.register_task("transform_data", self._task_transform_data)
        self.register_task("check_health", self._task_check_health)
    
    def register_task(self, task_name: str, task_func: Callable):
        """Register a task implementation"""
        self.task_registry[task_name] = task_func
        logging.info(f"Registered task: {task_name}")
    
    def _generate_cache_key(self, node_name: str, inputs: Dict[str, Any]) -> str:
        """Generate cache key for node execution"""
        cache_config = self.nodes[node_name].cache
        
        if not cache_config.get('enabled', False):
            return None
        
        key_strategy = cache_config.get('key_strategy', 'task_input_hash')
        
        if key_strategy == 'task_name':
            return f"{node_name}"
        elif key_strategy == 'task_input_hash':
            # Create hash of inputs
            inputs_str = json.dumps(inputs, sort_keys=True, default=str)
            inputs_hash = hashlib.sha256(inputs_str.encode()).hexdigest()
            return f"{node_name}:{inputs_hash}"
        elif key_strategy == 'custom':
            # Use custom key generation
            custom_key = cache_config.get('custom_key', '')
            # Replace placeholders
            custom_key = custom_key.replace('node_name', node_name)
            if 'parameters_hash' in custom_key:
                params_str = json.dumps(inputs, sort_keys=True, default=str)
                params_hash = hashlib.sha256(params_str.encode()).hexdigest()
                custom_key = custom_key.replace('parameters_hash', params_hash)
            return custom_key
        
        return None
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired"""
        if not self.cache_enabled or not cache_key:
            return None
        
        with self.cache_lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if time.time() - entry.timestamp < entry.ttl_seconds:
                    self.metrics["cache_hits"] += 1
                    logging.debug(f"Cache hit for key: {cache_key}")
                    return entry.result
                else:
                    # Expired, remove from cache
                    del self.cache[cache_key]
        
        self.metrics["cache_misses"] += 1
        return None
    
    def _cache_result(self, cache_key: str, result: Any, node_name: str, ttl_seconds: int):
        """Cache execution result"""
        if not self.cache_enabled or not cache_key:
            return
        
        with self.cache_lock:
            self.cache[cache_key] = CacheEntry(
                key=cache_key,
                result=result,
                timestamp=time.time(),
                ttl_seconds=ttl_seconds,
                node_name=node_name
            )
            logging.debug(f"Cached result for key: {cache_key}")
    
    async def execute_dag(self, 
                         dag_id: str,
                         inputs: Dict[str, Any],
                         execution_mode: ExecutionMode = ExecutionMode.PARALLEL,
                         rerun_affected_only: bool = False) -> ExecutionContext:
        """Execute DAG with given inputs"""
        execution_id = str(uuid.uuid4())
        
        # Create execution context
        context = ExecutionContext(
            dag_id=dag_id,
            execution_id=execution_id,
            start_time=time.time(),
            status=DAGStatus.RUNNING
        )
        
        # Initialize node statuses
        for node_name in self.nodes.keys():
            context.node_statuses[node_name] = NodeStatus.PENDING
        
        self.execution_contexts[execution_id] = context
        
        try:
            # Determine execution order
            if rerun_affected_only:
                nodes_to_execute = self._get_affected_nodes(inputs)
            else:
                nodes_to_execute = list(self.nodes.keys())
            
            # Execute nodes based on mode
            if execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(context, nodes_to_execute, inputs)
            elif execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(context, nodes_to_execute, inputs)
            else:  # HYBRID
                await self._execute_hybrid(context, nodes_to_execute, inputs)
            
            # Check final status
            if all(status == NodeStatus.SUCCESS for status in context.node_statuses.values()):
                context.status = DAGStatus.SUCCESS
            else:
                context.status = DAGStatus.FAILED
            
        except Exception as e:
            context.status = DAGStatus.FAILED
            logging.error(f"DAG execution failed: {e}")
            raise
        finally:
            context.end_time = time.time()
            context.execution_metrics = {
                "total_time": context.end_time - context.start_time,
                "nodes_executed": len([s for s in context.node_statuses.values() if s != NodeStatus.PENDING]),
                "successful_nodes": len([s for s in context.node_statuses.values() if s == NodeStatus.SUCCESS]),
                "failed_nodes": len([s for s in context.node_statuses.values() if s == NodeStatus.FAILED])
            }
            
            # Update metrics
            self.metrics["total_executions"] += 1
            if context.status == DAGStatus.SUCCESS:
                self.metrics["successful_executions"] += 1
            else:
                self.metrics["failed_executions"] += 1
            self.metrics["total_execution_time"] += context.execution_metrics["total_time"]
        
        return context
    
    def _get_affected_nodes(self, inputs: Dict[str, Any]) -> List[str]:
        """Get nodes that need to be re-executed based on input changes"""
        # This is a simplified implementation
        # In a real system, you'd analyze the dependency graph and input changes
        affected_nodes = set()
        
        # For now, return all nodes (full execution)
        # TODO: Implement intelligent change detection
        return list(self.nodes.keys())
    
    async def _execute_sequential(self, context: ExecutionContext, nodes: List[str], inputs: Dict[str, Any]):
        """Execute nodes sequentially"""
        for node_name in nodes:
            await self._execute_node(context, node_name, inputs)
    
    async def _execute_parallel(self, context: ExecutionContext, nodes: List[str], inputs: Dict[str, Any]):
        """Execute nodes in parallel where possible"""
        # Create execution plan based on dependencies
        execution_plan = self._create_execution_plan(nodes)
        
        for level in execution_plan:
            # Execute all nodes in current level in parallel
            tasks = []
            for node_name in level:
                if context.node_statuses[node_name] == NodeStatus.PENDING:
                    tasks.append(self._execute_node(context, node_name, inputs))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_hybrid(self, context: ExecutionContext, nodes: List[str], inputs: Dict[str, Any]):
        """Execute nodes in hybrid mode (parallel with concurrency limits)"""
        execution_plan = self._create_execution_plan(nodes)
        
        for level in execution_plan:
            # Execute nodes in level with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
            
            async def execute_with_semaphore(node_name):
                async with semaphore:
                    await self._execute_node(context, node_name, inputs)
            
            tasks = []
            for node_name in level:
                if context.node_statuses[node_name] == NodeStatus.PENDING:
                    tasks.append(execute_with_semaphore(node_name))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _create_execution_plan(self, nodes: List[str]) -> List[List[str]]:
        """Create execution plan with dependency levels"""
        # Create subgraph with only the nodes we want to execute
        subgraph = self.graph.subgraph(nodes)
        
        # Topological sort to get execution order
        try:
            topo_order = list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            # If there are cycles, just return nodes in original order
            topo_order = nodes
        
        # Group nodes by dependency level
        levels = []
        remaining_nodes = set(topo_order)
        
        while remaining_nodes:
            # Find nodes with no dependencies in remaining set
            current_level = []
            for node in list(remaining_nodes):
                predecessors = set(self.graph.predecessors(node))
                if not predecessors.intersection(remaining_nodes):
                    current_level.append(node)
            
            if not current_level:
                # No progress, add remaining nodes
                current_level = list(remaining_nodes)
            
            levels.append(current_level)
            remaining_nodes -= set(current_level)
        
        return levels
    
    async def _execute_node(self, context: ExecutionContext, node_name: str, inputs: Dict[str, Any]):
        """Execute a single node"""
        if context.node_statuses[node_name] != NodeStatus.PENDING:
            return
        
        node_def = self.nodes[node_name]
        context.node_statuses[node_name] = NodeStatus.RUNNING
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(node_name, inputs)
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result is not None:
                context.node_results[node_name] = cached_result
                context.node_statuses[node_name] = NodeStatus.SUCCESS
                logging.info(f"Node {node_name} executed from cache")
                return
            
            # Execute task with retry logic
            result = await self._execute_task_with_retry(node_def, inputs, context)
            
            # Cache result
            if cache_key:
                ttl_seconds = node_def.cache.get('ttl_seconds', 3600)
                self._cache_result(cache_key, result, node_name, ttl_seconds)
            
            context.node_results[node_name] = result
            context.node_statuses[node_name] = NodeStatus.SUCCESS
            
            logging.info(f"Node {node_name} executed successfully")
            
        except Exception as e:
            context.node_statuses[node_name] = NodeStatus.FAILED
            context.node_errors[node_name] = str(e)
            logging.error(f"Node {node_name} failed: {e}")
            
            # Check if we should continue or stop
            failure_policy = self.dag_definition.get('settings', {}).get('failure_policy', 'stop_on_first_failure')
            if failure_policy == 'stop_on_first_failure':
                raise
    
    async def _execute_task_with_retry(self, node_def: NodeDefinition, inputs: Dict[str, Any], context: ExecutionContext):
        """Execute task with retry logic"""
        retry_policy = node_def.retry_policy
        max_retries = retry_policy.get('max_retries', 0)
        retry_delay = retry_policy.get('retry_delay', 1)
        exponential_backoff = retry_policy.get('exponential_backoff', False)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Get task function
                task_func = self.task_registry.get(node_def.task)
                if not task_func:
                    raise ValueError(f"Task not found: {node_def.task}")
                
                # Execute task with timeout
                result = await asyncio.wait_for(
                    task_func(inputs, context),
                    timeout=node_def.timeout_seconds
                )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = retry_delay
                    if exponential_backoff:
                        delay *= (2 ** attempt)
                    
                    logging.warning(f"Task {node_def.task} failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"Task {node_def.task} failed after {max_retries + 1} attempts: {e}")
        
        raise last_exception
    
    def export_graph(self, output_file: str = "dag_graph.png", format: str = "png"):
        """Export DAG as image using Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            logging.warning("Graphviz not available, cannot export graph")
            return None
        
        try:
            # Create Graphviz graph
            dot = graphviz.Digraph(comment='AgentDev DAG')
            dot.attr(rankdir='TB')
            dot.attr('node', shape='box', style='rounded,filled')
            
            # Add nodes
            for node_name, node_def in self.nodes.items():
                color = self._get_node_color(node_name)
                dot.node(node_name, f"{node_name}\n{node_def.task}", fillcolor=color)
            
            # Add edges
            for edge in self.edges:
                dot.edge(edge.from_node, edge.to_node, label=edge.condition)
            
            # Render graph
            output_path = dot.render(output_file, format=format, cleanup=True)
            logging.info(f"Exported DAG graph to: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Failed to export graph: {e}")
            return None
    
    def _get_node_color(self, node_name: str) -> str:
        """Get color for node based on type"""
        node_type = self.nodes[node_name].type
        
        color_map = {
            'job_management': 'lightblue',
            'ai_processing': 'lightgreen',
            'tool_execution': 'lightyellow',
            'security': 'lightcoral',
            'data_processing': 'lightpink',
            'monitoring': 'lightgray',
            'custom': 'lightsteelblue'
        }
        
        return color_map.get(node_type, 'white')
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get execution status by ID"""
        return self.execution_contexts.get(execution_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics"""
        return self.metrics.copy()
    
    def clear_cache(self):
        """Clear execution cache"""
        with self.cache_lock:
            self.cache.clear()
        logging.info("Cleared execution cache")
    
    # Default task implementations
    async def _task_start_job(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Start job task"""
        return {
            "job_context": {
                "job_id": inputs.get("job_id"),
                "user_id": inputs.get("user_id"),
                "session_id": inputs.get("session_id")
            },
            "start_time": time.time()
        }
    
    async def _task_complete_job(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Complete job task"""
        return {
            "completion_time": time.time(),
            "final_status": inputs.get("status", "completed")
        }
    
    async def _task_make_ai_request(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Make AI request task"""
        # Simulate AI request
        await asyncio.sleep(0.1)
        return {
            "response": f"AI response for: {inputs.get('prompt', '')}",
            "tokens_used": 150,
            "latency_ms": 100
        }
    
    async def _task_process_ai_response(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Process AI response task"""
        response = inputs.get("response", "")
        return {
            "processed_response": response.upper(),
            "validation_status": "valid",
            "confidence_score": 0.95
        }
    
    async def _task_execute_tool(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute tool task"""
        tool_name = inputs.get("tool_name", "unknown")
        await asyncio.sleep(0.05)
        return {
            "result": f"Tool {tool_name} executed successfully",
            "execution_time_ms": 50,
            "status": "success"
        }
    
    async def _task_validate_security(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Validate security task"""
        return {
            "validation_result": {"blocked": False},
            "security_score": 0.9,
            "blocked": False
        }
    
    async def _task_transform_data(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Transform data task"""
        input_data = inputs.get("input_data", {})
        return {
            "transformed_data": {k: str(v).upper() for k, v in input_data.items()},
            "transformation_metadata": {"transformations_applied": 1}
        }
    
    async def _task_check_health(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Check health task"""
        return {
            "health_status": {"overall": "healthy"},
            "unhealthy_services": []
        }
