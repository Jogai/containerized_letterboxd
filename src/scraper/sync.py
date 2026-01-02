"""
Sync Letterboxd data to local SQLite database.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.db.database import SessionLocal, init_db
from src.db.models import User, Film, DiaryEntry, WatchlistItem, SyncLog
from src.scraper.client import LetterboxdClient

logger = logging.getLogger(__name__)


class LetterboxdSync:
    """Sync Letterboxd data to database."""

    def __init__(self, username: str, min_delay: float = 2.0):
        """
        Initialize sync for a user.

        Args:
            username: Letterboxd username to sync
            min_delay: Seconds between API requests (default: 2.0)
        """
        self.username = username
        self.client = LetterboxdClient(min_delay=min_delay)

    def sync_all(self, db: Session, fetch_film_details: bool = True) -> dict:
        """
        Full sync: user profile, diary, watchlist, and optionally film details.

        Args:
            db: Database session
            fetch_film_details: Whether to fetch full details for each film

        Returns:
            Dict with sync statistics
        """
        sync_log = SyncLog(
            sync_type="full",
            username=self.username,
            started_at=datetime.utcnow(),
            status="running"
        )
        db.add(sync_log)
        db.commit()

        stats = {
            "user_synced": False,
            "diary_entries": 0,
            "watchlist_items": 0,
            "films_synced": 0,
            "errors": []
        }

        try:
            # Sync user profile
            logger.info(f"Syncing user profile: {self.username}")
            user = self._sync_user(db)
            stats["user_synced"] = True

            # Sync diary (watched films)
            logger.info(f"Syncing diary for: {self.username}")
            diary_count = self._sync_diary(db, user, fetch_film_details)
            stats["diary_entries"] = diary_count

            # Sync watchlist
            logger.info(f"Syncing watchlist for: {self.username}")
            watchlist_count = self._sync_watchlist(db, user, fetch_film_details)
            stats["watchlist_items"] = watchlist_count

            # Count films
            stats["films_synced"] = db.query(Film).count()

            sync_log.status = "completed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.items_processed = diary_count + watchlist_count

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            stats["errors"].append(str(e))

        db.commit()
        return stats

    def _sync_user(self, db: Session) -> User:
        """Sync user profile."""
        user_data = self.client.get_user(self.username)

        user = db.query(User).filter(User.username == self.username).first()
        if not user:
            user = User(username=self.username)
            db.add(user)

        user.display_name = user_data.get("display_name")
        user.bio = user_data.get("bio")
        user.location = user_data.get("location")
        user.website = user_data.get("website")
        user.favorites_json = user_data.get("favorites")
        user.stats_json = user_data.get("stats")
        user.updated_at = datetime.utcnow()

        db.commit()
        return user

    def _sync_diary(self, db: Session, user: User, fetch_details: bool) -> int:
        """Sync user's diary entries."""
        diary_entries = self.client.get_user_diary(self.username)
        count = 0

        for entry_data in diary_entries:
            entry_id = entry_data.get("id")
            film_slug = entry_data.get("film_slug")

            if not film_slug:
                continue

            # Get or create film
            film = self._get_or_create_film(db, film_slug, fetch_details)
            if not film:
                continue

            # Check if entry already exists
            existing = db.query(DiaryEntry).filter(
                DiaryEntry.letterboxd_id == entry_id
            ).first()

            if existing:
                # Update existing entry
                existing.rating = entry_data.get("rating")
                existing.rewatch = entry_data.get("rewatch", False)
                existing.liked = entry_data.get("liked", False)
                existing.review_text = entry_data.get("review")
                existing.updated_at = datetime.utcnow()
            else:
                # Create new entry
                watched_date = None
                if entry_data.get("date"):
                    try:
                        watched_date = datetime.strptime(entry_data["date"], "%Y-%m-%d")
                    except (ValueError, TypeError):
                        pass

                entry = DiaryEntry(
                    user_id=user.id,
                    film_id=film.id,
                    letterboxd_id=entry_id,
                    watched_date=watched_date,
                    rating=entry_data.get("rating"),
                    rewatch=entry_data.get("rewatch", False),
                    liked=entry_data.get("liked", False),
                    review_text=entry_data.get("review"),
                )
                db.add(entry)
                count += 1

        db.commit()
        return count

    def _sync_watchlist(self, db: Session, user: User, fetch_details: bool) -> int:
        """Sync user's watchlist."""
        watchlist = self.client.get_user_watchlist(self.username)
        count = 0

        # Get existing watchlist film IDs
        existing_film_ids = {
            w.film_id for w in db.query(WatchlistItem).filter(
                WatchlistItem.user_id == user.id
            ).all()
        }

        for item_data in watchlist:
            film_slug = item_data.get("slug")
            if not film_slug:
                continue

            film = self._get_or_create_film(db, film_slug, fetch_details)
            if not film:
                continue

            if film.id not in existing_film_ids:
                watchlist_item = WatchlistItem(
                    user_id=user.id,
                    film_id=film.id,
                )
                db.add(watchlist_item)
                count += 1

        db.commit()
        return count

    def _get_or_create_film(
        self, db: Session, slug: str, fetch_details: bool
    ) -> Optional[Film]:
        """Get existing film or create new one."""
        film = db.query(Film).filter(Film.slug == slug).first()

        if film:
            return film

        # Create new film
        film = Film(slug=slug)

        if fetch_details:
            try:
                details = self.client.get_film(slug)
                film.title = details.get("title") or slug
                film.year = details.get("year")
                film.rating = details.get("rating")
                film.runtime_minutes = details.get("runtime")
                film.tagline = details.get("tagline")
                film.description = details.get("description")
                film.poster_url = details.get("poster")
                film.genres_json = details.get("genres")
                film.directors_json = details.get("directors")
                film.cast_json = details.get("cast")
                film.countries_json = details.get("countries")
                film.languages_json = details.get("languages")
                film.studios_json = details.get("studios")
                film.letterboxd_url = details.get("url")
                film.tmdb_id = details.get("tmdb_id")
                film.imdb_id = details.get("imdb_id")
            except Exception as e:
                logger.warning(f"Failed to fetch details for {slug}: {e}")
                film.title = slug
        else:
            film.title = slug

        db.add(film)
        db.commit()
        return film


def run_sync(username: str, fetch_details: bool = True, min_delay: float = 2.0) -> dict:
    """
    Run a full sync for a user.

    Args:
        username: Letterboxd username
        fetch_details: Whether to fetch full film details
        min_delay: Seconds between requests

    Returns:
        Sync statistics dict
    """
    init_db()
    db = SessionLocal()

    try:
        sync = LetterboxdSync(username, min_delay=min_delay)
        return sync.sync_all(db, fetch_film_details=fetch_details)
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) < 2:
        print("Usage: python -m src.scraper.sync <username>")
        sys.exit(1)

    username = sys.argv[1]
    print(f"Starting sync for user: {username}")

    stats = run_sync(username)
    print(f"\nSync completed:")
    print(f"  Diary entries: {stats['diary_entries']}")
    print(f"  Watchlist items: {stats['watchlist_items']}")
    print(f"  Films in database: {stats['films_synced']}")

    if stats['errors']:
        print(f"  Errors: {stats['errors']}")
