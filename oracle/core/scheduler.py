"""
Scheduler Module - Background tasks pour scrapers et trackers
Gère Twitter Scraper et Airdrop Tracker avec rate limiting
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable
import threading
import time
from sqlalchemy.orm import Session
from core.database import SessionLocal

logger = logging.getLogger(__name__)


class ScheduledTask:
    """Représentation d'une tâche planifiée"""
    
    def __init__(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        enabled: bool = True
    ):
        """
        Initialize task
        
        Args:
            name: Task name
            func: Async function to execute
            interval_seconds: Interval between executions
            enabled: Whether task is enabled
        """
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.last_run = None
        self.next_run = datetime.utcnow() + timedelta(seconds=10)
        self.run_count = 0
        self.error_count = 0
        self.last_error = None
    
    async def run(self):
        """Execute task"""
        try:
            logger.info(f"⏱️ Running task: {self.name}")
            start = time.time()
            
            # Run async function
            result = await self.func()
            
            duration = time.time() - start
            self.run_count += 1
            self.last_run = datetime.utcnow()
            self.next_run = self.last_run + timedelta(seconds=self.interval_seconds)
            
            logger.info(
                f"✅ Task completed: {self.name} ({duration:.2f}s)",
                run_count=self.run_count
            )
            return result
        
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"❌ Task failed: {self.name}: {e}")
            # Reschedule pour retry
            self.next_run = datetime.utcnow() + timedelta(seconds=300)  # Retry in 5 min
            raise
    
    def should_run(self) -> bool:
        """Check if task should run"""
        if not self.enabled:
            return False
        
        if self.next_run is None:
            return True
        
        return datetime.utcnow() >= self.next_run


class Scheduler:
    """Gestionnaire de tâches planifiées"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.tasks = {}
        self.running = False
        self.thread = None
        self.loop = None
        logger.info("✅ Scheduler initialized")
    
    def add_task(self, task: ScheduledTask) -> bool:
        """
        Add task to scheduler
        
        Args:
            task: Task to add
        
        Returns:
            Success status
        """
        try:
            if task.name in self.tasks:
                logger.warning(f"Task {task.name} already registered, replacing...")
            
            self.tasks[task.name] = task
            logger.info(f"✅ Task registered: {task.name} (interval: {task.interval_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Error registering task: {e}")
            return False
    
    def remove_task(self, task_name: str) -> bool:
        """
        Remove task from scheduler
        
        Args:
            task_name: Task name
        
        Returns:
            Success status
        """
        try:
            if task_name in self.tasks:
                del self.tasks[task_name]
                logger.info(f"✅ Task removed: {task_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error removing task: {e}")
            return False
    
    def enable_task(self, task_name: str) -> bool:
        """Enable task"""
        if task_name in self.tasks:
            self.tasks[task_name].enabled = True
            logger.info(f"✅ Task enabled: {task_name}")
            return True
        return False
    
    def disable_task(self, task_name: str) -> bool:
        """Disable task"""
        if task_name in self.tasks:
            self.tasks[task_name].enabled = False
            logger.info(f"✅ Task disabled: {task_name}")
            return True
        return False
    
    async def _run_loop(self):
        """Main scheduler loop"""
        logger.info("🚀 Scheduler loop started")
        
        while self.running:
            try:
                now = datetime.utcnow()
                
                # Check each task
                for task_name, task in self.tasks.items():
                    if task.should_run():
                        try:
                            await task.run()
                        except Exception as e:
                            logger.error(f"Task error: {task_name}: {e}")
                
                # Sleep brief period before next check
                await asyncio.sleep(30)
            
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
        
        logger.info("🛑 Scheduler loop stopped")
    
    def start(self) -> bool:
        """
        Start scheduler
        
        Returns:
            Success status
        """
        try:
            if self.running:
                logger.warning("Scheduler already running")
                return False
            
            self.running = True
            
            # Create async loop in background thread
            def run_async_loop():
                try:
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                    self.loop.run_until_complete(self._run_loop())
                except Exception as e:
                    logger.error(f"Error in async loop: {e}")
                finally:
                    if self.loop:
                        self.loop.close()
            
            self.thread = threading.Thread(target=run_async_loop, daemon=True)
            self.thread.start()
            
            logger.info("✅ Scheduler started")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
            self.running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop scheduler
        
        Returns:
            Success status
        """
        try:
            self.running = False
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            logger.info("✅ Scheduler stopped")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
            return False
    
    def get_status(self) -> dict:
        """
        Get scheduler status
        
        Returns:
            Status dict
        """
        return {
            "running": self.running,
            "tasks": {
                name: {
                    "enabled": task.enabled,
                    "interval": task.interval_seconds,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "run_count": task.run_count,
                    "error_count": task.error_count,
                    "last_error": task.last_error
                }
                for name, task in self.tasks.items()
            }
        }


