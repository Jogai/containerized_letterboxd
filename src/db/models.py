from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.db.database import Base


class User(Base):
    """Letterboxd user profile."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200))
    bio = Column(Text)
    location = Column(String(200))
    website = Column(String(500))
    favorites_json = Column(JSON)  # List of favorite film slugs
    stats_json = Column(JSON)  # films, this_year, lists, following, followers

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    diary_entries = relationship("DiaryEntry", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")
    user_films = relationship("UserFilm", back_populates="user", cascade="all, delete-orphan")


class Film(Base):
    """Film/movie information."""
    __tablename__ = "films"

    id = Column(Integer, primary_key=True)
    slug = Column(String(300), unique=True, nullable=False, index=True)  # e.g., "the-godfather"
    letterboxd_id = Column(String(50))  # Letterboxd internal ID
    title = Column(String(500), nullable=False)
    original_title = Column(String(500))  # Original language title
    year = Column(Integer, index=True)

    # Ratings & Popularity
    rating = Column(Float)  # Letterboxd average rating (out of 5)
    rating_count = Column(Integer)
    watchers_stats_json = Column(JSON)  # {members, fans, likes, reviews, lists}

    # Details
    runtime_minutes = Column(Integer)
    tagline = Column(Text)
    description = Column(Text)
    poster_url = Column(String(500))
    banner_url = Column(String(500))  # Banner image
    trailer_json = Column(JSON)  # {id, link, embed_url}
    alternative_titles_json = Column(JSON)  # List of international titles

    # Structured data stored as JSON
    genres_json = Column(JSON)  # [{"type": "genre", "name": "Drama", ...}]
    directors_json = Column(JSON)  # [{"name": "Francis Ford Coppola", "slug": "..."}]
    crew_json = Column(JSON)  # Full crew: {director: [...], writer: [...], composer: [...], ...}
    cast_json = Column(JSON)  # [{"name": "Marlon Brando", "slug": "...", "role_name": "..."}]
    countries_json = Column(JSON)  # [{"type": "country", "name": "USA", ...}]
    languages_json = Column(JSON)  # [{"type": "language", "name": "English", ...}]
    studios_json = Column(JSON)  # [{"type": "studio", "name": "Paramount", ...}]
    popular_reviews_json = Column(JSON)  # Top 12 reviews

    # External IDs & Links
    letterboxd_url = Column(String(500))
    tmdb_id = Column(String(50))
    imdb_id = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    diary_entries = relationship("DiaryEntry", back_populates="film")
    watchlist_items = relationship("WatchlistItem", back_populates="film")
    user_films = relationship("UserFilm", back_populates="film")
    tmdb_data = relationship("TmdbFilm", back_populates="film", uselist=False, cascade="all, delete-orphan")


class DiaryEntry(Base):
    """A user's film diary entry (watched film)."""
    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    film_id = Column(Integer, ForeignKey("films.id"), nullable=False, index=True)

    # Watch info
    watched_date = Column(DateTime, index=True)
    rating = Column(Float)  # User's rating (0.5 to 5, in 0.5 increments)
    rewatch = Column(Boolean, default=False)
    liked = Column(Boolean, default=False)

    # Review
    review_text = Column(Text)
    review_has_spoilers = Column(Boolean, default=False)

    # Letterboxd identifiers
    letterboxd_id = Column(String(100), unique=True)  # To avoid duplicates on sync

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="diary_entries")
    film = relationship("Film", back_populates="diary_entries")


class UserFilm(Base):
    """User's relationship with a film (watched status, rating, etc.)

    This captures ALL watched films, including those without diary entries.
    Datamaxx philosophy: capture everything.
    """
    __tablename__ = "user_films"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    film_id = Column(Integer, ForeignKey("films.id"), nullable=False, index=True)

    # Core status
    watched = Column(Boolean, default=False)  # In user's watched list
    rating = Column(Float)  # User's rating (may exist without diary entry!)
    liked = Column(Boolean, default=False)  # Aggregated from diary or standalone

    # Derived from diary entries
    watch_count = Column(Integer, default=0)  # Number of diary entries
    first_watched = Column(DateTime)  # Earliest diary entry date
    last_watched = Column(DateTime)  # Most recent diary entry date

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_films")
    film = relationship("Film", back_populates="user_films")


class WatchlistItem(Base):
    """A film on a user's watchlist."""
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    film_id = Column(Integer, ForeignKey("films.id"), nullable=False, index=True)

    added_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlist_items")
    film = relationship("Film", back_populates="watchlist_items")


class SyncLog(Base):
    """Track sync operations."""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    sync_type = Column(String(50), nullable=False)  # "full", "diary", "watchlist", "tmdb"
    username = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String(20), default="running")  # "running", "completed", "failed"
    items_processed = Column(Integer, default=0)
    error_message = Column(Text)


class TmdbFilm(Base):
    """TMDB enrichment data for films.

    Separated from Film table to keep Letterboxd data distinct from TMDB data.
    1:1 relationship with Film via film_id.
    """
    __tablename__ = "tmdb_films"

    id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("films.id"), unique=True, nullable=False, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)

    # === Financial ===
    budget = Column(Integer)  # Production budget in USD
    revenue = Column(Integer)  # Box office revenue in USD

    # === Ratings ===
    vote_average = Column(Float)  # TMDB rating out of 10
    vote_count = Column(Integer)  # Number of TMDB votes
    popularity = Column(Float)  # TMDB popularity score

    # === Classification ===
    certification = Column(String(20))  # US certification: "R", "PG-13", etc.
    certifications_json = Column(JSON)  # All countries: {"US": "R", "GB": "15", ...}
    adult = Column(Boolean, default=False)

    # === Metadata ===
    status = Column(String(50))  # "Released", "Post Production", "Planned", etc.
    release_date = Column(String(20))  # Full date: "1999-10-15"
    homepage = Column(String(500))  # Official website
    origin_country_json = Column(JSON)  # Primary origin countries: ["US", "GB"]

    # === Collection/Franchise ===
    collection_id = Column(Integer)  # TMDB collection ID
    collection_name = Column(String(300))  # "The Godfather Collection"
    collection_poster_path = Column(String(300))  # Collection poster

    # === Thematic ===
    keywords_json = Column(JSON)  # [{"id": 123, "name": "time travel"}, ...]

    # === Streaming/Watch Providers ===
    watch_providers_json = Column(JSON)  # {"US": {"flatrate": [...], "rent": [...], "buy": [...]}}

    # === Related Films ===
    similar_json = Column(JSON)  # List of similar TMDB IDs
    recommendations_json = Column(JSON)  # List of recommended TMDB IDs

    # === External IDs ===
    imdb_id = Column(String(20))  # IMDb ID (also in Film, but TMDB's version)
    wikidata_id = Column(String(50))  # Wikidata ID
    facebook_id = Column(String(100))  # Facebook page ID
    instagram_id = Column(String(100))  # Instagram handle
    twitter_id = Column(String(100))  # Twitter/X handle

    # === Media ===
    videos_json = Column(JSON)  # All trailers, teasers, featurettes

    # === Credits (TMDB's detailed version) ===
    cast_json = Column(JSON)  # Detailed cast with order, character, profile_path
    crew_json = Column(JSON)  # Detailed crew with department, job

    # === Production ===
    production_companies_json = Column(JSON)  # Detailed production companies

    # === Sync Tracking ===
    last_synced_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    film = relationship("Film", back_populates="tmdb_data")
