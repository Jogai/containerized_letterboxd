"""
Scheduler for periodic Letterboxd syncs.
Uses APScheduler to run syncs on a cron-like schedule.
"""

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scraper.sync import run_sync

logger = logging.getLogger(__name__)

# Configuration from environment
LETTERBOXD_USERNAME = os.environ.get("LETTERBOXD_USERNAME")
SYNC_SCHEDULE = os.environ.get("SYNC_SCHEDULE", "0 6 * * *")  # Default: daily at 6 AM
SYNC_MIN_DELAY = float(os.environ.get("SYNC_MIN_DELAY", "2.0"))  # Seconds between requests


def sync_job():
    """Run the sync job."""
    if not LETTERBOXD_USERNAME:
        logger.error("LETTERBOXD_USERNAME not set, skipping sync")
        return

    logger.info(f"Starting scheduled sync for: {LETTERBOXD_USERNAME}")
    try:
        stats = run_sync(LETTERBOXD_USERNAME, fetch_details=True, min_delay=SYNC_MIN_DELAY)
        logger.info(f"Sync completed: {stats}")
    except Exception as e:
        logger.error(f"Sync failed: {e}")


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the scheduler."""
    scheduler = BackgroundScheduler()

    if LETTERBOXD_USERNAME:
        # Parse cron schedule (minute hour day month day_of_week)
        parts = SYNC_SCHEDULE.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
            scheduler.add_job(sync_job, trigger, id="letterboxd_sync")
            logger.info(f"Scheduled sync for {LETTERBOXD_USERNAME} at: {SYNC_SCHEDULE}")
        else:
            logger.error(f"Invalid SYNC_SCHEDULE: {SYNC_SCHEDULE}")
    else:
        logger.warning("LETTERBOXD_USERNAME not set, scheduler disabled")

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run immediate sync for testing
    sync_job()
