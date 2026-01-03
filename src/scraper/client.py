"""
Rate-limited Letterboxd scraper client.

Uses letterboxdpy with added rate limiting to be respectful to Letterboxd's servers.
Default: 1 request per 2 seconds (30 requests/minute).
"""

import time
import logging
from functools import wraps
from typing import Optional, Any
from datetime import datetime

from letterboxdpy.user import User
from letterboxdpy.movie import Movie

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter with configurable delay between requests."""

    def __init__(self, min_delay: float = 2.0):
        self.min_delay = min_delay
        self.last_request_time: Optional[float] = None

    def wait(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                sleep_time = self.min_delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self.last_request_time = time.time()


# Global rate limiter instance
_rate_limiter = RateLimiter(min_delay=2.0)


def rate_limited(func):
    """Decorator to add rate limiting to any function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        _rate_limiter.wait()
        return func(*args, **kwargs)
    return wrapper


class LetterboxdClient:
    """Rate-limited Letterboxd client wrapping letterboxdpy."""

    def __init__(self, min_delay: float = 2.0):
        """
        Initialize client with rate limiting.

        Args:
            min_delay: Minimum seconds between requests (default: 2.0)
        """
        self.rate_limiter = RateLimiter(min_delay=min_delay)

    def _wait(self):
        """Apply rate limiting before request."""
        self.rate_limiter.wait()

    def get_user(self, username: str) -> dict:
        """
        Get user profile data.

        Returns dict with keys like:
        - username, display_name, bio, location, website
        - favorites (list of film slugs)
        - stats (films, this_year, lists, following, followers)
        """
        self._wait()
        logger.info(f"Fetching user profile: {username}")

        user = User(username)
        return {
            "username": user.username,
            "display_name": getattr(user, "display_name", None),
            "bio": getattr(user, "bio", None),
            "location": getattr(user, "location", None),
            "website": getattr(user, "website", None),
            "favorites": getattr(user, "favorites", []),
            "stats": getattr(user, "stats", {}),
        }

    def get_user_films(self, username: str) -> list[dict]:
        """
        Get all films a user has logged (watched).

        Returns list of dicts with film info including user's rating.
        """
        self._wait()
        logger.info(f"Fetching watched films for: {username}")

        user = User(username)
        films_data = user.get_films()

        # films_data structure: {movies: {slug: {name, id, rating, year, liked}}, count, liked_count}
        result = []
        if isinstance(films_data, dict):
            movies = films_data.get("movies", {})
            if isinstance(movies, dict):
                for slug, data in movies.items():
                    if not isinstance(data, dict):
                        continue
                    # Rating is 0-10 in letterboxdpy, convert to 0.5-5 scale
                    raw_rating = data.get("rating")
                    rating = raw_rating / 2.0 if raw_rating else None
                    result.append({
                        "slug": slug,
                        "name": data.get("name"),
                        "year": data.get("year"),
                        "rating": rating,
                        "liked": data.get("liked", False),
                    })
        return result

    def get_user_diary(self, username: str, year: Optional[int] = None) -> list[dict]:
        """
        Get user's diary entries.

        Args:
            username: Letterboxd username
            year: Optional year to filter by

        Returns list of diary entry dicts.
        """
        self._wait()
        logger.info(f"Fetching diary for: {username}" + (f" (year={year})" if year else ""))

        user = User(username)

        if year:
            diary_data = user.get_diary(year=year)
        else:
            diary_data = user.get_diary()

        # Convert diary data to list
        # Structure: {'entries': {'entry_id': {'name': ..., 'slug': ..., 'actions': {...}, 'date': {...}}}}
        entries = []
        if isinstance(diary_data, dict):
            entries_dict = diary_data.get("entries", diary_data)
            for entry_id, data in entries_dict.items():
                if not isinstance(data, dict):
                    continue
                actions = data.get("actions", {})
                date_info = data.get("date", {})

                # Convert date dict to string
                date_str = None
                if isinstance(date_info, dict) and date_info.get("year"):
                    date_str = f"{date_info['year']}-{date_info.get('month', 1):02d}-{date_info.get('day', 1):02d}"

                # Rating is 0-10 in letterboxdpy, convert to 0.5-5 scale
                raw_rating = actions.get("rating")
                rating = raw_rating / 2.0 if raw_rating else None

                entries.append({
                    "id": entry_id,
                    "film_slug": data.get("slug"),
                    "film_name": data.get("name"),
                    "date": date_str,
                    "rating": rating,
                    "rewatch": actions.get("rewatched", False),
                    "liked": actions.get("liked", False),
                    "review": None,  # Reviews need separate fetch
                })
        return entries

    def get_user_watchlist(self, username: str) -> list[dict]:
        """
        Get user's watchlist.

        Returns list of film dicts on the watchlist.
        """
        self._wait()
        logger.info(f"Fetching watchlist for: {username}")

        user = User(username)
        # get_watchlist_movies() returns {film_id: {slug, name, year, url}}
        watchlist_data = user.get_watchlist_movies()

        result = []
        if isinstance(watchlist_data, dict):
            for film_id, data in watchlist_data.items():
                if not isinstance(data, dict):
                    continue
                result.append({
                    "slug": data.get("slug"),
                    "name": data.get("name"),
                    "year": data.get("year"),
                })
        return result

    def get_film(self, slug: str) -> dict:
        """
        Get detailed film information.

        Args:
            slug: Film slug (e.g., "the-godfather")

        Returns dict with full film details.
        """
        self._wait()
        logger.info(f"Fetching film details: {slug}")

        movie = Movie(slug)

        # Directors are in crew dict, not a direct attribute
        crew = getattr(movie, "crew", {}) or {}
        directors = crew.get("director", [])

        return {
            "slug": slug,
            "title": getattr(movie, "title", None),
            "year": getattr(movie, "year", None),
            "rating": getattr(movie, "rating", None),
            "runtime": getattr(movie, "runtime", None),
            "tagline": getattr(movie, "tagline", None),
            "description": getattr(movie, "description", None),
            "poster": getattr(movie, "poster", None),
            "genres": getattr(movie, "genres", []),
            "directors": directors,
            "cast": getattr(movie, "cast", []),
            "countries": getattr(movie, "countries", []),
            "languages": getattr(movie, "languages", []),
            "studios": getattr(movie, "studios", []),
            "url": getattr(movie, "url", None),
            "tmdb_id": getattr(movie, "tmdb_id", None),
            "imdb_id": getattr(movie, "imdb_id", None),
        }
