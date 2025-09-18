#!/usr/bin/env python3
"""
🚀 SANDBOX DEPLOY SCRIPT - PHASE 1
🚀 SCRIPT TRIỂN KHAI SANDBOX - GIAI ĐOẠN 1

PURPOSE / MỤC ĐÍCH:
- Automated sandbox deployment và verification
- Triển khai sandbox tự động và xác minh
- Docker image building và container management
- Xây dựng Docker image và quản lý container
- Health checks và integration testing
- Kiểm tra sức khỏe và test tích hợp
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stillme_core.core.advanced_security.sandbox_controller import (
    SandboxController,
    SandboxType,
    SandboxStatus
)

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_IMAGE = "python:3.9-slim"
CUSTOM_IMAGE_TAG = "stillme-security-test"
HEALTH_CHECK_TIMEOUT = 30
DEPLOYMENT_TIMEOUT = 300  # 5 minutes


class SandboxDeployer:
    """
    🚀 Automated Sandbox Deployment Manager
    🚀 Quản lý triển khai Sandbox tự động
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize Sandbox Deployer
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root or os.getcwd())
        self.docker_client = docker.from_env()
        self.sandbox_controller = SandboxController(self.docker_client)
        self.deployment_logs: List[Dict] = []
        
        logger.info(f"🚀 SandboxDeployer initialized for project: {self.project_root}")

    async def deploy_security_sandbox(
        self,
        name: str = "security-test",
        image: str = DEFAULT_IMAGE,
        custom_dockerfile: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Deploy a security testing sandbox
        
        Args:
            name: Sandbox name
            image: Base Docker image
            custom_dockerfile: Path to custom Dockerfile
            
        Returns:
            Tuple of (success, sandbox_id, deployment_info)
        """
        deployment_id = f"deploy_{int(time.time())}"
        
        try:
            self._log_deployment("INFO", f"Starting deployment {deployment_id}")
            
            # Step 1: Build custom image if needed
            if custom_dockerfile:
                image = await self._build_custom_image(custom_dockerfile)
            
            # Step 2: Create sandbox
            sandbox = await self.sandbox_controller.create_sandbox(
                name=name,
                sandbox_type=SandboxType.SECURITY_TEST,
                image=image,
                environment_vars={
                    "SANDBOX_MODE": "security_test",
                    "DEPLOYMENT_ID": deployment_id,
                    "PYTHONPATH": "/workspace"
                }
            )
            
            # Step 3: Deploy application code
            await self._deploy_application_code(sandbox)
            
            # Step 4: Install dependencies
            await self._install_dependencies(sandbox)
            
            # Step 5: Run health checks
            health_status = await self._run_health_checks(sandbox)
            
            # Step 6: Verify deployment
            verification_result = await self._verify_deployment(sandbox)
            
            deployment_info = {
                "deployment_id": deployment_id,
                "sandbox_id": sandbox.config.sandbox_id,
                "image": image,
                "health_status": health_status,
                "verification_result": verification_result,
                "deployment_time": time.time(),
                "logs": self.deployment_logs
            }
            
            if health_status["overall_health"] and verification_result["verified"]:
                self._log_deployment("SUCCESS", f"Deployment {deployment_id} completed successfully")
                return True, sandbox.config.sandbox_id, deployment_info
            else:
                self._log_deployment("ERROR", f"Deployment {deployment_id} failed health checks")
                return False, sandbox.config.sandbox_id, deployment_info
                
        except Exception as e:
            self._log_deployment("ERROR", f"Deployment {deployment_id} failed: {str(e)}")
            return False, "", {"error": str(e), "deployment_id": deployment_id}

    async def _build_custom_image(self, dockerfile_path: str) -> str:
        """Build custom Docker image"""
        try:
            self._log_deployment("INFO", f"Building custom image from {dockerfile_path}")
            
            # Build image
            image, build_logs = self.docker_client.images.build(
                path=str(self.project_root),
                dockerfile=dockerfile_path,
                tag=CUSTOM_IMAGE_TAG,
                rm=True
            )
            
            self._log_deployment("SUCCESS", f"Custom image built: {CUSTOM_IMAGE_TAG}")
            return CUSTOM_IMAGE_TAG
            
        except Exception as e:
            self._log_deployment("ERROR", f"Failed to build custom image: {str(e)}")
            raise

    async def _deploy_application_code(self, sandbox):
        """Deploy application code to sandbox"""
        try:
            self._log_deployment("INFO", f"Deploying application code to sandbox {sandbox.config.sandbox_id}")
            
            # Copy project files to sandbox
            sandbox_dir = self.sandbox_controller.isolation_base / sandbox.config.sandbox_id
            
            # Copy essential files
            essential_files = [
                "stillme_core",
                "requirements.txt",
                "README.md",
                ".env.example"
            ]
            
            for file_path in essential_files:
                src_path = self.project_root / file_path
                if src_path.exists():
                    dst_path = sandbox_dir / file_path
                    if src_path.is_dir():
                        self._copy_directory(src_path, dst_path)
                    else:
                        self._copy_file(src_path, dst_path)
            
            self._log_deployment("SUCCESS", "Application code deployed successfully")
            
        except Exception as e:
            self._log_deployment("ERROR", f"Failed to deploy application code: {str(e)}")
            raise

    def _copy_directory(self, src: Path, dst: Path):
        """Copy directory recursively"""
        import shutil
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".git", ".pytest_cache"
        ))

    def _copy_file(self, src: Path, dst: Path):
        """Copy file"""
        import shutil
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    async def _install_dependencies(self, sandbox):
        """Install Python dependencies in sandbox"""
        try:
            self._log_deployment("INFO", f"Installing dependencies in sandbox {sandbox.config.sandbox_id}")
            
            # Check if requirements.txt exists
            result = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["ls", "-la", "/workspace/requirements.txt"]
            )
            
            if result["exit_code"] == 0:
                # Install dependencies
                install_result = await self.sandbox_controller.execute_in_sandbox(
                    sandbox.config.sandbox_id,
                    ["pip", "install", "-r", "/workspace/requirements.txt"]
                )
                
                if install_result["exit_code"] == 0:
                    self._log_deployment("SUCCESS", "Dependencies installed successfully")
                else:
                    self._log_deployment("WARNING", f"Dependency installation had issues: {install_result['stderr']}")
            else:
                self._log_deployment("INFO", "No requirements.txt found, skipping dependency installation")
                
        except Exception as e:
            self._log_deployment("ERROR", f"Failed to install dependencies: {str(e)}")
            raise

    async def _run_health_checks(self, sandbox) -> Dict:
        """Run comprehensive health checks"""
        health_checks = {
            "container_running": False,
            "python_available": False,
            "imports_working": False,
            "network_isolation": False,
            "resource_limits": False,
            "overall_health": False
        }
        
        try:
            self._log_deployment("INFO", f"Running health checks for sandbox {sandbox.config.sandbox_id}")
            
            # Check 1: Container is running
            status = self.sandbox_controller.get_sandbox_status(sandbox.config.sandbox_id)
            health_checks["container_running"] = bool(status and status.get("status") == "running")
            
            # Check 2: Python is available
            python_check = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["python", "--version"]
            )
            health_checks["python_available"] = python_check["exit_code"] == 0
            
            # Check 3: Core imports work
            import_check = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["python", "-c", "import sys; sys.path.append('/workspace'); import stillme_core; print('OK')"]
            )
            health_checks["imports_working"] = import_check["exit_code"] == 0
            
            # Check 4: Network isolation
            network_check = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["python", "-c", "import requests; requests.get('http://google.com', timeout=5)"]
            )
            # Should fail due to network isolation
            health_checks["network_isolation"] = network_check["exit_code"] != 0
            
            # Check 5: Resource limits
            resource_status = status.get("resource_usage", {}) if status else {}
            health_checks["resource_limits"] = (
                resource_status.get("cpu_percent", 0) < 70 and
                resource_status.get("memory_percent", 0) < 80
            )
            
            # Overall health
            health_checks["overall_health"] = bool(all([
                health_checks["container_running"],
                health_checks["python_available"],
                health_checks["imports_working"],
                health_checks["network_isolation"],
                health_checks["resource_limits"]
            ]))
            
            self._log_deployment("INFO", f"Health checks completed: {health_checks}")
            
        except Exception as e:
            self._log_deployment("ERROR", f"Health checks failed: {str(e)}")
        
        return health_checks

    async def _verify_deployment(self, sandbox) -> Dict:
        """Verify deployment is working correctly"""
        verification = {
            "verified": False,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": {}
        }
        
        try:
            self._log_deployment("INFO", f"Verifying deployment for sandbox {sandbox.config.sandbox_id}")
            
            # Test 1: Basic Python execution
            test1 = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["python", "-c", "print('Hello from sandbox!')"]
            )
            if test1["exit_code"] == 0:
                verification["tests_passed"] += 1
                verification["details"]["basic_execution"] = "PASS"
            else:
                verification["tests_failed"] += 1
                verification["details"]["basic_execution"] = "FAIL"
            
            # Test 2: StillMe core import
            test2 = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["python", "-c", "import stillme_core; print('StillMe core imported successfully')"]
            )
            if test2["exit_code"] == 0:
                verification["tests_passed"] += 1
                verification["details"]["core_import"] = "PASS"
            else:
                verification["tests_failed"] += 1
                verification["details"]["core_import"] = "FAIL"
            
            # Test 3: Security module import
            test3 = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                ["python", "-c", "from stillme_core.core.advanced_security.safe_attack_simulator import SafeAttackSimulator; print('Security module imported')"]
            )
            if test3["exit_code"] == 0:
                verification["tests_passed"] += 1
                verification["details"]["security_import"] = "PASS"
            else:
                verification["tests_failed"] += 1
                verification["details"]["security_import"] = "FAIL"
            
            # Overall verification
            verification["verified"] = verification["tests_failed"] == 0
            
            self._log_deployment("INFO", f"Verification completed: {verification['tests_passed']} passed, {verification['tests_failed']} failed")
            
        except Exception as e:
            self._log_deployment("ERROR", f"Verification failed: {str(e)}")
            verification["details"]["error"] = str(e)
        
        return verification

    def _log_deployment(self, level: str, message: str):
        """Log deployment event"""
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message
        }
        self.deployment_logs.append(log_entry)
        logger.info(f"[{level}] {message}")

    async def cleanup_deployment(self, sandbox_id: str) -> bool:
        """Clean up deployment"""
        try:
            self._log_deployment("INFO", f"Cleaning up deployment {sandbox_id}")
            success = await self.sandbox_controller.destroy_sandbox(sandbox_id)
            if success:
                self._log_deployment("SUCCESS", f"Deployment {sandbox_id} cleaned up successfully")
            else:
                self._log_deployment("ERROR", f"Failed to clean up deployment {sandbox_id}")
            return success
        except Exception as e:
            self._log_deployment("ERROR", f"Cleanup failed: {str(e)}")
            return False

    def get_deployment_report(self) -> Dict:
        """Get comprehensive deployment report"""
        return {
            "total_deployments": len(self.deployment_logs),
            "successful_deployments": len([log for log in self.deployment_logs if log["level"] == "SUCCESS"]),
            "failed_deployments": len([log for log in self.deployment_logs if log["level"] == "ERROR"]),
            "active_sandboxes": len(self.sandbox_controller.active_sandboxes),
            "deployment_logs": self.deployment_logs,
            "sandbox_status": self.sandbox_controller.get_all_sandboxes()
        }


async def main():
    """Main deployment function"""
    logging.basicConfig(level=logging.INFO)
    
    deployer = SandboxDeployer()
    
    try:
        # Deploy security sandbox
        success, sandbox_id, info = await deployer.deploy_security_sandbox(
            name="security-test-deployment",
            image=DEFAULT_IMAGE
        )
        
        if success:
            print(f"✅ Deployment successful! Sandbox ID: {sandbox_id}")
            print(f"📊 Deployment info: {json.dumps(info, indent=2, default=str)}")
        else:
            print(f"❌ Deployment failed! Error: {info.get('error', 'Unknown error')}")
        
        # Get deployment report
        report = deployer.get_deployment_report()
        print(f"📈 Deployment report: {json.dumps(report, indent=2, default=str)}")
        
        # Cleanup after 30 seconds (for testing)
        await asyncio.sleep(30)
        await deployer.cleanup_deployment(sandbox_id)
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
