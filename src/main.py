"""
Main entrypoint that runs both the API server and the scheduler.
"""

import logging
import uvicorn

from src.api.main import app
from src.scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)

logger = logging.getLogger(__name__)


def main():
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)


if __name__ == "__main__":
    main()
