"""
Scheduler for periodic Letterboxd and TMDB syncs.
Uses APScheduler to run syncs on a cron-like schedule.

Flow:
1. Letterboxd sync runs on schedule (fetches films with tmdb_ids)
2. TMDB sync runs automatically after Letterboxd sync completes
   - Only if TMDB_API_KEY is configured
   - Only enriches films that don't already have TMDB data
"""

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scraper.sync import run_sync
from src.scraper.tmdb_sync import run_tmdb_sync

logger = logging.getLogger(__name__)

LETTERBOXD_USERNAME = os.environ.get("LETTERBOXD_USERNAME")
SYNC_SCHEDULE = os.environ.get("SYNC_SCHEDULE", "0 6 * * *")
SYNC_MIN_DELAY = float(os.environ.get("SYNC_MIN_DELAY", "4.0"))
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")


def sync_job():
    """Run the full sync: Letterboxd first, then TMDB enrichment."""
    if not LETTERBOXD_USERNAME:
        logger.error("LETTERBOXD_USERNAME not set, skipping sync")
        return

    logger.info(f"[1/2] Starting Letterboxd sync for: {LETTERBOXD_USERNAME}")
    try:
        stats = run_sync(LETTERBOXD_USERNAME, fetch_details=True, min_delay=SYNC_MIN_DELAY)
        logger.info(f"[1/2] Letterboxd sync completed: {stats}")
    except Exception as e:
        logger.error(f"[1/2] Letterboxd sync failed: {e}")
        return

    if not TMDB_API_KEY:
        logger.info("[2/2] TMDB_API_KEY not set, skipping TMDB enrichment")
        return

    logger.info("[2/2] Starting TMDB enrichment sync...")
    try:
        tmdb_stats = run_tmdb_sync()
        logger.info(f"[2/2] TMDB sync completed: {tmdb_stats['films_enriched']} enriched, {tmdb_stats['films_failed']} failed")
    except Exception as e:
        logger.error(f"[2/2] TMDB sync failed: {e}")


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the scheduler."""
    scheduler = BackgroundScheduler()

    if LETTERBOXD_USERNAME:
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

    sync_job()
