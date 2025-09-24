#!/usr/bin/env python3
"""
StillMe AgentDev - Automated Workflows
Enterprise-grade automated CI/CD workflows and pipeline orchestration
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
from pathlib import Path

class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class StepStatus(Enum):
    """Pipeline step status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class TriggerType(Enum):
    """Pipeline trigger types"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    TAG = "tag"
    RELEASE = "release"

@dataclass
class PipelineStep:
    """Pipeline step definition"""
    step_id: str
    name: str
    description: str
    command: str
    working_directory: Optional[str]
    environment: Dict[str, str]
    dependencies: List[str]
    timeout: int
    retry_count: int
    condition: Optional[str]
    artifacts: List[str]
    notifications: List[str]

@dataclass
class Pipeline:
    """Pipeline definition"""
    pipeline_id: str
    name: str
    description: str
    version: str
    triggers: List[TriggerType]
    steps: List[PipelineStep]
    environment: Dict[str, str]
    variables: Dict[str, str]
    notifications: Dict[str, Any]
    timeout: int
    parallel_execution: bool

@dataclass
class PipelineExecution:
    """Pipeline execution instance"""
    execution_id: str
    pipeline_id: str
    status: PipelineStatus
    trigger_type: TriggerType
    trigger_data: Dict[str, Any]
    started_at: float
    completed_at: Optional[float]
    duration: Optional[float]
    steps_executed: List[str]
    steps_failed: List[str]
    artifacts: List[str]
    logs: List[Dict[str, Any]]
    variables: Dict[str, str]

class AutomatedWorkflows:
    """Enterprise automated workflows system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.pipelines: Dict[str, Pipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.scheduled_jobs: Dict[str, Any] = {}
        self.webhook_handlers: Dict[str, Callable] = {}
        self.running = False
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load automated workflows configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/automated_workflows.yaml")
            
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return {
                'pipelines_directory': 'agent-dev/pipelines',
                'executions_directory': '.agentdev/executions',
                'artifacts_directory': '.agentdev/artifacts',
                'logs_directory': '.agentdev/logs',
                'default_timeout': 3600,
                'max_concurrent_executions': 5,
                'retention_days': 30,
                'notifications': {
                    'slack': {
                        'enabled': False,
                        'webhook_url': None
                    },
                    'email': {
                        'enabled': False,
                        'smtp_server': None,
                        'smtp_port': 587,
                        'username': None,
                        'password': None,
                        'recipients': []
                    }
                }
            }
    
    def load_pipeline(self, pipeline_file: str) -> Optional[Pipeline]:
        """Load pipeline from YAML file"""
        try:
            pipeline_path = Path(self.config['pipelines_directory']) / pipeline_file
            
            if not pipeline_path.exists():
                print(f"⚠️ Pipeline file not found: {pipeline_path}")
                return None
            
            with open(pipeline_path, 'r') as f:
                pipeline_data = yaml.safe_load(f)
            
            # Convert trigger strings to enums
            triggers = [TriggerType(t) for t in pipeline_data.get('triggers', [])]
            
            # Convert steps
            steps = []
            for step_data in pipeline_data.get('steps', []):
                step = PipelineStep(
                    step_id=step_data['id'],
                    name=step_data['name'],
                    description=step_data.get('description', ''),
                    command=step_data['command'],
                    working_directory=step_data.get('working_directory'),
                    environment=step_data.get('environment', {}),
                    dependencies=step_data.get('dependencies', []),
                    timeout=step_data.get('timeout', 300),
                    retry_count=step_data.get('retry_count', 0),
                    condition=step_data.get('condition'),
                    artifacts=step_data.get('artifacts', []),
                    notifications=step_data.get('notifications', [])
                )
                steps.append(step)
            
            pipeline = Pipeline(
                pipeline_id=pipeline_data['id'],
                name=pipeline_data['name'],
                description=pipeline_data.get('description', ''),
                version=pipeline_data.get('version', '1.0.0'),
                triggers=triggers,
                steps=steps,
                environment=pipeline_data.get('environment', {}),
                variables=pipeline_data.get('variables', {}),
                notifications=pipeline_data.get('notifications', {}),
                timeout=pipeline_data.get('timeout', self.config['default_timeout']),
                parallel_execution=pipeline_data.get('parallel_execution', False)
            )
            
            self.pipelines[pipeline.pipeline_id] = pipeline
            print(f"✅ Loaded pipeline: {pipeline.name}")
            return pipeline
            
        except Exception as e:
            print(f"⚠️ Failed to load pipeline {pipeline_file}: {e}")
            return None
    
    def load_all_pipelines(self):
        """Load all pipelines from directory"""
        pipelines_dir = Path(self.config['pipelines_directory'])
        
        if not pipelines_dir.exists():
            pipelines_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created pipelines directory: {pipelines_dir}")
            return
        
        for pipeline_file in pipelines_dir.glob("*.yaml"):
            self.load_pipeline(pipeline_file.name)
        
        print(f"📋 Loaded {len(self.pipelines)} pipelines")
    
    async def execute_pipeline(self, pipeline_id: str, trigger_type: TriggerType,
                             trigger_data: Optional[Dict[str, Any]] = None,
                             variables: Optional[Dict[str, str]] = None) -> str:
        """Execute a pipeline"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        
        # Check if trigger is allowed
        if trigger_type not in pipeline.triggers:
            raise ValueError(f"Trigger type {trigger_type.value} not allowed for pipeline {pipeline_id}")
        
        # Create execution
        execution_id = str(uuid.uuid4())
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_id=pipeline_id,
            status=PipelineStatus.PENDING,
            trigger_type=trigger_type,
            trigger_data=trigger_data or {},
            started_at=time.time(),
            completed_at=None,
            duration=None,
            steps_executed=[],
            steps_failed=[],
            artifacts=[],
            logs=[],
            variables={**pipeline.variables, **(variables or {})}
        )
        
        self.executions[execution_id] = execution
        
        # Start execution
        asyncio.create_task(self._execute_pipeline_async(execution))
        
        print(f"🚀 Pipeline execution started: {execution_id}")
        return execution_id
    
    async def _execute_pipeline_async(self, execution: PipelineExecution):
        """Execute pipeline asynchronously"""
        try:
            execution.status = PipelineStatus.RUNNING
            
            pipeline = self.pipelines[execution.pipeline_id]
            
            # Execute steps
            if pipeline.parallel_execution:
                await self._execute_steps_parallel(execution, pipeline)
            else:
                await self._execute_steps_sequential(execution, pipeline)
            
            # Determine final status
            if execution.steps_failed:
                execution.status = PipelineStatus.FAILED
            else:
                execution.status = PipelineStatus.SUCCESS
            
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            self._log_execution(execution, f"Pipeline execution failed: {e}")
        
        finally:
            execution.completed_at = time.time()
            execution.duration = execution.completed_at - execution.started_at
            
            # Save execution
            await self._save_execution(execution)
            
            # Send notifications
            await self._send_notifications(execution)
            
            print(f"🏁 Pipeline execution completed: {execution.execution_id} - {execution.status.value}")
    
    async def _execute_steps_sequential(self, execution: PipelineExecution, pipeline: Pipeline):
        """Execute pipeline steps sequentially"""
        executed_steps = set()
        
        while len(executed_steps) < len(pipeline.steps):
            # Find steps that can be executed (dependencies satisfied)
            ready_steps = []
            for step in pipeline.steps:
                if step.step_id in executed_steps:
                    continue
                
                # Check dependencies
                dependencies_satisfied = all(
                    dep in executed_steps for dep in step.dependencies
                )
                
                if dependencies_satisfied:
                    ready_steps.append(step)
            
            if not ready_steps:
                # No ready steps, check for circular dependencies
                remaining_steps = [s for s in pipeline.steps if s.step_id not in executed_steps]
                if remaining_steps:
                    raise Exception(f"Circular dependency detected in steps: {[s.step_id for s in remaining_steps]}")
                break
            
            # Execute ready steps
            for step in ready_steps:
                await self._execute_step(execution, step)
                executed_steps.add(step.step_id)
    
    async def _execute_steps_parallel(self, execution: PipelineExecution, pipeline: Pipeline):
        """Execute pipeline steps in parallel where possible"""
        # This is a simplified parallel execution
        # In a real implementation, you'd need a more sophisticated dependency resolver
        
        tasks = []
        for step in pipeline.steps:
            task = asyncio.create_task(self._execute_step(execution, step))
            tasks.append(task)
        
        # Wait for all steps to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                step = pipeline.steps[i]
                execution.steps_failed.append(step.step_id)
                self._log_execution(execution, f"Step {step.name} failed: {result}")
    
    async def _execute_step(self, execution: PipelineExecution, step: PipelineStep):
        """Execute a single pipeline step"""
        try:
            self._log_execution(execution, f"Starting step: {step.name}")
            
            # Check condition
            if step.condition and not self._evaluate_condition(step.condition, execution):
                self._log_execution(execution, f"Skipping step {step.name} due to condition")
                return
            
            # Execute command
            success = await self._run_command(execution, step)
            
            if success:
                execution.steps_executed.append(step.step_id)
                self._log_execution(execution, f"Step completed: {step.name}")
                
                # Collect artifacts
                for artifact in step.artifacts:
                    await self._collect_artifact(execution, artifact)
            else:
                execution.steps_failed.append(step.step_id)
                self._log_execution(execution, f"Step failed: {step.name}")
                
        except Exception as e:
            execution.steps_failed.append(step.step_id)
            self._log_execution(execution, f"Step error: {step.name} - {e}")
    
    async def _run_command(self, execution: PipelineExecution, step: PipelineStep) -> bool:
        """Run a command for a pipeline step"""
        try:
            # Prepare environment
            env = {**execution.variables, **step.environment}
            
            # Set working directory
            cwd = step.working_directory or Path.cwd()
            
            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                step.command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=step.timeout
                )
                
                # Log output
                if stdout:
                    self._log_execution(execution, f"STDOUT: {stdout.decode()}")
                if stderr:
                    self._log_execution(execution, f"STDERR: {stderr.decode()}")
                
                return process.returncode == 0
                
            except asyncio.TimeoutError:
                process.kill()
                self._log_execution(execution, f"Step timed out after {step.timeout}s")
                return False
                
        except Exception as e:
            self._log_execution(execution, f"Command execution error: {e}")
            return False
    
    def _evaluate_condition(self, condition: str, execution: PipelineExecution) -> bool:
        """Evaluate step condition"""
        try:
            # Simple condition evaluation
            # In a real implementation, you'd use a proper expression evaluator
            return eval(condition, {"execution": execution, "variables": execution.variables})
        except Exception as e:
            self._log_execution(execution, f"Condition evaluation error: {e}")
            return False
    
    async def _collect_artifact(self, execution: PipelineExecution, artifact_path: str):
        """Collect pipeline artifact"""
        try:
            artifacts_dir = Path(self.config['artifacts_directory']) / execution.execution_id
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy artifact to artifacts directory
            import shutil
            source_path = Path(artifact_path)
            if source_path.exists():
                dest_path = artifacts_dir / source_path.name
                shutil.copy2(source_path, dest_path)
                execution.artifacts.append(str(dest_path))
                self._log_execution(execution, f"Artifact collected: {artifact_path}")
            else:
                self._log_execution(execution, f"Artifact not found: {artifact_path}")
                
        except Exception as e:
            self._log_execution(execution, f"Artifact collection error: {e}")
    
    def _log_execution(self, execution: PipelineExecution, message: str):
        """Log execution message"""
        log_entry = {
            'timestamp': time.time(),
            'message': message
        }
        execution.logs.append(log_entry)
        print(f"[{execution.execution_id}] {message}")
    
    async def _save_execution(self, execution: PipelineExecution):
        """Save execution to disk"""
        try:
            executions_dir = Path(self.config['executions_directory'])
            executions_dir.mkdir(parents=True, exist_ok=True)
            
            execution_file = executions_dir / f"{execution.execution_id}.json"
            
            # Convert to serializable format
            execution_data = asdict(execution)
            execution_data['status'] = execution.status.value
            execution_data['trigger_type'] = execution.trigger_type.value
            
            with open(execution_file, 'w') as f:
                json.dump(execution_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Failed to save execution: {e}")
    
    async def _send_notifications(self, execution: PipelineExecution):
        """Send pipeline notifications"""
        try:
            pipeline = self.pipelines[execution.pipeline_id]
            notifications = pipeline.notifications
            
            # Slack notification
            if notifications.get('slack', {}).get('enabled'):
                await self._send_slack_notification(execution, notifications['slack'])
            
            # Email notification
            if notifications.get('email', {}).get('enabled'):
                await self._send_email_notification(execution, notifications['email'])
                
        except Exception as e:
            print(f"⚠️ Notification error: {e}")
    
    async def _send_slack_notification(self, execution: PipelineExecution, slack_config: Dict[str, Any]):
        """Send Slack notification"""
        # Implementation would depend on Slack API
        print(f"📱 Slack notification: Pipeline {execution.pipeline_id} - {execution.status.value}")
    
    async def _send_email_notification(self, execution: PipelineExecution, email_config: Dict[str, Any]):
        """Send email notification"""
        # Implementation would depend on SMTP
        print(f"📧 Email notification: Pipeline {execution.pipeline_id} - {execution.status.value}")
    
    def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get pipeline status and statistics"""
        if pipeline_id not in self.pipelines:
            return {}
        
        pipeline = self.pipelines[pipeline_id]
        executions = [e for e in self.executions.values() if e.pipeline_id == pipeline_id]
        
        # Calculate statistics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == PipelineStatus.SUCCESS])
        failed_executions = len([e for e in executions if e.status == PipelineStatus.FAILED])
        
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        # Get recent executions
        recent_executions = sorted(executions, key=lambda x: x.started_at, reverse=True)[:5]
        
        return {
            'pipeline_id': pipeline_id,
            'name': pipeline.name,
            'version': pipeline.version,
            'triggers': [t.value for t in pipeline.triggers],
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': success_rate,
            'recent_executions': [
                {
                    'execution_id': e.execution_id,
                    'status': e.status.value,
                    'started_at': e.started_at,
                    'duration': e.duration
                }
                for e in recent_executions
            ]
        }
    
    def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get execution logs"""
        execution = self.executions.get(execution_id)
        return execution.logs if execution else []
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel pipeline execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status in [PipelineStatus.PENDING, PipelineStatus.RUNNING]:
            execution.status = PipelineStatus.CANCELLED
            execution.completed_at = time.time()
            execution.duration = execution.completed_at - execution.started_at
            
            await self._save_execution(execution)
            print(f"🛑 Pipeline execution cancelled: {execution_id}")
            return True
        
        return False

# Global automated workflows instance
automated_workflows = AutomatedWorkflows()

# Convenience functions
def load_pipeline(pipeline_file: str) -> Optional[Pipeline]:
    """Load pipeline from file"""
    return automated_workflows.load_pipeline(pipeline_file)

async def execute_pipeline(pipeline_id: str, trigger_type: TriggerType,
                         trigger_data: Optional[Dict[str, Any]] = None) -> str:
    """Execute pipeline"""
    return await automated_workflows.execute_pipeline(pipeline_id, trigger_type, trigger_data)

def get_pipeline_status(pipeline_id: str) -> Dict[str, Any]:
    """Get pipeline status"""
    return automated_workflows.get_pipeline_status(pipeline_id)

if __name__ == "__main__":
    async def main():
        # Example usage
        workflows = AutomatedWorkflows()
        
        # Load all pipelines
        workflows.load_all_pipelines()
        
        # Execute a pipeline
        if workflows.pipelines:
            pipeline_id = list(workflows.pipelines.keys())[0]
            execution_id = await workflows.execute_pipeline(
                pipeline_id, 
                TriggerType.MANUAL,
                {"user": "developer"}
            )
            
            # Wait for completion
            while workflows.executions[execution_id].status == PipelineStatus.RUNNING:
                await asyncio.sleep(1)
            
            # Get status
            status = workflows.get_pipeline_status(pipeline_id)
            print(f"Pipeline status: {status}")
    
    asyncio.run(main())
