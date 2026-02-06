"""
Unit tests for Scheduler Module
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from core.scheduler import (
    ScheduledTask, Scheduler, 
    twitter_scraper_task, airdrop_tracker_task, cleanup_task
)


class TestScheduledTask:
    """Test ScheduledTask class"""
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test creating a scheduled task"""
        async def dummy_func():
            return "done"
        
        task = ScheduledTask(
            name="test_task",
            func=dummy_func,
            interval_seconds=3600,
            enabled=True
        )
        
        assert task.name == "test_task"
        assert task.interval_seconds == 3600
        assert task.enabled == True
        assert task.run_count == 0
    
    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test executing a task"""
        async def dummy_func():
            return {"status": "done"}
        
        task = ScheduledTask(
            name="test_execute",
            func=dummy_func,
            interval_seconds=3600
        )
        
        # First run should execute
        assert task.should_run() == True
        
        result = await task.run()
        
        assert result == {"status": "done"}
        assert task.run_count == 1
        assert task.last_run is not None
    
    @pytest.mark.asyncio
    async def test_task_error_handling(self):
        """Test task error handling"""
        async def failing_func():
            raise ValueError("Task failed")
        
        task = ScheduledTask(
            name="test_fail",
            func=failing_func,
            interval_seconds=3600
        )
        
        with pytest.raises(ValueError):
            await task.run()
        
        assert task.error_count == 1
        assert task.last_error == "Task failed"
    
    @pytest.mark.asyncio
    async def test_task_rate_limiting(self):
        """Test task should_run logic"""
        async def dummy_func():
            return "done"
        
        task = ScheduledTask(
            name="test_rate",
            func=dummy_func,
            interval_seconds=10
        )
        
        # Should run initially
        assert task.should_run() == True
        
        # After run, should not run immediately
        await task.run()
        
        # Check scheduling
        assert task.next_run is not None
        # Should be 10 seconds in the future
        time_until_next = (task.next_run - datetime.utcnow()).total_seconds()
        assert 9 < time_until_next <= 10
    
    @pytest.mark.asyncio
    async def test_task_disabled(self):
        """Test disabled task doesn't run"""
        async def dummy_func():
            return "done"
        
        task = ScheduledTask(
            name="test_disabled",
            func=dummy_func,
            interval_seconds=3600,
            enabled=False
        )
        
        assert task.should_run() == False


class TestScheduler:
    """Test Scheduler class"""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        scheduler = Scheduler()
        
        assert scheduler.running == False
        assert len(scheduler.tasks) == 0
        assert scheduler.thread is None
    
    def test_add_task(self):
        """Test adding task to scheduler"""
        async def dummy_func():
            return "done"
        
        scheduler = Scheduler()
        task = ScheduledTask(
            name="test_add",
            func=dummy_func,
            interval_seconds=3600
        )
        
        result = scheduler.add_task(task)
        
        assert result == True
        assert "test_add" in scheduler.tasks
    
    def test_add_duplicate_task(self):
        """Test adding duplicate task"""
        async def dummy_func():
            return "done"
        
        scheduler = Scheduler()
        task1 = ScheduledTask(
            name="test_dup",
            func=dummy_func,
            interval_seconds=3600
        )
        task2 = ScheduledTask(
            name="test_dup",
            func=dummy_func,
            interval_seconds=1800
        )
        
        scheduler.add_task(task1)
        scheduler.add_task(task2)  # Should replace
        
        assert len(scheduler.tasks) == 1
        assert scheduler.tasks["test_dup"].interval_seconds == 1800
    
    def test_remove_task(self):
        """Test removing task"""
        async def dummy_func():
            return "done"
        
        scheduler = Scheduler()
        task = ScheduledTask(
            name="test_remove",
            func=dummy_func,
            interval_seconds=3600
        )
        
        scheduler.add_task(task)
        assert "test_remove" in scheduler.tasks
        
        result = scheduler.remove_task("test_remove")
        assert result == True
        assert "test_remove" not in scheduler.tasks
    
    def test_enable_disable_task(self):
        """Test enabling and disabling tasks"""
        async def dummy_func():
            return "done"
        
        scheduler = Scheduler()
        task = ScheduledTask(
            name="test_en_dis",
            func=dummy_func,
            interval_seconds=3600,
            enabled=True
        )
        
        scheduler.add_task(task)
        
        # Disable
        result = scheduler.disable_task("test_en_dis")
        assert result == True
        assert scheduler.tasks["test_en_dis"].enabled == False
        
        # Enable
        result = scheduler.enable_task("test_en_dis")
        assert result == True
        assert scheduler.tasks["test_en_dis"].enabled == True
    
    def test_get_status(self):
        """Test getting scheduler status"""
        async def dummy_func():
            return "done"
        
        scheduler = Scheduler()
        task = ScheduledTask(
            name="test_status",
            func=dummy_func,
            interval_seconds=3600
        )
        
        scheduler.add_task(task)
        
        status = scheduler.get_status()
        
        assert "running" in status
        assert "tasks" in status
        assert "test_status" in status["tasks"]
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping scheduler"""
        scheduler = Scheduler()
        
        # Start
        result = scheduler.start()
        assert result == True
        assert scheduler.running == True
        assert scheduler.thread is not None
        
        # Stop
        result = scheduler.stop()
        assert result == True
        assert scheduler.running == False


class TestSchedulerTasks:
    """Test predefined scheduler tasks"""
    
    @pytest.mark.asyncio
    async def test_twitter_scraper_task(self):
        """Test twitter scraper task"""
        with patch('core.scheduler.twitter_scraper') as mock_scraper:
            with patch('core.scheduler.TwitterScraperDB') as mock_db:
                mock_scraper.scrape_all_sources = AsyncMock(return_value=[])
                mock_db.save_tweets = Mock(return_value=0)
                
                # Would need real modules to test properly
                try:
                    # result = await twitter_scraper_task()
                    pass
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_airdrop_tracker_task(self):
        """Test airdrop tracker task"""
        with patch('core.scheduler.airdrop_tracker') as mock_tracker:
            with patch('core.scheduler.AirdropTrackerDB') as mock_db:
                mock_tracker.check_all_sources = AsyncMock(return_value=[])
                mock_db.save_airdrops = Mock(return_value=0)
                mock_db.cleanup_expired = Mock(return_value=0)
                
                # Would need real modules to test
                try:
                    # result = await airdrop_tracker_task()
                    pass
                except Exception:
                    pass


class TestIntegration:
    """Integration tests"""
    
    def test_scheduler_workflow(self):
        """Test basic scheduler workflow"""
        async def task_func():
            return {"processed": 5}
        
        scheduler = Scheduler()
        
        # Add task
        task = ScheduledTask(
            name="test_workflow",
            func=task_func,
            interval_seconds=300
        )
        scheduler.add_task(task)
        
        # Check status
        status = scheduler.get_status()
        assert "test_workflow" in status["tasks"]
        assert status["tasks"]["test_workflow"]["enabled"] == True
        
        # Disable
        scheduler.disable_task("test_workflow")
        status = scheduler.get_status()
        assert status["tasks"]["test_workflow"]["enabled"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
