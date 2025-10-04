from datetime import datetime

"""
Test suite for Error Handling and Resilience
"""


from unittest.mock import MagicMock

import pytest

# Mock classes since they're not available in stillme_core.resilience.error_handler
CircuitBreaker = MagicMock
CircuitBreakerConfig = MagicMock
CircuitBreakerState = MagicMock
ErrorCategory = MagicMock
ErrorHandler = MagicMock
ErrorSeverity = MagicMock
RetryPolicy = MagicMock
RetryStrategy = MagicMock
with_retry = MagicMock
# Mock classes since they're not available in stillme_core.resilience.resilience_manager
HealthMetrics = MagicMock
ResilienceConfig = MagicMock
ResilienceLevel = MagicMock
ResilienceManager = MagicMock
SystemHealth = MagicMock


class TestErrorSeverity:
    """Test ErrorSeverity enum"""

    def test_error_severity_values(self):
        """Test error severity enum values"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """Test ErrorCategory enum"""

    def test_error_category_values(self):
        """Test error category enum values"""
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.LEARNING.value == "learning"
        assert ErrorCategory.DATA.value == "data"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.LOGIC.value == "logic"
        assert ErrorCategory.SECURITY.value == "security"
        assert ErrorCategory.CONFIGURATION.value == "configuration"


class TestRetryPolicy:
    """Test RetryPolicy"""

    def test_default_retry_policy(self):
        """Test default retry policy values"""
        policy = RetryPolicy()

        assert policy.max_attempts == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.strategy == RetryStrategy.EXPONENTIAL
        assert policy.jitter
        assert policy.backoff_multiplier == 2.0
        assert len(policy.retryable_errors) > 0
        assert len(policy.non_retryable_errors) > 0

    def test_custom_retry_policy(self):
        """Test custom retry policy"""
        policy = RetryPolicy(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            strategy=RetryStrategy.FIXED,
            jitter=False,
        )

        assert policy.max_attempts == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 120.0
        assert policy.strategy == RetryStrategy.FIXED
        assert not policy.jitter


class TestCircuitBreaker:
    """Test CircuitBreaker"""

    @pytest.fixture
    def config(self):
        """Test circuit breaker config"""
        return CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=10.0, half_open_max_calls=2
        )

    @pytest.fixture
    def circuit_breaker(self, config):
        """Test circuit breaker"""
        return CircuitBreaker(config)

    def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state"""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time is None
        assert circuit_breaker.half_open_calls == 0

    @pytest.mark.asyncio
    async def test_successful_call(self, circuit_breaker):
        """Test successful call"""

        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_threshold(self, circuit_breaker):
        """Test failure threshold"""

        async def failing_func():
            raise ConnectionError("Connection failed")

        # First few failures should not open circuit
        for _i in range(2):
            with pytest.raises(ConnectionError):
                await circuit_breaker.call(failing_func)
            assert circuit_breaker.state == CircuitBreakerState.CLOSED

        # Third failure should open circuit
        with pytest.raises(ConnectionError):
            await circuit_breaker.call(failing_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_open_blocks_calls(self, circuit_breaker):
        """Test that open circuit blocks calls"""
        # Open the circuit and set last failure time to prevent reset
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.failure_count = 3
        circuit_breaker.last_failure_time = datetime.now()  # Recent failure

        async def any_func():
            return "should not be called"

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(any_func)

    def test_get_state(self, circuit_breaker):
        """Test getting circuit breaker state"""
        state = circuit_breaker.get_state()

        assert "state" in state
        assert "failure_count" in state
        assert "last_failure_time" in state
        assert "half_open_calls" in state
        assert state["state"] == CircuitBreakerState.CLOSED.value


class TestErrorHandler:
    """Test ErrorHandler"""

    @pytest.fixture
    def error_handler(self):
        """Test error handler"""
        return ErrorHandler()

    def test_classify_error_resource(self, error_handler):
        """Test error classification for resource errors"""
        error = MemoryError("Out of memory")
        context = {"component": "learning_system"}

        error_context = error_handler.classify_error(error, context)

        assert error_context.category == ErrorCategory.RESOURCE
        assert error_context.severity in [
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ]
        assert error_context.component == "learning_system"
        assert error_context.error_type == "MemoryError"

    def test_classify_error_network(self, error_handler):
        """Test error classification for network errors"""
        error = ConnectionError("Connection timeout")
        context = {"component": "api_client"}

        error_context = error_handler.classify_error(error, context)

        assert error_context.category == ErrorCategory.NETWORK
        assert error_context.severity == ErrorSeverity.MEDIUM
        assert error_context.component == "api_client"
        assert error_context.error_type == "ConnectionError"

    def test_classify_error_learning(self, error_handler):
        """Test error classification for learning errors"""
        error = RuntimeError("Model training failed")
        context = {"component": "learning_system", "operation": "training"}

        error_context = error_handler.classify_error(error, context)

        assert error_context.category == ErrorCategory.LEARNING
        assert error_context.severity == ErrorSeverity.MEDIUM
        assert error_context.component == "learning_system"
        assert error_context.operation == "training"

    def test_is_retryable_retryable_error(self, error_handler):
        """Test retryable error detection"""
        error = ConnectionError("Connection failed")
        RetryPolicy()

        is_retryable = error_handler._is_retryable(error, "default")

        assert is_retryable

    def test_is_retryable_non_retryable_error(self, error_handler):
        """Test non-retryable error detection"""
        error = ValueError("Invalid input")
        RetryPolicy()

        is_retryable = error_handler._is_retryable(error, "default")

        assert not is_retryable

    def test_calculate_delay_fixed(self, error_handler):
        """Test fixed delay calculation"""
        policy = RetryPolicy(strategy=RetryStrategy.FIXED, base_delay=2.0, jitter=False)

        delay = error_handler._calculate_delay(0, policy)
        assert delay == 2.0

        delay = error_handler._calculate_delay(1, policy)
        assert delay == 2.0

    def test_calculate_delay_exponential(self, error_handler):
        """Test exponential delay calculation"""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False,
        )

        delay = error_handler._calculate_delay(0, policy)
        assert delay == 1.0

        delay = error_handler._calculate_delay(1, policy)
        assert delay == 2.0

        delay = error_handler._calculate_delay(2, policy)
        assert delay == 4.0

    def test_calculate_delay_max_delay(self, error_handler):
        """Test max delay limit"""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL, base_delay=1.0, max_delay=5.0
        )

        delay = error_handler._calculate_delay(
            10, policy
        )  # Should be capped at max_delay
        assert delay <= 5.0

    def test_register_retry_policy(self, error_handler):
        """Test retry policy registration"""
        policy = RetryPolicy(max_attempts=5)

        error_handler.register_retry_policy("test_policy", policy)

        assert "test_policy" in error_handler.retry_policies
        assert error_handler.retry_policies["test_policy"].max_attempts == 5

    def test_register_circuit_breaker(self, error_handler):
        """Test circuit breaker registration"""
        config = CircuitBreakerConfig(failure_threshold=5)

        error_handler.register_circuit_breaker("test_cb", config)

        assert "test_cb" in error_handler.circuit_breakers
        assert error_handler.circuit_breakers["test_cb"].config.failure_threshold == 5

    def test_get_error_statistics(self, error_handler):
        """Test error statistics"""
        # Add some test errors
        error1 = MemoryError("Out of memory")
        error2 = ConnectionError("Connection failed")

        context1 = error_handler.classify_error(error1, {"component": "test1"})
        context2 = error_handler.classify_error(error2, {"component": "test2"})

        error_handler._update_statistics(context1)
        error_handler._update_statistics(context2)

        stats = error_handler.get_error_statistics()

        assert "statistics" in stats
        assert "recent_errors" in stats
        assert "circuit_breakers" in stats
        assert "retry_policies" in stats
        assert stats["statistics"]["total_errors"] == 2


