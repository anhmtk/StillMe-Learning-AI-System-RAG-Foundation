#!/usr/bin/env python3
"""
🧪 SANDBOX SYSTEM TEST SUITE - PHASE 1
🧪 BỘ TEST HỆ THỐNG SANDBOX - GIAI ĐOẠN 1

PURPOSE / MỤC ĐÍCH:
- Comprehensive test suite for sandbox system
- Bộ test toàn diện cho hệ thống sandbox
- Unit tests, integration tests, và end-to-end tests
- Test đơn vị, test tích hợp, và test end-to-end
- Performance và security validation
- Xác thực hiệu suất và bảo mật
"""

import asyncio
import logging

# Add parent directory to path for imports
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import docker
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stillme_core.core.advanced_security.sandbox_controller import (
    SECURITY_METRICS,
    SandboxConfig,
    SandboxController,
    SandboxInstance,
    SandboxStatus,
    SandboxType,
)
from stillme_core.core.advanced_security.sandbox_deploy import SandboxDeployer

logger = logging.getLogger(__name__)


class TestSandboxController(unittest.TestCase):
    """Test cases for SandboxController"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_docker_client = Mock()
        self.sandbox_controller = SandboxController(self.mock_docker_client)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any test sandboxes
        asyncio.run(self.sandbox_controller.cleanup_all())

    def test_sandbox_config_creation(self):
        """Test sandbox configuration creation"""
        config = SandboxConfig(
            sandbox_id="test_sandbox",
            name="Test Sandbox",
            sandbox_type=SandboxType.SECURITY_TEST,
        )

        self.assertEqual(config.sandbox_id, "test_sandbox")
        self.assertEqual(config.name, "Test Sandbox")
        self.assertEqual(config.sandbox_type, SandboxType.SECURITY_TEST)
        self.assertEqual(config.memory_limit, 512)  # Default value
        self.assertEqual(config.timeout, 900)  # Default value

    def test_security_metrics_configuration(self):
        """Test security metrics configuration"""
        self.assertEqual(SECURITY_METRICS["max_cpu_usage"], 70)
        self.assertEqual(SECURITY_METRICS["max_memory_usage"], 512)
        self.assertEqual(SECURITY_METRICS["max_execution_time"], 900)
        self.assertEqual(SECURITY_METRICS["network_egress_limit"], 0)

    @patch("docker.from_env")
    def test_sandbox_controller_initialization(self, mock_docker):
        """Test sandbox controller initialization"""
        mock_client = Mock()
        mock_docker.return_value = mock_client

        controller = SandboxController()

        self.assertEqual(controller.docker_client, mock_client)
        self.assertEqual(len(controller.active_sandboxes), 0)
        self.assertEqual(len(controller.sandbox_history), 0)
        self.assertTrue(controller.isolation_base.exists())

    def test_sandbox_instance_creation(self):
        """Test sandbox instance creation"""
        config = SandboxConfig(
            sandbox_id="test_instance",
            name="Test Instance",
            sandbox_type=SandboxType.CODE_EXECUTION,
        )

        instance = SandboxInstance(config=config)

        self.assertEqual(instance.config, config)
        self.assertEqual(instance.status, SandboxStatus.CREATING)
        self.assertIsNotNone(instance.created_at)
        self.assertEqual(len(instance.logs), 0)
        self.assertEqual(len(instance.security_violations), 0)

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    async def test_resource_check_success(self, mock_memory, mock_cpu):
        """Test successful resource check"""
        mock_cpu.return_value = 50.0  # 50% CPU usage
        mock_memory.return_value = Mock(percent=60.0)  # 60% memory usage

        result = await self.sandbox_controller._check_system_resources()

        self.assertTrue(result)

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    async def test_resource_check_failure_high_cpu(self, mock_memory, mock_cpu):
        """Test resource check failure due to high CPU"""
        mock_cpu.return_value = 80.0  # 80% CPU usage (exceeds limit)
        mock_memory.return_value = Mock(percent=60.0)

        result = await self.sandbox_controller._check_system_resources()

        self.assertFalse(result)

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    async def test_resource_check_failure_high_memory(self, mock_memory, mock_cpu):
        """Test resource check failure due to high memory"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(
            percent=85.0
        )  # 85% memory usage (exceeds limit)

        result = await self.sandbox_controller._check_system_resources()

        self.assertFalse(result)

    def test_docker_availability_check_success(self):
        """Test successful Docker availability check"""
        self.mock_docker_client.ping.return_value = True

        result = asyncio.run(self.sandbox_controller._check_docker_availability())

        self.assertTrue(result)
        self.mock_docker_client.ping.assert_called_once()

    def test_docker_availability_check_failure(self):
        """Test Docker availability check failure"""
        self.mock_docker_client.ping.side_effect = Exception("Docker not available")

        result = asyncio.run(self.sandbox_controller._check_docker_availability())

        self.assertFalse(result)

    async def test_security_policy_check_success(self):
        """Test successful security policy check"""
        config = SandboxConfig(
            sandbox_id="test_policy",
            name="Test Policy",
            sandbox_type=SandboxType.SECURITY_TEST,
            memory_limit=256,  # Within limits
            timeout=600,  # Within limits
        )

        instance = SandboxInstance(config=config)

        result = await self.sandbox_controller._check_security_policies(instance)

        self.assertTrue(result)

    async def test_security_policy_check_failure_memory(self):
        """Test security policy check failure due to memory limit"""
        config = SandboxConfig(
            sandbox_id="test_policy_fail",
            name="Test Policy Fail",
            sandbox_type=SandboxType.SECURITY_TEST,
            memory_limit=1024,  # Exceeds limit (512MB)
            timeout=600,
        )

        instance = SandboxInstance(config=config)

        with self.assertRaises(ValueError) as context:
            await self.sandbox_controller._check_security_policies(instance)

        self.assertIn("Memory limit", str(context.exception))

    async def test_security_policy_check_failure_timeout(self):
        """Test security policy check failure due to timeout"""
        config = SandboxConfig(
            sandbox_id="test_policy_fail",
            name="Test Policy Fail",
            sandbox_type=SandboxType.SECURITY_TEST,
            memory_limit=256,
            timeout=1200,  # Exceeds limit (900s)
        )

        instance = SandboxInstance(config=config)

        with self.assertRaises(ValueError) as context:
            await self.sandbox_controller._check_security_policies(instance)

        self.assertIn("Timeout", str(context.exception))

    def test_get_sandbox_status_active(self):
        """Test getting status of active sandbox"""
        config = SandboxConfig(
            sandbox_id="test_status",
            name="Test Status",
            sandbox_type=SandboxType.SECURITY_TEST,
        )

        instance = SandboxInstance(config=config)
        instance.status = SandboxStatus.RUNNING
        instance.started_at = time.time()

        self.sandbox_controller.active_sandboxes["test_status"] = instance

        status = self.sandbox_controller.get_sandbox_status("test_status")

        self.assertIsNotNone(status)
        self.assertEqual(status["sandbox_id"], "test_status")
        self.assertEqual(status["status"], "running")

    def test_get_sandbox_status_not_found(self):
        """Test getting status of non-existent sandbox"""
        status = self.sandbox_controller.get_sandbox_status("non_existent")

        self.assertIsNone(status)


