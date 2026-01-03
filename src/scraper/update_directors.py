"""
One-time script to update directors for existing films.
"""

import logging
import time

from letterboxdpy.movie import Movie
from src.db.database import SessionLocal, init_db
from src.db.models import Film

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def update_film_directors():
    """Update directors for all films missing director data."""
    init_db()
    db = SessionLocal()

    try:
        # Get films with empty directors
        films = db.query(Film).filter(
            (Film.directors_json == None) | (Film.directors_json == [])
        ).all()

        logger.info(f"Found {len(films)} films without director data")

        for i, film in enumerate(films):
            try:
                logger.info(f"[{i+1}/{len(films)}] Fetching directors for: {film.title}")
                time.sleep(2)  # Rate limit

                movie = Movie(film.slug)
                crew = getattr(movie, "crew", {}) or {}
                directors = crew.get("director", [])

                if directors:
                    film.directors_json = directors
                    db.commit()
                    logger.info(f"  -> {[d.get('name') for d in directors]}")
                else:
                    logger.info(f"  -> No directors found")

            except Exception as e:
                logger.error(f"  -> Error: {e}")

        logger.info("Done!")

    finally:
        db.close()


if __name__ == "__main__":
    update_film_directors()
