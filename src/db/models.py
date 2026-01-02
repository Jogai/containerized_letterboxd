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


class Film(Base):
    """Film/movie information."""
    __tablename__ = "films"

    id = Column(Integer, primary_key=True)
    slug = Column(String(300), unique=True, nullable=False, index=True)  # e.g., "the-godfather"
    title = Column(String(500), nullable=False)
    year = Column(Integer, index=True)

    # Ratings
    rating = Column(Float)  # Letterboxd average rating (out of 5)
    rating_count = Column(Integer)

    # Details
    runtime_minutes = Column(Integer)
    tagline = Column(Text)
    description = Column(Text)
    poster_url = Column(String(500))

    # Structured data stored as JSON
    genres_json = Column(JSON)  # ["Drama", "Crime"]
    directors_json = Column(JSON)  # [{"name": "Francis Ford Coppola", "slug": "..."}]
    cast_json = Column(JSON)  # [{"name": "Marlon Brando", "slug": "...", "character": "..."}]
    countries_json = Column(JSON)
    languages_json = Column(JSON)
    studios_json = Column(JSON)

    # Metadata
    letterboxd_url = Column(String(500))
    tmdb_id = Column(String(50))
    imdb_id = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    diary_entries = relationship("DiaryEntry", back_populates="film")
    watchlist_items = relationship("WatchlistItem", back_populates="film")


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
    sync_type = Column(String(50), nullable=False)  # "full", "diary", "watchlist"
    username = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String(20), default="running")  # "running", "completed", "failed"
    items_processed = Column(Integer, default=0)
    error_message = Column(Text)