# Task definitions
async def twitter_scraper_task():
    """
    Twitter scraper task
    Runs: Every 1 hour (max 10 tweets/hour)
    """
    try:
        from core.twitter_scraper import twitter_scraper, TwitterScraperDB
        
        logger.info("📱 Starting Twitter scraper task")
        
        # Scrape tweets
        tweets = await twitter_scraper.scrape_all_sources()
        
        if not tweets:
            logger.warning("No tweets scraped")
            return {"tweets_found": 0}
        
        # Save to DB
        db = SessionLocal()
        try:
            count = TwitterScraperDB.save_tweets(db, tweets)
            return {"tweets_found": len(tweets), "tweets_saved": count}
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Twitter scraper task failed: {e}")
        raise


async def airdrop_tracker_task():
    """
    Airdrop tracker task
    Runs: Every 8 hours (max 3 checks/day)
    """
    try:
        from core.airdrop_tracker import airdrop_tracker, AirdropTrackerDB
        
        logger.info("🎁 Starting airdrop tracker task")
        
        # Check airdrops
        airdrops = await airdrop_tracker.check_all_sources()
        
        if not airdrops:
            logger.warning("No airdrops found")
            return {"airdrops_found": 0}
        
        # Save to DB
        db = SessionLocal()
        try:
            count = AirdropTrackerDB.save_airdrops(db, airdrops)
            AirdropTrackerDB.cleanup_expired(db)
            return {"airdrops_found": len(airdrops), "airdrops_saved": count}
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Airdrop tracker task failed: {e}")
        raise


async def cleanup_task():
    """
    Cleanup task
    Runs: Daily at 2 AM
    """
    try:
        from core.twitter_scraper import TwitterScraperDB
        from core.airdrop_tracker import AirdropTrackerDB
        
        logger.info("🧹 Starting cleanup task")
        
        db = SessionLocal()
        try:
            # Cleanup old tweets (older than 7 days)
            deleted_tweets = TwitterScraperDB.cleanup_old_tweets(db, days=7)
            
            # Cleanup expired airdrops
            expired_airdrops = AirdropTrackerDB.cleanup_expired(db)
            
            return {
                "tweets_deleted": deleted_tweets,
                "airdrops_expired": expired_airdrops
            }
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Cleanup task failed: {e}")
        raise


# Global scheduler instance
scheduler = Scheduler()


def initialize_scheduler():
    """
    Initialize and start scheduler with default tasks
    Called from main.py startup
    """
    try:
        # Add Twitter scraper task (every 1 hour)
        scraper_task = ScheduledTask(
            name="twitter_scraper",
            func=twitter_scraper_task,
            interval_seconds=3600,  # 1 hour
            enabled=True
        )
        scheduler.add_task(scraper_task)
        
        # Add airdrop tracker task (every 8 hours)
        tracker_task = ScheduledTask(
            name="airdrop_tracker",
            func=airdrop_tracker_task,
            interval_seconds=28800,  # 8 hours
            enabled=True
        )
        scheduler.add_task(tracker_task)
        
        # Add cleanup task (every 24 hours)
        cleanup = ScheduledTask(
            name="cleanup_task",
            func=cleanup_task,
            interval_seconds=86400,  # 24 hours
            enabled=True
        )
        scheduler.add_task(cleanup)
        
        # Start scheduler
        scheduler.start()
        
        logger.info("✅ Scheduler initialized with default tasks")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error initializing scheduler: {e}")
        return False
