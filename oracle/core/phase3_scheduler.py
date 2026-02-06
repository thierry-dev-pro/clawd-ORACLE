"""
ORACLE Phase 3: Notion Hourly Sync Scheduler
Integrated with existing Phase 2 scheduler
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Optional

from notion_sync import NotionSyncHandler

logger = logging.getLogger(__name__)

class Phase3Scheduler:
    """Manages Phase 3 Notion sync scheduling"""
    
    def __init__(self, existing_scheduler: Optional[BackgroundScheduler] = None):
        """
        Initialize Phase 3 scheduler
        
        Args:
            existing_scheduler: Existing APScheduler instance from Phase 2
        """
        self.scheduler = existing_scheduler or BackgroundScheduler()
        self.notion_sync = NotionSyncHandler()
        self.job_id = "notion_sync_hourly"
        self.is_running = False
    
    def sync_task(self) -> None:
        """Execute hourly Notion sync"""
        try:
            logger.info("Starting Phase 3 Notion sync...")
            stats = self.notion_sync.sync_all_handles()
            
            logger.info(f"Phase 3 sync result: {stats}")
            
            # Log to file for monitoring
            with open("logs/phase3_sync.log", "a") as f:
                f.write(f"[{datetime.utcnow().isoformat()}] {stats}\n")
            
        except Exception as e:
            logger.error(f"Phase 3 sync failed: {e}")
    
    def start(self) -> bool:
        """Start hourly sync"""
        try:
            if self.job_id in [job.id for job in self.scheduler.get_jobs()]:
                logger.warning("Phase 3 sync already scheduled")
                return False
            
            # Schedule for every hour at :00
            self.scheduler.add_job(
                self.sync_task,
                CronTrigger(minute=0),
                id=self.job_id,
                name="Phase 3 Notion Sync",
                replace_existing=True
            )
            
            self.is_running = True
            logger.info("Phase 3 Notion sync scheduled hourly")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Phase 3 sync: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop sync"""
        try:
            self.scheduler.remove_job(self.job_id)
            self.is_running = False
            logger.info("Phase 3 sync stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop Phase 3 sync: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get sync status"""
        jobs = {job.id: {
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else "Stopped",
            "trigger": str(job.trigger)
        } for job in self.scheduler.get_jobs() if job.id == self.job_id}
        
        return {
            "enabled": self.is_running,
            "job": jobs.get(self.job_id, {}),
            "last_sync": self._get_last_sync_time()
        }
    
    def _get_last_sync_time(self) -> Optional[str]:
        """Get timestamp of last successful sync"""
        try:
            with open("logs/phase3_sync.log", "r") as f:
                lines = f.readlines()
                if lines:
                    return lines[-1].split("] ")[0].replace("[", "")
        except FileNotFoundError:
            pass
        return None


def integrate_with_phase2(phase2_scheduler: BackgroundScheduler) -> Phase3Scheduler:
    """
    Integrate Phase 3 scheduler with Phase 2 scheduler
    
    Args:
        phase2_scheduler: Existing Phase 2 scheduler instance
    
    Returns:
        Phase3Scheduler instance
    """
    phase3 = Phase3Scheduler(phase2_scheduler)
    return phase3
