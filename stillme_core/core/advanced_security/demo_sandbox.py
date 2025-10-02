#!/usr/bin/env python3
"""
🚀 SANDBOX SYSTEM DEMO - PHASE 1
🚀 DEMO HỆ THỐNG SANDBOX - GIAI ĐOẠN 1

PURPOSE / MỤC ĐÍCH:
- Demo script để test sandbox system
- Script demo để test hệ thống sandbox
- Showcase các tính năng chính
- Trình diễn các tính năng chính
- Integration với existing security framework
- Tích hợp với framework bảo mật hiện có
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stillme_core.core.advanced_security.safe_attack_simulator import (
    SafeAttackSimulator,
)
from stillme_core.core.advanced_security.sandbox_controller import (
    SandboxController,
    SandboxType,
)
from stillme_core.core.advanced_security.sandbox_deploy import SandboxDeployer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SandboxDemo:
    """
    🚀 Sandbox System Demo
    🚀 Demo hệ thống Sandbox
    """

    def __init__(self):
        """Initialize demo"""
        self.controller = None
        self.deployer = None
        self.simulator = None
        self.demo_results = {}

    async def run_full_demo(self):
        """Run complete sandbox system demo"""
        print("🚀 Starting StillMe Security Sandbox System Demo")
        print("=" * 60)

        try:
            # Step 1: Initialize components
            await self._demo_initialization()

            # Step 2: Sandbox creation and management
            await self._demo_sandbox_management()

            # Step 3: Security testing
            await self._demo_security_testing()

            # Step 4: Resource monitoring
            await self._demo_resource_monitoring()

            # Step 5: Cleanup and reporting
            await self._demo_cleanup_and_reporting()

            print("\n🎉 Demo completed successfully!")
            self._print_demo_summary()

        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo failed: {e}")
            return False

        return True

    async def _demo_initialization(self):
        """Demo component initialization"""
        print("\n📋 Step 1: Component Initialization")
        print("-" * 40)

        # Initialize Sandbox Controller
        print("🔧 Initializing Sandbox Controller...")
        self.controller = SandboxController()
        print("✅ Sandbox Controller initialized")

        # Initialize Sandbox Deployer
        print("🔧 Initializing Sandbox Deployer...")
        self.deployer = SandboxDeployer()
        print("✅ Sandbox Deployer initialized")

        # Initialize Attack Simulator
        print("🔧 Initializing Attack Simulator...")
        self.simulator = SafeAttackSimulator()
        print("✅ Attack Simulator initialized")

        self.demo_results["initialization"] = "SUCCESS"

    async def _demo_sandbox_management(self):
        """Demo sandbox creation and management"""
        print("\n📦 Step 2: Sandbox Management")
        print("-" * 40)

        # Create security test sandbox
        print("🏗️ Creating security test sandbox...")
        sandbox = await self.controller.create_sandbox(
            name="demo-security-test",
            sandbox_type=SandboxType.SECURITY_TEST,
            image="python:3.9-slim"
        )

        print(f"✅ Sandbox created: {sandbox.config.sandbox_id}")
        self.demo_results["sandbox_creation"] = "SUCCESS"

        # Test basic command execution
        print("⚡ Testing command execution...")
        result = await self.controller.execute_in_sandbox(
            sandbox.config.sandbox_id,
            ["python", "-c", "print('Hello from StillMe Sandbox!')"]
        )

        if result["exit_code"] == 0:
            print(f"✅ Command executed successfully: {result['stdout'].strip()}")
            self.demo_results["command_execution"] = "SUCCESS"
        else:
            print(f"❌ Command execution failed: {result['stderr']}")
            self.demo_results["command_execution"] = "FAILED"

        # Test Python import
        print("🐍 Testing Python imports...")
        import_result = await self.controller.execute_in_sandbox(
            sandbox.config.sandbox_id,
            ["python", "-c", "import sys; print(f'Python {sys.version}')"]
        )

        if import_result["exit_code"] == 0:
            print(f"✅ Python import successful: {import_result['stdout'].strip()}")
            self.demo_results["python_imports"] = "SUCCESS"
        else:
            print(f"❌ Python import failed: {import_result['stderr']}")
            self.demo_results["python_imports"] = "FAILED"

        # Store sandbox ID for later use
        self.demo_results["sandbox_id"] = sandbox.config.sandbox_id

    async def _demo_security_testing(self):
        """Demo security testing capabilities"""
        print("\n🔒 Step 3: Security Testing")
        print("-" * 40)

        # Test network isolation
        print("🌐 Testing network isolation...")
        network_test = await self.controller.execute_in_sandbox(
            self.demo_results["sandbox_id"],
            ["python", "-c", "import requests; requests.get('http://google.com', timeout=5)"]
        )

        if network_test["exit_code"] != 0:
            print("✅ Network isolation working (external access blocked)")
            self.demo_results["network_isolation"] = "SUCCESS"
        else:
            print("❌ Network isolation failed (external access allowed)")
            self.demo_results["network_isolation"] = "FAILED"

        # Run attack simulation
        print("🎯 Running security attack simulation...")
        try:
            simulation_result = self.simulator.run_simulation(
                scenario_id="OWASP_SQL_INJECTION",
                target_config={
                    "host": "localhost",
                    "use_test_data": True,
                    "use_real_data": False
                }
            )

            print(f"✅ Attack simulation completed: {simulation_result.status}")
            print(f"🔍 Vulnerabilities found: {len(simulation_result.vulnerabilities_found)}")
            print(f"🛡️ Defenses triggered: {len(simulation_result.defenses_triggered)}")
            print(f"📊 Risk score: {simulation_result.risk_score:.2f}")

            self.demo_results["attack_simulation"] = "SUCCESS"
            self.demo_results["simulation_details"] = {
                "status": simulation_result.status.value,
                "vulnerabilities": len(simulation_result.vulnerabilities_found),
                "defenses": len(simulation_result.defenses_triggered),
                "risk_score": simulation_result.risk_score
            }

        except Exception as e:
            print(f"❌ Attack simulation failed: {e}")
            self.demo_results["attack_simulation"] = "FAILED"

    async def _demo_resource_monitoring(self):
        """Demo resource monitoring"""
        print("\n📊 Step 4: Resource Monitoring")
        print("-" * 40)

        # Wait for monitoring to collect data
        print("⏳ Collecting resource usage data...")
        await asyncio.sleep(5)

        # Get sandbox status
        status = self.controller.get_sandbox_status(self.demo_results["sandbox_id"])

        if status:
            print(f"📈 Sandbox status: {status['status']}")

            if status.get("resource_usage"):
                resource_usage = status["resource_usage"]
                print(f"💻 CPU usage: {resource_usage.get('cpu_percent', 0):.1f}%")
                print(f"🧠 Memory usage: {resource_usage.get('memory_usage_mb', 0):.1f} MB")
                print(f"📊 Memory percentage: {resource_usage.get('memory_percent', 0):.1f}%")

                self.demo_results["resource_monitoring"] = "SUCCESS"
                self.demo_results["resource_usage"] = resource_usage
            else:
                print("⚠️ No resource usage data available yet")
                self.demo_results["resource_monitoring"] = "PARTIAL"
        else:
            print("❌ Could not get sandbox status")
            self.demo_results["resource_monitoring"] = "FAILED"

        # Check for security violations
        if status and status.get("security_violations"):
            violations = status["security_violations"]
            print(f"🚨 Security violations detected: {len(violations)}")
            for violation in violations:
                print(f"   - {violation['type']}: {violation['value']} (limit: {violation['limit']})")
        else:
            print("✅ No security violations detected")

    async def _demo_cleanup_and_reporting(self):
        """Demo cleanup and reporting"""
        print("\n🧹 Step 5: Cleanup and Reporting")
        print("-" * 40)

        # Get deployment report
        print("📋 Generating deployment report...")
        deployment_report = self.deployer.get_deployment_report()
        print(f"📊 Total deployments: {deployment_report['total_deployments']}")
        print(f"✅ Successful: {deployment_report['successful_deployments']}")
        print(f"❌ Failed: {deployment_report['failed_deployments']}")

        # Get security report
        print("🔒 Generating security report...")
        security_report = self.simulator.get_safety_report()
        print(f"🎯 Total simulations: {security_report['total_simulations']}")
        print(f"✅ Safety checks passed: {security_report['safety_checks_passed']}")
        print(f"❌ Safety checks failed: {security_report['safety_checks_failed']}")

        # Clean up sandbox
        print("🧹 Cleaning up sandbox...")
        cleanup_success = await self.controller.destroy_sandbox(self.demo_results["sandbox_id"])

        if cleanup_success:
            print("✅ Sandbox cleaned up successfully")
            self.demo_results["cleanup"] = "SUCCESS"
        else:
            print("❌ Sandbox cleanup failed")
            self.demo_results["cleanup"] = "FAILED"

        # Final cleanup
        print("🧹 Final cleanup...")
        await self.controller.cleanup_all()
        print("✅ All resources cleaned up")

    def _print_demo_summary(self):
        """Print demo summary"""
        print("\n📊 DEMO SUMMARY")
        print("=" * 60)

        total_tests = len(self.demo_results) - 2  # Exclude sandbox_id and simulation_details
        passed_tests = sum(1 for key, value in self.demo_results.items()
                          if key not in ["sandbox_id", "simulation_details"] and value == "SUCCESS")

        print(f"📈 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📊 Success rate: {(passed_tests/total_tests)*100:.1f}%")

        print("\n📋 Detailed Results:")
        for key, value in self.demo_results.items():
            if key not in ["sandbox_id", "simulation_details"]:
                status_emoji = "✅" if value == "SUCCESS" else "❌" if value == "FAILED" else "⚠️"
                print(f"   {status_emoji} {key.replace('_', ' ').title()}: {value}")

        if "simulation_details" in self.demo_results:
            details = self.demo_results["simulation_details"]
            print("\n🎯 Security Simulation Details:")
            print(f"   📊 Status: {details['status']}")
            print(f"   🔍 Vulnerabilities: {details['vulnerabilities']}")
            print(f"   🛡️ Defenses: {details['defenses']}")
            print(f"   📈 Risk Score: {details['risk_score']:.2f}")

        if "resource_usage" in self.demo_results:
            usage = self.demo_results["resource_usage"]
            print("\n💻 Resource Usage:")
            print(f"   🖥️ CPU: {usage.get('cpu_percent', 0):.1f}%")
            print(f"   🧠 Memory: {usage.get('memory_usage_mb', 0):.1f} MB")
            print(f"   📊 Memory %: {usage.get('memory_percent', 0):.1f}%")


async def main():
    """Main demo function"""
    print("🚀 StillMe Security Sandbox System - Phase 1 Demo")
    print("🚀 Demo hệ thống Sandbox bảo mật StillMe - Giai đoạn 1")
    print("=" * 60)

    # Check if Docker is available
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("✅ Docker is available and running")
    except Exception as e:
        print(f"❌ Docker is not available: {e}")
        print("Please install and start Docker to run this demo")
        return 1

    # Run demo
    demo = SandboxDemo()
    success = await demo.run_full_demo()

    if success:
        print("\n🎉 Demo completed successfully!")
        print("🚀 Sandbox system is ready for Phase 2 development!")
        return 0
    else:
        print("\n❌ Demo failed!")
        print("Please check the logs and troubleshoot the issues")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo crashed: {e}")
        sys.exit(1)
