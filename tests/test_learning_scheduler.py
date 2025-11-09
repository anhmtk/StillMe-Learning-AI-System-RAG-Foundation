"""
Tests for Learning Scheduler Service
Tests scheduler start/stop, learning cycles, error recovery, and interval configuration
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import asyncio
from backend.services.learning_scheduler import LearningScheduler
from backend.services.rss_fetcher import RSSFetcher


class TestLearningScheduler:
    """Test suite for LearningScheduler"""
    
    @pytest.fixture
    def mock_rss_fetcher(self):
        """Create mock RSS fetcher"""
        fetcher = Mock(spec=RSSFetcher)
        fetcher.feeds = ["https://example.com/feed.xml"]
        fetcher.fetch_feeds = Mock(return_value=[
            {"title": "Test Article", "link": "https://example.com/article", "summary": "Test summary"}
        ])
        return fetcher
    
    @pytest.fixture
    def scheduler(self, mock_rss_fetcher):
        """Create scheduler instance with mock RSS fetcher"""
        return LearningScheduler(
            rss_fetcher=mock_rss_fetcher,
            interval_hours=1,  # Use 1 hour for faster tests
            auto_add_to_rag=True
        )
    
    @pytest.mark.asyncio
    async def test_run_learning_cycle_success(self, scheduler, mock_rss_fetcher):
        """Test successful learning cycle execution"""
        result = await scheduler.run_learning_cycle()
        
        assert result["cycle_number"] == 1
        assert result["entries_fetched"] == 1
        assert "timestamp" in result
        assert "next_run" in result
        assert scheduler.cycle_count == 1
        assert scheduler.last_run_time is not None
        assert scheduler.next_run_time is not None
        mock_rss_fetcher.fetch_feeds.assert_called_once_with(max_items_per_feed=5)
    
    @pytest.mark.asyncio
    async def test_run_learning_cycle_error_handling(self, scheduler, mock_rss_fetcher):
        """Test error handling in learning cycle"""
        # Mock fetch_feeds to raise exception
        mock_rss_fetcher.fetch_feeds.side_effect = Exception("Network error")
        
        result = await scheduler.run_learning_cycle()
        
        assert "error" in result
        assert result["error"] == "Network error"
        assert result["cycle_number"] == 0  # Cycle count not incremented on error
        assert scheduler.cycle_count == 0
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler):
        """Test starting the scheduler"""
        await scheduler.start()
        
        assert scheduler.is_running is True
        assert scheduler._task is not None
        assert not scheduler._task.done()
        
        # Cleanup
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_start_scheduler_already_running(self, scheduler):
        """Test starting scheduler when already running"""
        scheduler.is_running = True
        
        await scheduler.start()
        
        # Should not create new task
        assert scheduler._task is None
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler):
        """Test stopping the scheduler"""
        # Start scheduler first
        await scheduler.start()
        assert scheduler.is_running is True
        
        # Stop scheduler
        await scheduler.stop()
        
        assert scheduler.is_running is False
        if scheduler._task:
            assert scheduler._task.cancelled() or scheduler._task.done()
    
    @pytest.mark.asyncio
    async def test_stop_scheduler_not_running(self, scheduler):
        """Test stopping scheduler when not running"""
        scheduler.is_running = False
        
        await scheduler.stop()
        
        # Should handle gracefully
        assert scheduler.is_running is False
    
    def test_get_status(self, scheduler):
        """Test getting scheduler status"""
        scheduler.cycle_count = 5
        scheduler.last_run_time = datetime.now()
        scheduler.next_run_time = datetime.now() + timedelta(hours=1)
        
        status = scheduler.get_status()
        
        assert status["is_running"] is False
        assert status["interval_hours"] == 1
        assert status["auto_add_to_rag"] is True
        assert status["cycle_count"] == 5
        assert status["last_run_time"] is not None
        assert status["next_run_time"] is not None
        assert status["feeds_configured"] == 1
    
    def test_get_status_no_runs(self, scheduler):
        """Test getting status when no cycles have run"""
        status = scheduler.get_status()
        
        assert status["last_run_time"] is None
        assert status["next_run_time"] is None
        assert status["cycle_count"] == 0
    
    def test_interval_configuration(self):
        """Test scheduler with different interval configurations"""
        scheduler = LearningScheduler(interval_hours=6)
        
        assert scheduler.interval_hours == 6
        status = scheduler.get_status()
        assert status["interval_hours"] == 6
    
    def test_auto_add_to_rag_configuration(self):
        """Test scheduler with auto_add_to_rag disabled"""
        scheduler = LearningScheduler(auto_add_to_rag=False)
        
        assert scheduler.auto_add_to_rag is False
        status = scheduler.get_status()
        assert status["auto_add_to_rag"] is False
    
    @pytest.mark.asyncio
    async def test_scheduler_loop_runs_cycles(self, scheduler, mock_rss_fetcher):
        """Test that scheduler loop runs learning cycles"""
        scheduler.is_running = True
        
        # Mock asyncio.sleep to return immediately and stop after first cycle
        call_count = 0
        async def mock_sleep_immediate(delay):
            nonlocal call_count
            call_count += 1
            # After first sleep (after first cycle), stop the loop
            if call_count >= 1:
                scheduler.is_running = False
        
        with patch('backend.services.learning_scheduler.asyncio.sleep', side_effect=mock_sleep_immediate):
            # Create task
            task = asyncio.create_task(scheduler._scheduler_loop())
            
            # Wait for task to complete or timeout
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Should have called fetch_feeds at least once
        assert mock_rss_fetcher.fetch_feeds.called
    
    @pytest.mark.asyncio
    async def test_scheduler_loop_error_recovery(self, scheduler, mock_rss_fetcher):
        """Test error recovery in scheduler loop"""
        scheduler.is_running = True
        mock_rss_fetcher.fetch_feeds.side_effect = Exception("Temporary error")
        
        # Mock asyncio.sleep to return immediately and stop after error handling
        call_count = 0
        async def mock_sleep_immediate(delay):
            nonlocal call_count
            call_count += 1
            # After error sleep (60 seconds), stop the loop
            if call_count >= 1:
                scheduler.is_running = False
        
        with patch('backend.services.learning_scheduler.asyncio.sleep', side_effect=mock_sleep_immediate):
            task = asyncio.create_task(scheduler._scheduler_loop())
            
            # Wait for task to complete or timeout
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Should have attempted to fetch (error occurred but loop continued)
        assert mock_rss_fetcher.fetch_feeds.called
    
    @pytest.mark.asyncio
    async def test_scheduler_loop_cancellation(self, scheduler):
        """Test scheduler loop handles cancellation properly"""
        scheduler.is_running = True
        
        task = asyncio.create_task(scheduler._scheduler_loop())
        
        # Cancel immediately
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Task should be cancelled
        assert task.cancelled()
    
    @pytest.mark.asyncio
    async def test_multiple_cycles(self, scheduler, mock_rss_fetcher):
        """Test running multiple learning cycles"""
        # Run first cycle
        result1 = await scheduler.run_learning_cycle()
        assert result1["cycle_number"] == 1
        
        # Run second cycle
        result2 = await scheduler.run_learning_cycle()
        assert result2["cycle_number"] == 2
        
        assert scheduler.cycle_count == 2
        assert mock_rss_fetcher.fetch_feeds.call_count == 2
    
    def test_scheduler_initialization_defaults(self):
        """Test scheduler initialization with default values"""
        scheduler = LearningScheduler()
        
        assert scheduler.interval_hours == 4  # Default
        assert scheduler.auto_add_to_rag is True  # Default
        assert scheduler.is_running is False
        assert scheduler.cycle_count == 0
        assert scheduler.rss_fetcher is not None
    
    def test_scheduler_initialization_custom(self):
        """Test scheduler initialization with custom values"""
        custom_fetcher = Mock(spec=RSSFetcher)
        scheduler = LearningScheduler(
            rss_fetcher=custom_fetcher,
            interval_hours=8,
            auto_add_to_rag=False
        )
        
        assert scheduler.rss_fetcher == custom_fetcher
        assert scheduler.interval_hours == 8
        assert scheduler.auto_add_to_rag is False