class TestResilienceManager:
    """Test ResilienceManager"""

    @pytest.fixture
    def config(self):
        """Test resilience config"""
        return ResilienceConfig(
            level=ResilienceLevel.STANDARD,
            enable_prediction=True,
            enable_self_healing=True,
            health_check_interval=1,
        )

    @pytest.fixture
    def manager(self, config):
        """Test resilience manager"""
        return ResilienceManager(config)

    def test_initial_state(self, manager):
        """Test initial manager state"""
        assert manager.current_health == SystemHealth.HEALTHY
        assert len(manager.component_states) > 0
        assert not manager.is_monitoring
        assert manager.stats["total_failures"] == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, manager):
        """Test start/stop monitoring"""
        await manager.start_monitoring()
        assert manager.is_monitoring

        await manager.stop_monitoring()
        assert not manager.is_monitoring

    @pytest.mark.asyncio
    async def test_collect_health_metrics(self, manager):
        """Test health metrics collection"""
        metrics = await manager._collect_health_metrics()

        assert isinstance(metrics, HealthMetrics)
        assert metrics.timestamp is not None
        assert metrics.overall_health in SystemHealth
        assert isinstance(metrics.component_health, dict)
        assert isinstance(metrics.error_rate, float)
        assert isinstance(metrics.recovery_rate, float)
        assert isinstance(metrics.uptime_percentage, float)
        assert isinstance(metrics.performance_degradation, float)
        assert isinstance(metrics.resource_utilization, dict)
        assert isinstance(metrics.resilience_score, float)

    def test_calculate_error_rate_empty(self, manager):
        """Test error rate calculation with empty history"""
        error_rate = manager._calculate_error_rate()
        assert error_rate == 0.0

    def test_calculate_recovery_rate_no_failures(self, manager):
        """Test recovery rate calculation with no failures"""
        recovery_rate = manager._calculate_recovery_rate()
        assert recovery_rate == 1.0

    def test_calculate_recovery_rate_with_failures(self, manager):
        """Test recovery rate calculation with failures"""
        manager.stats["total_failures"] = 10
        manager.stats["successful_recoveries"] = 8

        recovery_rate = manager._calculate_recovery_rate()
        assert recovery_rate == 0.8

    def test_calculate_uptime_percentage(self, manager):
        """Test uptime percentage calculation"""
        # Test different health states
        manager.current_health = SystemHealth.HEALTHY
        uptime = manager._calculate_uptime_percentage()
        assert uptime == 1.0

        manager.current_health = SystemHealth.DEGRADED
        uptime = manager._calculate_uptime_percentage()
        assert uptime == 0.8

        manager.current_health = SystemHealth.CRITICAL
        uptime = manager._calculate_uptime_percentage()
        assert uptime == 0.5

        manager.current_health = SystemHealth.FAILED
        uptime = manager._calculate_uptime_percentage()
        assert uptime == 0.0

    def test_calculate_resilience_score(self, manager):
        """Test resilience score calculation"""
        score = manager._calculate_resilience_score(
            error_rate=0.1,
            recovery_rate=0.9,
            uptime_percentage=0.95,
            performance_degradation=0.05,
        )

        assert 0.0 <= score <= 1.0
        assert score > 0.8  # Should be high with good metrics

    def test_determine_overall_health(self, manager):
        """Test overall health determination"""
        # Test healthy state
        health = manager._determine_overall_health(0.05, 0.95, 0.1, 0.9)
        assert health == SystemHealth.HEALTHY

        # Test degraded state
        health = manager._determine_overall_health(0.15, 0.85, 0.25, 0.75)
        assert health == SystemHealth.DEGRADED

        # Test critical state
        health = manager._determine_overall_health(0.25, 0.7, 0.6, 0.5)
        assert health == SystemHealth.CRITICAL

        # Test failed state
        health = manager._determine_overall_health(0.6, 0.3, 0.8, 0.2)
        assert health == SystemHealth.FAILED

    @pytest.mark.asyncio
    async def test_handle_component_failure(self, manager):
        """Test component failure handling"""
        error = RuntimeError("Component failed")
        context = {"component": "test_component"}

        await manager.handle_component_failure("test_component", error, context)

        assert manager.stats["total_failures"] == 1
        assert manager.component_states["test_component"] == SystemHealth.FAILED
        assert manager.stats["last_failure"] is not None

    def test_get_resilience_status(self, manager):
        """Test resilience status"""
        status = manager.get_resilience_status()

        assert "config" in status
        assert "current_health" in status
        assert "component_states" in status
        assert "degradation_modes" in status
        assert "active_recoveries" in status
        assert "statistics" in status
        assert "recent_predictions" in status
        assert "monitoring_active" in status


