"""
Twitter Daily Job Scheduler - Run daily Twitter scans and push to Notion.
Uses APScheduler for reliable cron-like scheduling.
"""

import logging
from datetime import datetime
from typing import Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

from .twitter_daily_scanner import TwitterDailyScanner
from .twitter_notion_sync import TwitterNotionSync

logger = logging.getLogger(__name__)


class TwitterDailyJob:
    """Manage Twitter daily scanning job."""
    
    def __init__(
        self,
        camofox_url: str = "http://localhost:9377",
        proxy_list: Optional[List[str]] = None,
        notion_api_key: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        scan_time: str = "09:00"  # HH:MM UTC
    ):
        """
        Initialize daily job.
        
        Args:
            camofox_url: Camofox service URL
            proxy_list: Optional proxy list
            notion_api_key: Notion API key
            notion_database_id: Notion database ID
            scan_time: Time to run scan (HH:MM UTC)
        """
        self.scanner = TwitterDailyScanner(camofox_url, proxy_list)
        
        try:
            self.notion_sync = TwitterNotionSync(notion_api_key, notion_database_id)
        except ValueError:
            logger.warning("Notion credentials not configured - Notion sync disabled")
            self.notion_sync = None
        
        self.scan_time = scan_time
        self.scheduler: Optional[BackgroundScheduler] = None
        self.job: Optional[Job] = None
        self.last_run: Optional[datetime] = None
        self.last_result_count = 0
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.scheduler is not None:
            logger.warning("Scheduler already running")
            return
        
        self.scheduler = BackgroundScheduler()
        
        # Parse scan time (HH:MM)
        hour, minute = map(int, self.scan_time.split(":"))
        
        # Schedule daily job
        self.job = self.scheduler.add_job(
            self.run_scan,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="twitter_daily_scan",
            name="Twitter Daily Scan",
            misfire_grace_time=300,  # Allow 5 min grace period
            max_instances=1  # Only one instance at a time
        )
        
        self.scheduler.start()
        
        logger.info(
            f"Twitter daily job started (scan at {self.scan_time} UTC)"
        )
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler is None:
            return
        
        self.scheduler.shutdown(wait=False)
        self.scheduler = None
        self.job = None
        
        logger.info("Twitter daily job stopped")
    
    def run_scan(self) -> None:
        """Execute the daily scan."""
        logger.info("Starting Twitter daily scan...")
        
        try:
            # Scan Twitter
            results = self.scanner.scan_daily()
            
            # Get top results per category
            top_results = self.scanner.get_top_by_category(results, top_n=3)
            
            # Count results
            total = sum(len(r) for r in top_results.values())
            self.last_result_count = total
            
            logger.info(f"Scan found {total} top results")
            
            # Push to Notion
            if self.notion_sync:
                try:
                    stats = self.notion_sync.sync_batch(top_results)
                    logger.info(
                        f"Notion sync: {stats['created']} created, "
                        f"{stats['updated']} updated, {stats['failed']} failed"
                    )
                except Exception as e:
                    logger.error(f"Notion sync failed: {e}")
            else:
                logger.debug("Notion sync disabled")
            
            self.last_run = datetime.now()
            
            logger.info("Twitter daily scan completed successfully")
            
        except Exception as e:
            logger.error(f"Twitter daily scan failed: {e}", exc_info=True)
    
    def run_now(self) -> None:
        """Run scan immediately (for testing)."""
        logger.info("Running Twitter scan immediately...")
        
        if self.scheduler and self.scheduler.running:
            # Run as task
            self.scheduler.add_job(
                self.run_scan,
                id="twitter_scan_manual",
                replace_existing=True
            )
        else:
            # Run directly
            self.run_scan()
    
    def get_status(self) -> dict:
        """Get job status."""
        return {
            "running": self.scheduler is not None and self.scheduler.running,
            "scheduled_time": self.scan_time,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result_count": self.last_result_count,
            "notion_enabled": self.notion_sync is not None,
            "next_run": (
                self.job.next_run_time.isoformat() 
                if self.job and self.job.next_run_time 
                else None
            )
        }
    
    def get_jobs(self) -> List[dict]:
        """Get all scheduled jobs."""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return jobs


# Global instance for easy access
_global_job: Optional[TwitterDailyJob] = None


def get_twitter_job() -> TwitterDailyJob:
    """Get or create global Twitter job instance."""
    global _global_job
    
    if _global_job is None:
        _global_job = TwitterDailyJob()
    
    return _global_job


def start_twitter_job(scan_time: str = "09:00") -> TwitterDailyJob:
    """
    Start the global Twitter daily job.
    
    Args:
        scan_time: Time to run scan (HH:MM UTC)
        
    Returns:
        TwitterDailyJob instance
    """
    job = get_twitter_job()
    job.scan_time = scan_time
    job.start()
    return job


def stop_twitter_job() -> None:
    """Stop the global Twitter daily job."""
    job = get_twitter_job()
    job.stop()


# Example usage
def demo_daily_job():
    """Demo the daily job."""
    import time
    
    # Create job (scan at 09:00 UTC daily)
    job = TwitterDailyJob(scan_time="09:00")
    
    # Start scheduler
    job.start()
    
    # Show status
    print(f"Job status: {job.get_status()}")
    print(f"Scheduled jobs: {job.get_jobs()}")
    
    # Run immediately for testing
    print("\nRunning scan immediately...")
    job.run_now()
    
    # Keep running for a bit
    time.sleep(10)
    
    # Check status
    print(f"\nJob status: {job.get_status()}")
    
    # Stop
    job.stop()
