"""
Test suite for Learning Scheduler
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

pytest.skip("Module not available", allow_module_level=True)

from stillme_core.learning.automation_service import (
    AutomationServiceConfig,
    LearningAutomationService,
)
from stillme_core.learning.scheduler import (
    LearningScheduler,
    SchedulerConfig,
)


class TestSchedulerConfig:
    """Test SchedulerConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = SchedulerConfig()

        assert not config.enabled
        assert config.cron_expression == "30 2 * * *"
        assert config.timezone == "Asia/Ho_Chi_Minh"
        assert config.jitter_seconds == 300
        assert config.max_concurrent_sessions == 1
        assert config.skip_if_cpu_high
        assert config.cpu_threshold == 70.0
        assert config.skip_if_memory_high
        assert config.memory_threshold_mb == 1024
        assert config.skip_if_tokens_low
        assert config.min_tokens_required == 1000

    def test_custom_config(self):
        """Test custom configuration"""
        config = SchedulerConfig(
            enabled=True,
            cron_expression="0 3 * * *",
            timezone="UTC",
            jitter_seconds=600,
            max_concurrent_sessions=2,
            cpu_threshold=80.0,
            memory_threshold_mb=2048
        )

        assert config.enabled
        assert config.cron_expression == "0 3 * * *"
        assert config.timezone == "UTC"
        assert config.jitter_seconds == 600
        assert config.max_concurrent_sessions == 2
        assert config.cpu_threshold == 80.0
        assert config.memory_threshold_mb == 2048

class TestLearningScheduler:
    """Test LearningScheduler"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return SchedulerConfig(
            enabled=True,
            cron_expression="30 2 * * *",
            timezone="Asia/Ho_Chi_Minh",
            jitter_seconds=300
        )

    @pytest.fixture
    def scheduler(self, config):
        """Test scheduler instance"""
        with patch('stillme_core.learning.scheduler.APSCHEDULER_AVAILABLE', True):
            return LearningScheduler(config)

    @pytest.mark.asyncio
    async def test_initialize(self, scheduler):
        """Test scheduler initialization"""
        with patch('stillme_core.learning.scheduler.AsyncIOScheduler') as mock_scheduler_class:
            mock_scheduler = Mock()
            mock_scheduler_class.return_value = mock_scheduler

            result = await scheduler.initialize()

            assert result
            assert scheduler.scheduler == mock_scheduler
            mock_scheduler.add_listener.assert_called()

    @pytest.mark.asyncio
    async def test_start(self, scheduler):
        """Test scheduler start"""
        with patch('stillme_core.learning.scheduler.AsyncIOScheduler') as mock_scheduler_class:
            mock_scheduler = Mock()
            mock_scheduler_class.return_value = mock_scheduler

            await scheduler.initialize()
            result = await scheduler.start()

            assert result
            assert scheduler.is_running
            mock_scheduler.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, scheduler):
        """Test scheduler stop"""
        with patch('stillme_core.learning.scheduler.AsyncIOScheduler') as mock_scheduler_class:
            mock_scheduler = Mock()
            mock_scheduler_class.return_value = mock_scheduler

            await scheduler.initialize()
            await scheduler.start()
            result = await scheduler.stop()

            assert result
            assert not scheduler.is_running
            mock_scheduler.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_schedule_daily_training(self, scheduler):
        """Test scheduling daily training"""
        with patch('stillme_core.learning.scheduler.AsyncIOScheduler') as mock_scheduler_class:
            mock_scheduler = Mock()
            mock_job = Mock()
            mock_job.next_run_time = datetime.now() + timedelta(hours=1)
            mock_scheduler.add_job.return_value = mock_job
            mock_scheduler_class.return_value = mock_scheduler

            await scheduler.initialize()

            async def test_training():
                return {"status": "success"}

            result = await scheduler.schedule_daily_training(test_training)

            assert result
            assert 'daily_training' in scheduler.scheduled_jobs
            assert scheduler.stats['total_jobs'] == 1
            mock_scheduler.add_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_resource_check(self, scheduler):
        """Test resource checking"""
        with patch('builtins.__import__') as mock_import:
            # Mock psutil import
            mock_psutil = Mock()
            mock_psutil.cpu_percent.return_value = 50.0
            mock_memory = Mock()
            mock_memory.used = 512 * 1024 * 1024  # 512MB
            mock_psutil.virtual_memory.return_value = mock_memory

            def import_side_effect(name, *args, **kwargs):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = await scheduler._check_resources()

            assert result
            mock_psutil.cpu_percent.assert_called_once_with(interval=1)
            mock_psutil.virtual_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_resource_check_high_cpu(self, scheduler):
        """Test resource check with high CPU"""
        with patch('builtins.__import__') as mock_import:
            # Mock psutil import with high CPU
            mock_psutil = Mock()
            mock_psutil.cpu_percent.return_value = 80.0
            mock_memory = Mock()
            mock_memory.used = 512 * 1024 * 1024  # 512MB
            mock_psutil.virtual_memory.return_value = mock_memory

            def import_side_effect(name, *args, **kwargs):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = await scheduler._check_resources()

            assert not result  # Should fail due to high CPU

    def test_get_status(self, scheduler):
        """Test getting scheduler status"""
        status = scheduler.get_status()

        assert 'enabled' in status
        assert 'running' in status
        assert 'timezone' in status
        assert 'cron_expression' in status
        assert 'scheduled_jobs' in status
        assert 'statistics' in status
        assert 'apscheduler_available' in status

class TestAutomationService:
    """Test LearningAutomationService"""

    @pytest.fixture
    def service_config(self):
        """Test service configuration"""
        return AutomationServiceConfig(
            enabled=True,
            health_check_interval=60,
            log_level="INFO",
            enable_metrics=True
        )

    @pytest.fixture
    def service(self, service_config):
        """Test service instance"""
        with patch('stillme_core.learning.automation_service.EvolutionaryLearningSystem'):
            return LearningAutomationService(service_config)

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization"""
        with patch('stillme_core.learning.automation_service.get_learning_scheduler') as mock_get_scheduler:
            mock_scheduler = Mock()
            mock_scheduler.initialize = AsyncMock(return_value=True)
            mock_scheduler.schedule_daily_training = AsyncMock(return_value=True)
            mock_get_scheduler.return_value = mock_scheduler

            result = await service.initialize()

            assert result
            assert service.learning_system is not None
            assert service.scheduler == mock_scheduler

    @pytest.mark.asyncio
    async def test_start(self, service):
        """Test service start"""
        with patch('stillme_core.learning.automation_service.get_learning_scheduler') as mock_get_scheduler:
            mock_scheduler = Mock()
            mock_scheduler.initialize = AsyncMock(return_value=True)
            mock_scheduler.start = AsyncMock(return_value=True)
            mock_scheduler.schedule_daily_training = AsyncMock(return_value=True)
            mock_get_scheduler.return_value = mock_scheduler

            result = await service.start()

            assert result
            assert service.status.running
            assert service.status.start_time is not None
            mock_scheduler.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, service):
        """Test service stop"""
        with patch('stillme_core.learning.automation_service.get_learning_scheduler'):
            mock_scheduler = Mock()
            mock_scheduler.stop = AsyncMock(return_value=True)
            service.scheduler = mock_scheduler
            service.status.running = True

            result = await service.stop()

            assert result
            assert not service.status.running
            mock_scheduler.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_training_session(self, service):
        """Test running training session"""
        with patch('stillme_core.learning.automation_service.EvolutionaryLearningSystem') as mock_learning_class:
            mock_learning = Mock()
            mock_session = Mock()
            mock_session.session_id = "test_session"
            mock_learning.daily_learning_session = AsyncMock(return_value=mock_session)
            mock_learning_class.return_value = mock_learning
            service.learning_system = mock_learning

            result = await service._run_training_session()

            assert result['status'] == 'success'
            assert 'session_id' in result
            assert 'duration' in result
            assert service.stats['total_training_sessions'] == 1
            assert service.stats['successful_sessions'] == 1

    @pytest.mark.asyncio
    async def test_run_training_session_failure(self, service):
        """Test training session failure"""
        with patch('stillme_core.learning.automation_service.EvolutionaryLearningSystem') as mock_learning_class:
            mock_learning = Mock()
            mock_learning.daily_learning_session = AsyncMock(side_effect=Exception("Test error"))
            mock_learning_class.return_value = mock_learning
            service.learning_system = mock_learning

            result = await service._run_training_session()

            assert result['status'] == 'failed'
            assert 'error' in result
            assert service.stats['total_training_sessions'] == 1
            assert service.stats['failed_sessions'] == 1

    def test_get_status(self, service):
        """Test getting service status"""
        status = service.get_status()

        assert 'service' in status
        assert 'statistics' in status
        assert 'scheduler' in status
        assert 'learning_system' in status
        assert 'config' in status