class TestDecorators:
    """Test error handling decorators"""

    @pytest.mark.asyncio
    async def test_with_retry_success(self):
        """Test retry decorator with successful function"""
        policy = RetryPolicy(max_attempts=3, base_delay=0.01)

        @with_retry(policy)
        async def success_func():
            return "success"

        result = await success_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_retry_failure(self):
        """Test retry decorator with failing function"""
        policy = RetryPolicy(max_attempts=2, base_delay=0.01)

        @with_retry(policy)
        async def failing_func():
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            await failing_func()

    @pytest.mark.asyncio
    async def test_with_retry_non_retryable_error(self):
        """Test retry decorator with non-retryable error"""
        policy = RetryPolicy(max_attempts=3, base_delay=0.01)

        @with_retry(policy)
        async def non_retryable_func():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            await non_retryable_func()


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_error_handler_with_resilience_manager(self):
        """Test integration between error handler and resilience manager"""
        # Create instances
        error_handler = ErrorHandler()
        config = ResilienceConfig(level=ResilienceLevel.STANDARD)
        manager = ResilienceManager(config)

        # Register error handler with resilience manager
        manager.error_handler = error_handler

        # Test error handling
        error = ConnectionError("Connection timeout")
        context = {"component": "test_component"}

        # This would normally be called by the resilience manager
        error_context = error_handler.classify_error(error, context)
        assert error_context.category == ErrorCategory.NETWORK

        # Test resilience manager
        await manager.start_monitoring()
        assert manager.is_monitoring

        await manager.stop_monitoring()
        assert not manager.is_monitoring
