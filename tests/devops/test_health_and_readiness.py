"""
Health Check and Readiness Tests
Tests for Kubernetes/Docker health endpoints
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from stillme_core.health import HealthChecker, HealthStatus


class TestHealthChecker:
    """Test health checker functionality"""

    @pytest.fixture
    def health_checker(self):
        """Create health checker instance"""
        config = {
            'version': '1.0.0',
            'environment': 'test',
            'database': {'path': ':memory:'}
        }
        return HealthChecker(config)

    def test_health_checker_initialization(self, health_checker):
        """Test health checker initialization"""
        assert health_checker.version == '1.0.0'
        assert health_checker.environment == 'test'
        assert health_checker.start_time > 0

    def test_database_check_healthy(self, health_checker):
        """Test database health check when healthy"""
        check = health_checker.check_database()

        assert check.name == "database"
        assert check.status == HealthStatus.HEALTHY
        assert "successful" in check.message
        assert check.duration_ms > 0
        assert isinstance(check.timestamp, datetime)
        assert check.details is not None

    def test_memory_check_healthy(self, health_checker):
        """Test memory health check when healthy"""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.Process') as mock_process:

            # Mock healthy memory usage
            mock_memory.return_value.percent = 50.0
            mock_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB

            mock_process_instance = Mock()
            mock_process_instance.memory_info.return_value.rss = 512 * 1024 * 1024  # 512MB
            mock_process.return_value = mock_process_instance

            check = health_checker.check_memory()

            assert check.name == "memory"
            assert check.status == HealthStatus.HEALTHY
            assert "normal limits" in check.message
            assert check.duration_ms > 0
            assert check.details["system_memory_percent"] == 50.0

    def test_memory_check_unhealthy(self, health_checker):
        """Test memory health check when unhealthy"""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.Process') as mock_process:

            # Mock unhealthy memory usage
            mock_memory.return_value.percent = 95.0
            mock_memory.return_value.available = 100 * 1024 * 1024  # 100MB

            mock_process_instance = Mock()
            mock_process_instance.memory_info.return_value.rss = 512 * 1024 * 1024  # 512MB
            mock_process.return_value = mock_process_instance

            check = health_checker.check_memory()

            assert check.name == "memory"
            assert check.status == HealthStatus.UNHEALTHY
            assert "too high" in check.message
            assert check.details["system_memory_percent"] == 95.0

    def test_disk_check_healthy(self, health_checker):
        """Test disk health check when healthy"""
        with patch('psutil.disk_usage') as mock_disk:
            # Mock healthy disk usage
            mock_disk.return_value.used = 50 * 1024 * 1024 * 1024  # 50GB
            mock_disk.return_value.total = 100 * 1024 * 1024 * 1024  # 100GB
            mock_disk.return_value.free = 50 * 1024 * 1024 * 1024  # 50GB

            check = health_checker.check_disk()

            assert check.name == "disk"
            assert check.status == HealthStatus.HEALTHY
            assert "normal limits" in check.message
            assert check.details["disk_usage_percent"] == 50.0

    def test_disk_check_unhealthy(self, health_checker):
        """Test disk health check when unhealthy"""
        with patch('psutil.disk_usage') as mock_disk:
            # Mock unhealthy disk usage
            mock_disk.return_value.used = 95 * 1024 * 1024 * 1024  # 95GB
            mock_disk.return_value.total = 100 * 1024 * 1024 * 1024  # 100GB
            mock_disk.return_value.free = 5 * 1024 * 1024 * 1024  # 5GB

            check = health_checker.check_disk()

            assert check.name == "disk"
            assert check.status == HealthStatus.UNHEALTHY
            assert "too high" in check.message
            assert check.details["disk_usage_percent"] == 95.0

    def test_agentdev_check_healthy(self, health_checker):
        """Test AgentDev health check when healthy"""
        with patch('agent_dev.core.agentdev.AgentDev') as mock_agentdev:
            # Mock healthy AgentDev
            mock_instance = Mock()
            mock_instance.execute_task.return_value = "✅ Test completed successfully"
            mock_agentdev.return_value = mock_instance

            check = health_checker.check_agentdev()

            assert check.name == "agentdev"
            assert check.status == HealthStatus.HEALTHY
            assert "operational" in check.message
            assert check.duration_ms > 0

    def test_agentdev_check_unhealthy(self, health_checker):
        """Test AgentDev health check when unhealthy"""
        with patch('agent_dev.core.agentdev.AgentDev') as mock_agentdev:
            # Mock unhealthy AgentDev
            mock_agentdev.side_effect = Exception("AgentDev failed to initialize")

            check = health_checker.check_agentdev()

            assert check.name == "agentdev"
            assert check.status == HealthStatus.UNHEALTHY
            assert "failed" in check.message
            assert "error" in check.details

    def test_run_all_checks_healthy(self, health_checker):
        """Test running all checks when all are healthy"""
        with patch.object(health_checker, 'check_database') as mock_db, \
             patch.object(health_checker, 'check_memory') as mock_mem, \
             patch.object(health_checker, 'check_disk') as mock_disk, \
             patch.object(health_checker, 'check_agentdev') as mock_agentdev:

            # Mock all checks as healthy
            mock_db.return_value.status = HealthStatus.HEALTHY
            mock_mem.return_value.status = HealthStatus.HEALTHY
            mock_disk.return_value.status = HealthStatus.HEALTHY
            mock_agentdev.return_value.status = HealthStatus.HEALTHY

            response = health_checker.run_all_checks()

            assert response.status == HealthStatus.HEALTHY
            assert len(response.checks) == 4
            assert response.metrics["healthy_checks"] == 4
            assert response.metrics["unhealthy_checks"] == 0
            assert response.metrics["degraded_checks"] == 0

    def test_run_all_checks_mixed(self, health_checker):
        """Test running all checks with mixed results"""
        with patch.object(health_checker, 'check_database') as mock_db, \
             patch.object(health_checker, 'check_memory') as mock_mem, \
             patch.object(health_checker, 'check_disk') as mock_disk, \
             patch.object(health_checker, 'check_agentdev') as mock_agentdev:

            # Mock mixed results
            mock_db.return_value.status = HealthStatus.HEALTHY
            mock_mem.return_value.status = HealthStatus.DEGRADED
            mock_disk.return_value.status = HealthStatus.HEALTHY
            mock_agentdev.return_value.status = HealthStatus.UNHEALTHY

            response = health_checker.run_all_checks()

            assert response.status == HealthStatus.UNHEALTHY  # Should be unhealthy due to one unhealthy check
            assert response.metrics["healthy_checks"] == 2
            assert response.metrics["degraded_checks"] == 1
            assert response.metrics["unhealthy_checks"] == 1

    def test_health_response_serialization(self, health_checker):
        """Test health response can be serialized to JSON"""
        response = health_checker.run_all_checks()

        # Convert to dict and back to test serialization
        response_dict = response.__dict__

        # Check that all required fields are present
        assert "status" in response_dict
        assert "timestamp" in response_dict
        assert "version" in response_dict
        assert "environment" in response_dict
        assert "uptime_seconds" in response_dict
        assert "checks" in response_dict
        assert "metrics" in response_dict

        # Test JSON serialization
        json_str = json.dumps(response_dict, default=str)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

class TestHealthEndpoints:
    """Test health check endpoints"""

    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app"""
        app = Mock()
        app.route = Mock(return_value=lambda func: func)
        return app

    def test_create_health_endpoints(self, mock_app):
        """Test health endpoints are created correctly"""
        config = {
            'version': '1.0.0',
            'environment': 'test',
            'database': {'path': ':memory:'}
        }

        from stillme_core.health import create_health_endpoints

        # This should not raise an exception
        create_health_endpoints(mock_app, config)

        # Verify route decorators were called
        assert mock_app.route.call_count >= 3  # /healthz, /readyz, /metrics

    def test_liveness_probe_success(self, mock_app):
        """Test liveness probe returns success"""
        config = {'version': '1.0.0', 'environment': 'test'}

        from stillme_core.health import create_health_endpoints
        create_health_endpoints(mock_app, config)

        # Get the liveness probe function
        liveness_func = mock_app.route.call_args_list[0][0][0]

        # Test the function
        response, status_code = liveness_func()

        assert status_code == 200
        assert response["status"] == "alive"
        assert "timestamp" in response

    def test_readiness_probe_success(self, mock_app):
        """Test readiness probe returns success"""
        config = {
            'version': '1.0.0',
            'environment': 'test',
            'database': {'path': ':memory:'}
        }

        from stillme_core.health import create_health_endpoints
        create_health_endpoints(mock_app, config)

        # Get the readiness probe function
        readiness_func = mock_app.route.call_args_list[1][0][0]

        # Test the function
        response, status_code = readiness_func()

        assert status_code == 200
        assert "status" in response
        assert "checks" in response
        assert "metrics" in response

    def test_metrics_endpoint_success(self, mock_app):
        """Test metrics endpoint returns Prometheus format"""
        config = {
            'version': '1.0.0',
            'environment': 'test',
            'database': {'path': ':memory:'}
        }

        from stillme_core.health import create_health_endpoints
        create_health_endpoints(mock_app, config)

        # Get the metrics function
        metrics_func = mock_app.route.call_args_list[2][0][0]

        # Test the function
        response, status_code, headers = metrics_func()

        assert status_code == 200
        assert headers["Content-Type"] == "text/plain"
        assert "stillme_health_status" in response
        assert "stillme_uptime_seconds" in response
        assert "stillme_version_info" in response
