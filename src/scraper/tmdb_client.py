"""
TMDB API client with rate limiting.

Rate limit: 40 requests per 10 seconds (TMDB's limit).
We use a conservative 0.3s delay between requests.
"""

import os
import time
import logging
from typing import Optional, Any
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


class TmdbRateLimiter:
    """Rate limiter for TMDB API (40 requests per 10 seconds)."""

    def __init__(self, min_delay: float = 0.3):
        self.min_delay = min_delay
        self.last_request_time: Optional[float] = None

    def wait(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                sleep_time = self.min_delay - elapsed
                time.sleep(sleep_time)
        self.last_request_time = time.time()


class TmdbClient:
    """TMDB API client for fetching movie enrichment data."""

    def __init__(self, api_key: Optional[str] = None, min_delay: float = 0.3):
        """
        Initialize TMDB client.

        Args:
            api_key: TMDB API key. If not provided, reads from TMDB_API_KEY env var.
            min_delay: Minimum seconds between requests (default: 0.3)
        """
        self.api_key = api_key or os.environ.get("TMDB_API_KEY")
        if not self.api_key:
            raise ValueError("TMDB API key required. Set TMDB_API_KEY env var or pass api_key.")

        self.rate_limiter = TmdbRateLimiter(min_delay=min_delay)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make a rate-limited request to TMDB API."""
        self.rate_limiter.wait()

        url = f"{TMDB_API_BASE}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"TMDB resource not found: {endpoint}")
                return None
            logger.error(f"TMDB API error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB request failed: {e}")
            raise

    def get_movie(self, tmdb_id: int, country: str = "US") -> Optional[dict]:
        """
        Fetch complete movie data from TMDB with all append_to_response fields.

        Args:
            tmdb_id: TMDB movie ID
            country: Country code for watch providers and certifications (default: US)

        Returns:
            Parsed movie data dict or None if not found
        """
        logger.info(f"Fetching TMDB movie: {tmdb_id}")

        # Fetch everything in one request using append_to_response
        data = self._request(
            f"/movie/{tmdb_id}",
            params={
                "append_to_response": "credits,keywords,release_dates,external_ids,watch/providers,similar,recommendations,videos",
                "language": "en-US",
            }
        )

        if not data:
            return None

        return self._parse_movie_response(data, country)

    def _parse_movie_response(self, data: dict, country: str = "US") -> dict:
        """Parse TMDB movie response into our schema."""

        # Extract US certification from release_dates
        certification = None
        certifications_all = {}
        release_dates = data.get("release_dates", {}).get("results", [])
        for rd in release_dates:
            iso = rd.get("iso_3166_1")
            releases = rd.get("release_dates", [])
            for release in releases:
                cert = release.get("certification")
                if cert:
                    certifications_all[iso] = cert
                    if iso == country:
                        certification = cert
                    break  # Take first non-empty certification per country

        # Extract watch providers for specified country
        watch_providers = data.get("watch/providers", {}).get("results", {})
        watch_providers_parsed = {}
        for iso, providers in watch_providers.items():
            watch_providers_parsed[iso] = {
                "link": providers.get("link"),
                "flatrate": [
                    {"id": p.get("provider_id"), "name": p.get("provider_name"), "logo": p.get("logo_path")}
                    for p in providers.get("flatrate", [])
                ],
                "rent": [
                    {"id": p.get("provider_id"), "name": p.get("provider_name"), "logo": p.get("logo_path")}
                    for p in providers.get("rent", [])
                ],
                "buy": [
                    {"id": p.get("provider_id"), "name": p.get("provider_name"), "logo": p.get("logo_path")}
                    for p in providers.get("buy", [])
                ],
            }

        # Extract external IDs
        external_ids = data.get("external_ids", {})

        # Extract keywords
        keywords = [
            {"id": kw.get("id"), "name": kw.get("name")}
            for kw in data.get("keywords", {}).get("keywords", [])
        ]

        # Extract credits
        credits = data.get("credits", {})
        cast = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "character": c.get("character"),
                "order": c.get("order"),
                "profile_path": c.get("profile_path"),
            }
            for c in credits.get("cast", [])
        ]
        crew = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "job": c.get("job"),
                "department": c.get("department"),
                "profile_path": c.get("profile_path"),
            }
            for c in credits.get("crew", [])
        ]

        # Extract videos (trailers, teasers, etc.)
        videos = [
            {
                "id": v.get("id"),
                "key": v.get("key"),
                "name": v.get("name"),
                "site": v.get("site"),
                "type": v.get("type"),
                "official": v.get("official"),
            }
            for v in data.get("videos", {}).get("results", [])
        ]

        # Extract similar and recommendations (just IDs and basic info)
        similar = [
            {"id": m.get("id"), "title": m.get("title"), "poster_path": m.get("poster_path")}
            for m in data.get("similar", {}).get("results", [])
        ]
        recommendations = [
            {"id": m.get("id"), "title": m.get("title"), "poster_path": m.get("poster_path")}
            for m in data.get("recommendations", {}).get("results", [])
        ]

        # Extract production companies
        production_companies = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "logo_path": c.get("logo_path"),
                "origin_country": c.get("origin_country"),
            }
            for c in data.get("production_companies", [])
        ]

        # Extract collection info
        collection = data.get("belongs_to_collection")
        collection_id = collection.get("id") if collection else None
        collection_name = collection.get("name") if collection else None
        collection_poster_path = collection.get("poster_path") if collection else None

        return {
            "tmdb_id": data.get("id"),

            # Financial
            "budget": data.get("budget") or None,  # Convert 0 to None
            "revenue": data.get("revenue") or None,

            # Ratings
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "popularity": data.get("popularity"),

            # Classification
            "certification": certification,
            "certifications_json": certifications_all if certifications_all else None,
            "adult": data.get("adult", False),

            # Metadata
            "status": data.get("status"),
            "release_date": data.get("release_date"),
            "homepage": data.get("homepage") or None,
            "origin_country_json": data.get("origin_country") or None,

            # Collection
            "collection_id": collection_id,
            "collection_name": collection_name,
            "collection_poster_path": collection_poster_path,

            # Thematic
            "keywords_json": keywords if keywords else None,

            # Streaming
            "watch_providers_json": watch_providers_parsed if watch_providers_parsed else None,

            # Related
            "similar_json": similar if similar else None,
            "recommendations_json": recommendations if recommendations else None,

            # External IDs
            "imdb_id": external_ids.get("imdb_id"),
            "wikidata_id": external_ids.get("wikidata_id"),
            "facebook_id": external_ids.get("facebook_id"),
            "instagram_id": external_ids.get("instagram_id"),
            "twitter_id": external_ids.get("twitter_id"),

            # Media
            "videos_json": videos if videos else None,

            # Credits
            "cast_json": cast if cast else None,
            "crew_json": crew if crew else None,

            # Production
            "production_companies_json": production_companies if production_companies else None,
        }

    def test_connection(self) -> bool:
        """Test API connection by fetching configuration."""
        try:
            data = self._request("/configuration")
            return data is not None
        except Exception as e:
            logger.error(f"TMDB connection test failed: {e}")
            return False