class TestSandboxDeployer(unittest.TestCase):
    """Test cases for SandboxDeployer"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_docker_client = Mock()
        self.deployer = SandboxDeployer()
        self.deployer.docker_client = self.mock_docker_client

    def test_deployer_initialization(self):
        """Test deployer initialization"""
        self.assertIsNotNone(self.deployer.project_root)
        self.assertIsNotNone(self.deployer.sandbox_controller)
        self.assertEqual(len(self.deployer.deployment_logs), 0)

    def test_log_deployment(self):
        """Test deployment logging"""
        self.deployer._log_deployment("INFO", "Test message")

        self.assertEqual(len(self.deployer.deployment_logs), 1)
        self.assertEqual(self.deployer.deployment_logs[0]["level"], "INFO")
        self.assertEqual(self.deployer.deployment_logs[0]["message"], "Test message")

    def test_get_deployment_report(self):
        """Test deployment report generation"""
        # Add some test logs
        self.deployer._log_deployment("SUCCESS", "Test success")
        self.deployer._log_deployment("ERROR", "Test error")

        report = self.deployer.get_deployment_report()

        self.assertEqual(report["total_deployments"], 2)
        self.assertEqual(report["successful_deployments"], 1)
        self.assertEqual(report["failed_deployments"], 1)
        self.assertIn("deployment_logs", report)
        self.assertIn("sandbox_status", report)


class TestIntegration(unittest.TestCase):
    """Integration tests for sandbox system"""

    @pytest.mark.asyncio
    async def test_full_sandbox_lifecycle(self):
        """Test complete sandbox lifecycle"""
        # This test requires actual Docker to be running
        try:
            docker_client = docker.from_env()
            docker_client.ping()
        except Exception:
            self.skipTest("Docker not available for integration test")

        controller = SandboxController(docker_client)

        try:
            # Create sandbox
            sandbox = await controller.create_sandbox(
                name="integration_test", sandbox_type=SandboxType.SECURITY_TEST
            )

            self.assertIsNotNone(sandbox)
            self.assertEqual(sandbox.status, SandboxStatus.RUNNING)

            # Execute command
            result = await controller.execute_in_sandbox(
                sandbox.config.sandbox_id, ["echo", "Hello from sandbox"]
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertIn("Hello from sandbox", result["stdout"])

            # Check status
            status = controller.get_sandbox_status(sandbox.config.sandbox_id)
            self.assertIsNotNone(status)
            self.assertEqual(status["status"], "running")

            # Destroy sandbox
            success = await controller.destroy_sandbox(sandbox.config.sandbox_id)
            self.assertTrue(success)

        finally:
            await controller.cleanup_all()

    @pytest.mark.asyncio
    async def test_resource_monitoring(self):
        """Test resource monitoring functionality"""
        try:
            docker_client = docker.from_env()
            docker_client.ping()
        except Exception:
            self.skipTest("Docker not available for integration test")

        controller = SandboxController(docker_client)

        try:
            # Create sandbox
            sandbox = await controller.create_sandbox(
                name="resource_test", sandbox_type=SandboxType.SECURITY_TEST
            )

            # Wait for monitoring to collect data
            await asyncio.sleep(10)

            # Check resource usage
            status = controller.get_sandbox_status(sandbox.config.sandbox_id)
            self.assertIsNotNone(status)
            self.assertIn("resource_usage", status)

            # Clean up
            await controller.destroy_sandbox(sandbox.config.sandbox_id)

        finally:
            await controller.cleanup_all()

    @pytest.mark.asyncio
    async def test_network_isolation(self):
        """Test network isolation functionality"""
        try:
            docker_client = docker.from_env()
            docker_client.ping()
        except Exception:
            self.skipTest("Docker not available for integration test")

        controller = SandboxController(docker_client)

        try:
            # Create sandbox with network isolation
            sandbox = await controller.create_sandbox(
                name="network_test", sandbox_type=SandboxType.SECURITY_TEST
            )

            # Try to access external network (should fail)
            result = await controller.execute_in_sandbox(
                sandbox.config.sandbox_id,
                [
                    "python",
                    "-c",
                    "import requests; requests.get('http://google.com', timeout=5)",
                ],
            )

            # Should fail due to network isolation
            self.assertNotEqual(result["exit_code"], 0)

            # Clean up
            await controller.destroy_sandbox(sandbox.config.sandbox_id)

        finally:
            await controller.cleanup_all()


class TestSecurityValidation(unittest.TestCase):
    """Security validation tests"""

    def test_security_metrics_enforcement(self):
        """Test that security metrics are properly enforced"""
        # Test CPU limit
        self.assertLessEqual(SECURITY_METRICS["max_cpu_usage"], 70)

        # Test memory limit
        self.assertLessEqual(SECURITY_METRICS["max_memory_usage"], 512)

        # Test execution time limit
        self.assertLessEqual(SECURITY_METRICS["max_execution_time"], 900)

        # Test network isolation
        self.assertEqual(SECURITY_METRICS["network_egress_limit"], 0)

    def test_sandbox_config_security_defaults(self):
        """Test that sandbox config has secure defaults"""
        config = SandboxConfig(
            sandbox_id="security_test",
            name="Security Test",
            sandbox_type=SandboxType.SECURITY_TEST,
        )

        # Check secure defaults
        self.assertEqual(config.network_mode, "none")  # No network access
        self.assertLessEqual(config.memory_limit, 512)  # Memory limit
        self.assertLessEqual(config.timeout, 900)  # Timeout limit
        self.assertIn("no_network", config.security_policies)

    def test_isolation_requirements(self):
        """Test isolation requirements"""
        controller = SandboxController()

        # Check isolation base exists
        self.assertTrue(controller.isolation_base.exists())

        # Check security policies are initialized
        self.assertIn("network_isolation", controller.security_policies)
        self.assertIn("resource_limits", controller.security_policies)
        self.assertIn("execution_limits", controller.security_policies)
        self.assertIn("data_protection", controller.security_policies)


def run_performance_tests():
    """Run performance tests"""
    print("🚀 Running performance tests...")

    # Test sandbox creation performance
    start_time = time.time()

    # Simulate multiple sandbox creations
    for i in range(10):
        config = SandboxConfig(
            sandbox_id=f"perf_test_{i}",
            name=f"Performance Test {i}",
            sandbox_type=SandboxType.SECURITY_TEST,
        )
        SandboxInstance(config=config)

    end_time = time.time()
    creation_time = end_time - start_time

    print(f"✅ Created 10 sandbox instances in {creation_time:.2f} seconds")
    print(f"📊 Average creation time: {creation_time/10:.3f} seconds per instance")

    # Performance assertions
    assert creation_time < 1.0, "Sandbox creation is too slow"
    assert creation_time / 10 < 0.1, "Individual sandbox creation is too slow"


def run_security_tests():
    """Run security validation tests"""
    print("🔒 Running security validation tests...")

    # Test 1: Security metrics validation
    assert SECURITY_METRICS["max_cpu_usage"] <= 70, "CPU limit too high"
    assert SECURITY_METRICS["max_memory_usage"] <= 512, "Memory limit too high"
    assert (
        SECURITY_METRICS["max_execution_time"] <= 900
    ), "Execution time limit too high"
    assert (
        SECURITY_METRICS["network_egress_limit"] == 0
    ), "Network access should be blocked"

    print("✅ Security metrics validation passed")

    # Test 2: Default security policies
    controller = SandboxController()
    policies = controller.security_policies

    assert policies["network_isolation"][
        "enabled"
    ], "Network isolation should be enabled"
    assert policies["resource_limits"][
        "enforcement"
    ], "Resource limits should be enforced"
    assert policies["data_protection"]["no_real_data"], "Real data should be prohibited"

    print("✅ Default security policies validation passed")


def main():
    """Main test runner"""
    print("🧪 Starting Sandbox System Test Suite")
    print("=" * 50)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run unit tests
    print("\n🔬 Running Unit Tests...")
    unittest.main(argv=[""], exit=False, verbosity=2)

    # Run performance tests
    print("\n⚡ Running Performance Tests...")
    run_performance_tests()

    # Run security tests
    print("\n🔒 Running Security Tests...")
    run_security_tests()

    print("\n🎉 All tests completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()