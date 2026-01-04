"""
Sync TMDB enrichment data for films in the database.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.database import SessionLocal, init_db
from src.db.models import Film, TmdbFilm, SyncLog
from src.scraper.tmdb_client import TmdbClient

logger = logging.getLogger(__name__)


class TmdbSync:
    """Sync TMDB enrichment data for films."""

    def __init__(self, api_key: Optional[str] = None, min_delay: float = 0.3):
        """
        Initialize TMDB sync.

        Args:
            api_key: TMDB API key (or set TMDB_API_KEY env var)
            min_delay: Seconds between API requests (default: 0.3)
        """
        self.client = TmdbClient(api_key=api_key, min_delay=min_delay)

    def sync_all(self, db: Session, limit: Optional[int] = None, force: bool = False) -> dict:
        """
        Sync TMDB data for all films that have a tmdb_id.

        Args:
            db: Database session
            limit: Max number of films to process (None = all)
            force: Re-fetch even if TmdbFilm record exists

        Returns:
            Dict with sync statistics
        """
        sync_log = SyncLog(
            sync_type="tmdb",
            username="system",  # TMDB sync is system-level, not user-specific
            started_at=datetime.utcnow(),
            status="running"
        )
        db.add(sync_log)
        db.commit()

        stats = {
            "total_films": 0,
            "films_to_enrich": 0,
            "films_enriched": 0,
            "films_skipped": 0,
            "films_failed": 0,
            "errors": []
        }

        try:
            # Count total films with tmdb_id
            stats["total_films"] = db.query(Film).filter(Film.tmdb_id.isnot(None)).count()

            # Get films that need enrichment
            if force:
                # Re-fetch all films with tmdb_id
                query = db.query(Film).filter(Film.tmdb_id.isnot(None))
            else:
                # Only films without TmdbFilm record
                query = db.query(Film).outerjoin(TmdbFilm).filter(
                    and_(
                        Film.tmdb_id.isnot(None),
                        TmdbFilm.id.is_(None)
                    )
                )

            if limit:
                query = query.limit(limit)

            films = query.all()
            stats["films_to_enrich"] = len(films)

            logger.info(f"TMDB sync: {stats['films_to_enrich']} films to enrich (total with tmdb_id: {stats['total_films']})")

            for i, film in enumerate(films):
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{stats['films_to_enrich']} films processed")
                    db.commit()  # Commit periodically

                result = self._enrich_film(db, film, force)
                if result == "enriched":
                    stats["films_enriched"] += 1
                elif result == "skipped":
                    stats["films_skipped"] += 1
                elif result == "failed":
                    stats["films_failed"] += 1

            sync_log.status = "completed" if stats["films_failed"] == 0 else "completed_with_errors"
            sync_log.completed_at = datetime.utcnow()
            sync_log.items_processed = stats["films_enriched"]

        except Exception as e:
            logger.error(f"TMDB sync failed: {e}")
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            stats["errors"].append(str(e))

        db.commit()

        logger.info(f"TMDB sync complete: {stats['films_enriched']} enriched, {stats['films_failed']} failed")
        return stats

    def _enrich_film(self, db: Session, film: Film, force: bool = False) -> str:
        """
        Enrich a single film with TMDB data.

        Returns:
            "enriched", "skipped", or "failed"
        """
        if not film.tmdb_id:
            logger.debug(f"Skipping {film.slug}: no tmdb_id")
            return "skipped"

        # Check if already enriched
        existing = db.query(TmdbFilm).filter(TmdbFilm.film_id == film.id).first()
        if existing and not force:
            logger.debug(f"Skipping {film.slug}: already enriched")
            return "skipped"

        try:
            tmdb_id = int(film.tmdb_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid tmdb_id for film {film.slug}: {film.tmdb_id}")
            return "failed"

        try:
            data = self.client.get_movie(tmdb_id)
        except Exception as e:
            logger.error(f"Failed to fetch TMDB data for {film.slug} (tmdb_id={tmdb_id}): {type(e).__name__}: {e}")
            return "failed"

        if not data:
            logger.warning(f"No TMDB data found for {film.slug} (tmdb_id={tmdb_id})")
            return "failed"

        try:
            if existing:
                # Update existing record
                tmdb_film = existing
            else:
                # Create new record
                tmdb_film = TmdbFilm(film_id=film.id)
                db.add(tmdb_film)

            # Update all fields
            tmdb_film.tmdb_id = data.get("tmdb_id")
            tmdb_film.budget = data.get("budget")
            tmdb_film.revenue = data.get("revenue")
            tmdb_film.vote_average = data.get("vote_average")
            tmdb_film.vote_count = data.get("vote_count")
            tmdb_film.popularity = data.get("popularity")
            tmdb_film.certification = data.get("certification")
            tmdb_film.certifications_json = data.get("certifications_json")
            tmdb_film.adult = data.get("adult", False)
            tmdb_film.status = data.get("status")
            tmdb_film.release_date = data.get("release_date")
            tmdb_film.homepage = data.get("homepage")
            tmdb_film.origin_country_json = data.get("origin_country_json")
            tmdb_film.collection_id = data.get("collection_id")
            tmdb_film.collection_name = data.get("collection_name")
            tmdb_film.collection_poster_path = data.get("collection_poster_path")
            tmdb_film.keywords_json = data.get("keywords_json")
            tmdb_film.watch_providers_json = data.get("watch_providers_json")
            tmdb_film.similar_json = data.get("similar_json")
            tmdb_film.recommendations_json = data.get("recommendations_json")
            tmdb_film.imdb_id = data.get("imdb_id")
            tmdb_film.wikidata_id = data.get("wikidata_id")
            tmdb_film.facebook_id = data.get("facebook_id")
            tmdb_film.instagram_id = data.get("instagram_id")
            tmdb_film.twitter_id = data.get("twitter_id")
            tmdb_film.videos_json = data.get("videos_json")
            tmdb_film.cast_json = data.get("cast_json")
            tmdb_film.crew_json = data.get("crew_json")
            tmdb_film.production_companies_json = data.get("production_companies_json")
            tmdb_film.last_synced_at = datetime.utcnow()
            tmdb_film.updated_at = datetime.utcnow()

            logger.debug(f"Enriched {film.slug} (tmdb_id={tmdb_id})")
            return "enriched"

        except Exception as e:
            logger.error(f"Failed to save TMDB data for {film.slug}: {type(e).__name__}: {e}")
            return "failed"

    def enrich_single(self, db: Session, film_id: int, force: bool = False) -> dict:
        """
        Enrich a single film by its database ID.

        Args:
            db: Database session
            film_id: Film ID
            force: Re-fetch even if TmdbFilm record exists

        Returns:
            Dict with result info
        """
        film = db.query(Film).filter(Film.id == film_id).first()
        if not film:
            return {"status": "error", "message": "Film not found"}

        if not film.tmdb_id:
            return {"status": "error", "message": "Film has no tmdb_id"}

        result = self._enrich_film(db, film, force)
        db.commit()

        return {
            "status": result,
            "film_id": film_id,
            "film_slug": film.slug,
            "tmdb_id": film.tmdb_id
        }

    def get_enrichment_status(self, db: Session) -> dict:
        """
        Get status of TMDB enrichment.

        Returns:
            Dict with counts and percentages
        """
        total_films = db.query(Film).count()
        films_with_tmdb_id = db.query(Film).filter(Film.tmdb_id.isnot(None)).count()
        films_enriched = db.query(TmdbFilm).count()

        films_pending = films_with_tmdb_id - films_enriched
        films_without_tmdb_id = total_films - films_with_tmdb_id

        return {
            "total_films": total_films,
            "films_with_tmdb_id": films_with_tmdb_id,
            "films_enriched": films_enriched,
            "films_pending": films_pending,
            "films_without_tmdb_id": films_without_tmdb_id,
            "enrichment_percentage": round(films_enriched / films_with_tmdb_id * 100, 1) if films_with_tmdb_id > 0 else 0,
        }


def run_tmdb_sync(
    limit: Optional[int] = None,
    force: bool = False,
    api_key: Optional[str] = None,
    min_delay: float = 0.3
) -> dict:
    """
    Run TMDB enrichment sync.

    Args:
        limit: Max number of films to process
        force: Re-fetch even if already enriched
        api_key: TMDB API key
        min_delay: Seconds between requests

    Returns:
        Sync statistics dict
    """
    init_db()
    db = SessionLocal()

    try:
        sync = TmdbSync(api_key=api_key, min_delay=min_delay)
        return sync.sync_all(db, limit=limit, force=force)
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Sync TMDB enrichment data")
    parser.add_argument("--limit", type=int, help="Max films to process")
    parser.add_argument("--force", action="store_true", help="Re-fetch existing data")
    parser.add_argument("--status", action="store_true", help="Show enrichment status only")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    try:
        sync = TmdbSync()

        if args.status:
            status = sync.get_enrichment_status(db)
            print("\nTMDB Enrichment Status:")
            print(f"  Total films: {status['total_films']}")
            print(f"  With TMDB ID: {status['films_with_tmdb_id']}")
            print(f"  Enriched: {status['films_enriched']} ({status['enrichment_percentage']}%)")
            print(f"  Pending: {status['films_pending']}")
            print(f"  No TMDB ID: {status['films_without_tmdb_id']}")
        else:
            print("Starting TMDB sync...")
            stats = sync.sync_all(db, limit=args.limit, force=args.force)
            print(f"\nSync completed:")
            print(f"  Total films: {stats['total_films']}")
            print(f"  Films to enrich: {stats['films_to_enrich']}")
            print(f"  Enriched: {stats['films_enriched']}")
            print(f"  Skipped: {stats['films_skipped']}")
            print(f"  Failed: {stats['films_failed']}")
            if stats['errors']:
                print(f"  Errors: {stats['errors']}")
    finally:
        db.close()
