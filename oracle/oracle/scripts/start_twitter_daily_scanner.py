#!/usr/bin/env python3
"""
Start Twitter Daily Scanner with all components.
Scan → Categorize → Rank → Notion → Telegram (optional).
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from oracle.core.twitter_daily_job import TwitterDailyJob
from oracle.core.twitter_telegram_alerts import TwitterTelegramAlerts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_scanner.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start Twitter Daily Scanner"
    )
    parser.add_argument(
        '--time',
        default='09:00',
        help='Scan time in HH:MM UTC format (default: 09:00)'
    )
    parser.add_argument(
        '--run-now',
        action='store_true',
        help='Run scan immediately (for testing)'
    )
    parser.add_argument(
        '--telegram',
        action='store_true',
        help='Enable Telegram alerts (optional)'
    )
    parser.add_argument(
        '--no-notion',
        action='store_true',
        help='Disable Notion sync'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate time format
    try:
        hour, minute = map(int, args.time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Hour must be 0-23, minute 0-59")
    except ValueError as e:
        logger.error(f"Invalid time format: {e}")
        return 1
    
    logger.info("=" * 60)
    logger.info("Twitter Daily Scanner Starting")
    logger.info("=" * 60)
    
    # Check Notion credentials
    notion_enabled = not args.no_notion
    if notion_enabled:
        if not os.getenv("NOTION_API_KEY") or not os.getenv("NOTION_DATABASE_ID"):
            logger.warning(
                "NOTION_API_KEY and NOTION_DATABASE_ID not set - "
                "Notion sync disabled. Set environment variables to enable."
            )
            notion_enabled = False
    
    # Create job
    logger.info(f"Creating job (scan time: {args.time} UTC)")
    
    job = TwitterDailyJob(
        camofox_url=os.getenv("CAMOFOX_URL", "http://localhost:9377"),
        proxy_list=None,  # Add proxy list if needed
        notion_api_key=os.getenv("NOTION_API_KEY") if notion_enabled else None,
        notion_database_id=os.getenv("NOTION_DATABASE_ID") if notion_enabled else None,
        scan_time=args.time
    )
    
    # Setup Telegram alerts if requested
    if args.telegram:
        logger.info("Telegram alerts enabled (optional)")
        
        # Try to import telegram bot
        try:
            from oracle.core.telegram_bot import TelegramBot
            
            telegram_bot = TelegramBot()
            alerts = TwitterTelegramAlerts(telegram_bot)
            
            logger.info("Telegram bot initialized")
        except ImportError:
            logger.warning("TelegramBot not available - Telegram alerts disabled")
            args.telegram = False
    
    # Start job
    logger.info("Starting scheduler...")
    job.start()
    
    # Show status
    status = job.get_status()
    logger.info(f"Job status: {status}")
    logger.info(f"Next run: {status['next_run']}")
    
    # Run immediately if requested
    if args.run_now:
        logger.info("Running scan immediately (testing mode)...")
        job.run_now()
        
        status = job.get_status()
        logger.info(f"Last run: {status['last_run']}")
        logger.info(f"Results: {status['last_result_count']}")
        
        if not args.telegram:
            # Let test run complete then exit
            logger.info("Test run complete. Exiting.")
            job.stop()
            return 0
    
    # Keep running
    logger.info("Scanner running (press Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(60)
            
            # Log periodic status
            status = job.get_status()
            if status['running']:
                logger.debug(f"Next run: {status['next_run']}")
    
    except KeyboardInterrupt:
        logger.info("Stopping scanner...")
        job.stop()
        logger.info("Scanner stopped.")
        return 0
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        job.stop()
        return 1


if __name__ == "__main__":
    sys.exit(main())
