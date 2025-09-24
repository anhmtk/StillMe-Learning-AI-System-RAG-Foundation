#!/usr/bin/env python3
"""
AgentDev CLI - Resume Handler
SEAL-grade resume functionality for interrupted jobs
"""

import asyncio
import argparse
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from agentdev.state_store import StateStore, JobStatus, StepStatus

class ResumeHandler:
    """Handle job resume operations"""
    
    def __init__(self, state_store: StateStore):
        self.state_store = state_store
    
    async def resume_job(self, job_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Resume a job from the last checkpoint"""
        print(f"🔄 Resuming job: {job_id}")
        
        # Get job information
        job = await self.state_store.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        print(f"📋 Job: {job.job_type} (Status: {job.status.value})")
        print(f"👤 Created by: {job.created_by}")
        print(f"📅 Created: {time.ctime(job.created_at)}")
        
        # Get job steps
        steps = await self.state_store.get_job_steps(job_id)
        if not steps:
            print("⚠️ No steps found for job")
            return {"status": "no_steps", "job_id": job_id}
        
        # Sort steps by order
        steps.sort(key=lambda x: x.order_index)
        
        print(f"📝 Found {len(steps)} steps:")
        for step in steps:
            status_icon = {
                StepStatus.PENDING: "⏳",
                StepStatus.RUNNING: "🔄",
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️",
                StepStatus.CANCELLED: "🚫"
            }.get(step.status, "❓")
            
            print(f"  {status_icon} {step.step_name} ({step.status.value})")
        
        # Get resume point
        resume_point = await self.state_store.get_resume_point(job_id)
        if not resume_point:
            print("ℹ️ No resume point found - starting from beginning")
            resume_from_step = None
        else:
            resume_from_step, checkpoint_data = resume_point
            print(f"🎯 Resume point: {resume_from_step}")
            print(f"📊 Checkpoint data: {checkpoint_data}")
        
        # Determine which steps to execute
        steps_to_execute = []
        if resume_from_step:
            # Find the step after the resume point
            resume_index = next(
                (i for i, step in enumerate(steps) if step.step_id == resume_from_step),
                -1
            )
            if resume_index >= 0:
                steps_to_execute = steps[resume_index + 1:]
            else:
                steps_to_execute = steps
        else:
            steps_to_execute = steps
        
        # Filter out completed steps
        steps_to_execute = [
            step for step in steps_to_execute 
            if step.status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]
        ]
        
        if not steps_to_execute:
            print("✅ All steps already completed - nothing to resume")
            return {"status": "already_completed", "job_id": job_id}
        
        print(f"🚀 Will execute {len(steps_to_execute)} steps:")
        for step in steps_to_execute:
            print(f"  ▶️ {step.step_name}")
        
        if dry_run:
            print("🔍 Dry run mode - no actual execution")
            return {
                "status": "dry_run",
                "job_id": job_id,
                "steps_to_execute": [step.step_id for step in steps_to_execute],
                "resume_from": resume_from_step
            }
        
        # Execute steps
        return await self._execute_steps(job_id, steps_to_execute)
    
    async def _execute_steps(self, job_id: str, steps: List[Any]) -> Dict[str, Any]:
        """Execute the remaining steps"""
        print(f"🏃 Executing {len(steps)} steps...")
        
        executed_steps = []
        failed_steps = []
        
        for step in steps:
            print(f"\n🔄 Executing: {step.step_name}")
            
            try:
                # Update step status to running
                await self.state_store.update_step_status(
                    step.step_id, StepStatus.RUNNING,
                    started_at=time.time()
                )
                
                # Simulate step execution
                # In real implementation, this would execute the actual command
                await self._simulate_step_execution(step)
                
                # Update step status to completed
                await self.state_store.update_step_status(
                    step.step_id, StepStatus.COMPLETED,
                    completed_at=time.time(),
                    duration_ms=1000,  # Simulated duration
                    output={"stdout": f"Step {step.step_name} completed", "stderr": "", "return_code": 0}
                )
                
                executed_steps.append(step.step_id)
                print(f"✅ Completed: {step.step_name}")
                
            except Exception as e:
                # Update step status to failed
                await self.state_store.update_step_status(
                    step.step_id, StepStatus.FAILED,
                    error=str(e)
                )
                
                failed_steps.append(step.step_id)
                print(f"❌ Failed: {step.step_name} - {e}")
                
                # Stop execution on failure (unless configured otherwise)
                break
        
        # Update job status
        if failed_steps:
            await self.state_store.update_job_status(job_id, JobStatus.FAILED)
            status = "failed"
        else:
            await self.state_store.update_job_status(job_id, JobStatus.COMPLETED)
            status = "completed"
        
        return {
            "status": status,
            "job_id": job_id,
            "executed_steps": executed_steps,
            "failed_steps": failed_steps,
            "total_steps": len(steps)
        }
    
    async def _simulate_step_execution(self, step: Any):
        """Simulate step execution"""
        # In real implementation, this would:
        # 1. Check dependencies
        # 2. Execute the command
        # 3. Handle timeouts
        # 4. Capture output
        # 5. Handle errors
        
        print(f"  📝 Command: {step.command}")
        print(f"  📁 Working directory: {step.working_directory or 'current'}")
        print(f"  ⏱️ Timeout: {step.timeout_seconds}s")
        print(f"  🔄 Max retries: {step.max_retries}")
        
        # Simulate execution time
        await asyncio.sleep(0.1)
        
        # Simulate occasional failures for testing
        import random
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Simulated step failure")
    
    async def list_resumable_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs that can be resumed"""
        # This would query the database for jobs with incomplete steps
        # For now, return a mock list
        return [
            {
                "job_id": "example_job_123",
                "job_type": "deploy_edge",
                "status": "running",
                "created_at": time.time() - 3600,
                "created_by": "developer",
                "completed_steps": 2,
                "total_steps": 5
            }
        ]
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job status"""
        job = await self.state_store.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        steps = await self.state_store.get_job_steps(job_id)
        steps.sort(key=lambda x: x.order_index)
        
        # Count steps by status
        status_counts = {}
        for step in steps:
            status = step.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Get resume point
        resume_point = await self.state_store.get_resume_point(job_id)
        
        return {
            "job_id": job_id,
            "job_type": job.job_type,
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_ms": job.duration_ms,
            "created_by": job.created_by,
            "total_steps": len(steps),
            "step_status_counts": status_counts,
            "resume_point": resume_point[0] if resume_point else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "order_index": step.order_index,
                    "started_at": step.started_at,
                    "completed_at": step.completed_at,
                    "duration_ms": step.duration_ms,
                    "error": step.error
                }
                for step in steps
            ]
        }

def create_resume_parser() -> argparse.ArgumentParser:
    """Create argument parser for resume commands"""
    parser = argparse.ArgumentParser(
        description="AgentDev Resume Handler",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a job")
    resume_parser.add_argument("job_id", help="Job ID to resume")
    resume_parser.add_argument("--dry-run", action="store_true", 
                              help="Show what would be executed without actually running")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List resumable jobs")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get job status")
    status_parser.add_argument("job_id", help="Job ID to check")
    
    return parser

async def main():
    """Main CLI entry point"""
    parser = create_resume_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize state store
    state_store = StateStore()
    await state_store.initialize()
    
    handler = ResumeHandler(state_store)
    
    try:
        if args.command == "resume":
            result = await handler.resume_job(args.job_id, dry_run=args.dry_run)
            print(f"\n📊 Resume result: {result}")
            
        elif args.command == "list":
            jobs = await handler.list_resumable_jobs()
            print("📋 Resumable jobs:")
            for job in jobs:
                print(f"  🔄 {job['job_id']} ({job['job_type']}) - {job['completed_steps']}/{job['total_steps']} steps")
                
        elif args.command == "status":
            status = await handler.get_job_status(args.job_id)
            print(f"📊 Job status for {args.job_id}:")
            print(f"  Type: {status['job_type']}")
            print(f"  Status: {status['status']}")
            print(f"  Steps: {status['total_steps']}")
            print(f"  Step status: {status['step_status_counts']}")
            if status['resume_point']:
                print(f"  Resume point: {status['resume_point']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