class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_scheduler_with_learning_system(self):
        """Test scheduler integration with learning system"""
        with patch('stillme_core.learning.scheduler.APSCHEDULER_AVAILABLE', True), \
             patch('stillme_core.learning.scheduler.AsyncIOScheduler') as mock_scheduler_class, \
             patch('stillme_core.learning.automation_service.EvolutionaryLearningSystem') as mock_learning_class:

            # Setup mocks
            mock_scheduler = Mock()
            mock_job = Mock()
            mock_job.next_run_time = datetime.now() + timedelta(hours=1)
            mock_scheduler.add_job.return_value = mock_job
            mock_scheduler_class.return_value = mock_scheduler

            mock_learning = Mock()
            mock_session = Mock()
            mock_session.session_id = "integration_test"
            mock_learning.daily_learning_session = AsyncMock(return_value=mock_session)
            mock_learning_class.return_value = mock_learning

            # Create service
            config = AutomationServiceConfig()
            service = LearningAutomationService(config)
            service.learning_system = mock_learning

            # Initialize and start
            result = await service.initialize()
            assert result

            # Test training session
            training_result = await service._run_training_session()
            assert training_result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown"""
        with patch('stillme_core.learning.scheduler.APSCHEDULER_AVAILABLE', True), \
             patch('stillme_core.learning.scheduler.AsyncIOScheduler') as mock_scheduler_class, \
             patch('stillme_core.learning.automation_service.EvolutionaryLearningSystem') as mock_learning_class:

            # Setup mocks
            mock_scheduler = Mock()
            mock_scheduler.shutdown = AsyncMock()
            mock_scheduler_class.return_value = mock_scheduler

            mock_learning_class.return_value = Mock()

            # Create service
            config = AutomationServiceConfig()
            service = LearningAutomationService(config)

            # Initialize and start
            await service.initialize()
            await service.start()

            # Test shutdown
            await service.shutdown()

            # Verify shutdown was called
            mock_scheduler.shutdown.assert_called()
            assert not service.status.running
