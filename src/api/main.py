"""
FastAPI app to serve Letterboxd data.
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.db.database import get_db, init_db
from src.db.models import User, Film, DiaryEntry, WatchlistItem, SyncLog
from src.scraper.sync import run_sync

app = FastAPI(
    title="Your Letterboxd",
    description="Local backup and viewer for your Letterboxd data",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    init_db()


# ─────────────────────────────────────────────────────────────────────────────
# HTML Views - List all data
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(db: Session = Depends(get_db)):
    """Home page with summary and links."""
    user_count = db.query(User).count()
    film_count = db.query(Film).count()
    diary_count = db.query(DiaryEntry).count()
    watchlist_count = db.query(WatchlistItem).count()

    last_sync = db.query(SyncLog).order_by(SyncLog.started_at.desc()).first()
    last_sync_str = last_sync.started_at.strftime("%Y-%m-%d %H:%M") if last_sync else "Never"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            h2 {{ color: #99aabb; border-bottom: 1px solid #456; padding-bottom: 10px; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
            .stat {{ background: #1c2228; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-number {{ font-size: 2em; color: #00e054; font-weight: bold; }}
            .stat-label {{ color: #99aabb; margin-top: 5px; }}
            .nav {{ margin: 30px 0; }}
            .nav a {{ background: #00e054; color: #14181c; padding: 10px 20px; border-radius: 5px; margin-right: 10px; font-weight: bold; }}
            .nav a:hover {{ background: #00c04a; text-decoration: none; }}
            .info {{ color: #678; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>Your Letterboxd</h1>
        <p>Local backup of your Letterboxd data</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{user_count}</div>
                <div class="stat-label">Users</div>
            </div>
            <div class="stat">
                <div class="stat-number">{film_count}</div>
                <div class="stat-label">Films</div>
            </div>
            <div class="stat">
                <div class="stat-number">{diary_count}</div>
                <div class="stat-label">Diary Entries</div>
            </div>
            <div class="stat">
                <div class="stat-number">{watchlist_count}</div>
                <div class="stat-label">Watchlist</div>
            </div>
        </div>

        <div class="nav">
            <a href="/users">Users</a>
            <a href="/films">Films</a>
            <a href="/diary">Diary</a>
            <a href="/watchlist">Watchlist</a>
            <a href="/syncs">Sync History</a>
        </div>

        <p class="info">Last sync: {last_sync_str}</p>
    </body>
    </html>
    """
    return html


@app.get("/users", response_class=HTMLResponse)
def list_users(db: Session = Depends(get_db)):
    """List all users."""
    users = db.query(User).all()

    rows = ""
    for u in users:
        stats = u.stats_json or {}
        rows += f"""
        <tr>
            <td><a href="/users/{u.username}">{u.username}</a></td>
            <td>{u.display_name or ''}</td>
            <td>{stats.get('films', 0)}</td>
            <td>{len(u.diary_entries)}</td>
            <td>{len(u.watchlist_items)}</td>
            <td>{u.updated_at.strftime('%Y-%m-%d %H:%M') if u.updated_at else ''}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Users - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1100px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #456; }}
            th {{ background: #1c2228; color: #99aabb; }}
            tr:hover {{ background: #1c2228; }}
            .back {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/">&larr; Back</a></div>
        <h1>Users</h1>
        <table>
            <tr>
                <th>Username</th>
                <th>Display Name</th>
                <th>Total Films</th>
                <th>Diary Entries</th>
                <th>Watchlist</th>
                <th>Last Updated</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return html


@app.get("/users/{username}", response_class=HTMLResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    """Get user details."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stats = user.stats_json or {}
    favorites = user.favorites_json or []

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{user.username} - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            h2 {{ color: #99aabb; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            .meta {{ color: #678; margin: 10px 0; }}
            .bio {{ background: #1c2228; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
            .stat {{ background: #1c2228; padding: 15px; border-radius: 8px; text-align: center; }}
            .back {{ margin-bottom: 20px; }}
            pre {{ background: #1c2228; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/users">&larr; Back to Users</a></div>
        <h1>{user.display_name or user.username}</h1>
        <p class="meta">@{user.username} {(' - ' + user.location) if user.location else ''}</p>

        {f'<div class="bio">{user.bio}</div>' if user.bio else ''}

        <div class="stats">
            <div class="stat"><strong>{stats.get('films', 0)}</strong><br>Films</div>
            <div class="stat"><strong>{stats.get('following', 0)}</strong><br>Following</div>
            <div class="stat"><strong>{stats.get('followers', 0)}</strong><br>Followers</div>
        </div>

        <h2>Favorites</h2>
        <p>{', '.join(favorites) if favorites else 'None'}</p>

        <h2>Raw Data</h2>
        <pre>{user.stats_json}</pre>
    </body>
    </html>
    """
    return html


@app.get("/films", response_class=HTMLResponse)
def list_films(
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all films with pagination."""
    offset = (page - 1) * limit
    total = db.query(Film).count()
    films = db.query(Film).order_by(Film.year.desc()).offset(offset).limit(limit).all()

    rows = ""
    for f in films:
        directors = ", ".join([d.get("name", "") for d in (f.directors_json or [])[:2]])
        genres = ", ".join([g.get("name", "") if isinstance(g, dict) else str(g) for g in (f.genres_json or [])[:3]])
        rows += f"""
        <tr>
            <td><a href="/films/{f.slug}">{f.title}</a></td>
            <td>{f.year or ''}</td>
            <td>{directors}</td>
            <td>{genres}</td>
            <td>{f.rating or ''}</td>
            <td>{f.runtime_minutes or ''} min</td>
        </tr>
        """

    total_pages = (total + limit - 1) // limit
    prev_link = f'<a href="/films?page={page-1}">&larr; Prev</a>' if page > 1 else ''
    next_link = f'<a href="/films?page={page+1}">Next &rarr;</a>' if page < total_pages else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Films - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1100px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #456; }}
            th {{ background: #1c2228; color: #99aabb; }}
            tr:hover {{ background: #1c2228; }}
            .back {{ margin-bottom: 20px; }}
            .pagination {{ margin-top: 20px; display: flex; justify-content: space-between; }}
            .info {{ color: #678; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/">&larr; Back</a></div>
        <h1>Films ({total} total)</h1>
        <table>
            <tr>
                <th>Title</th>
                <th>Year</th>
                <th>Director(s)</th>
                <th>Genres</th>
                <th>Rating</th>
                <th>Runtime</th>
            </tr>
            {rows}
        </table>
        <div class="pagination">
            <span>{prev_link}</span>
            <span class="info">Page {page} of {total_pages}</span>
            <span>{next_link}</span>
        </div>
    </body>
    </html>
    """
    return html


@app.get("/films/{slug}", response_class=HTMLResponse)
def get_film(slug: str, db: Session = Depends(get_db)):
    """Get film details."""
    film = db.query(Film).filter(Film.slug == slug).first()
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")

    directors = ", ".join([d.get("name", "") for d in (film.directors_json or [])])
    cast = ", ".join([c.get("name", "") for c in (film.cast_json or [])[:10]])
    genres = ", ".join([g.get("name", "") if isinstance(g, dict) else str(g) for g in (film.genres_json or [])])
    countries = ", ".join([c.get("name", "") if isinstance(c, dict) else str(c) for c in (film.countries_json or [])])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{film.title} - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            h2 {{ color: #99aabb; margin-top: 30px; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            .meta {{ color: #678; margin: 10px 0; }}
            .poster {{ max-width: 200px; border-radius: 8px; margin: 20px 0; }}
            .description {{ background: #1c2228; padding: 15px; border-radius: 8px; margin: 20px 0; line-height: 1.6; }}
            .details {{ display: grid; grid-template-columns: 150px 1fr; gap: 10px; margin: 20px 0; }}
            .details dt {{ color: #99aabb; }}
            .back {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/films">&larr; Back to Films</a></div>

        {f'<img src="{film.poster_url}" class="poster" />' if film.poster_url else ''}

        <h1>{film.title} <span style="color:#678">({film.year})</span></h1>
        {f'<p class="meta"><em>{film.tagline}</em></p>' if film.tagline else ''}

        <dl class="details">
            <dt>Director(s)</dt><dd>{directors or 'Unknown'}</dd>
            <dt>Genres</dt><dd>{genres or 'Unknown'}</dd>
            <dt>Runtime</dt><dd>{film.runtime_minutes or '?'} minutes</dd>
            <dt>Rating</dt><dd>{film.rating or 'N/A'} / 5</dd>
            <dt>Countries</dt><dd>{countries or 'Unknown'}</dd>
        </dl>

        {f'<div class="description">{film.description}</div>' if film.description else ''}

        <h2>Cast</h2>
        <p>{cast or 'Unknown'}</p>

        <h2>External Links</h2>
        <p>
            {f'<a href="{film.letterboxd_url}" target="_blank">Letterboxd</a>' if film.letterboxd_url else ''}
            {f' | <a href="https://www.imdb.com/title/{film.imdb_id}" target="_blank">IMDb</a>' if film.imdb_id else ''}
            {f' | <a href="https://www.themoviedb.org/movie/{film.tmdb_id}" target="_blank">TMDB</a>' if film.tmdb_id else ''}
        </p>
    </body>
    </html>
    """
    return html


@app.get("/diary", response_class=HTMLResponse)
def list_diary(
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all diary entries."""
    offset = (page - 1) * limit
    total = db.query(DiaryEntry).count()
    entries = (
        db.query(DiaryEntry)
        .order_by(DiaryEntry.watched_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    rows = ""
    for e in entries:
        rating_stars = "★" * int(e.rating) + "½" * (1 if e.rating and e.rating % 1 else 0) if e.rating else ""
        rows += f"""
        <tr>
            <td>{e.watched_date.strftime('%Y-%m-%d') if e.watched_date else ''}</td>
            <td><a href="/films/{e.film.slug}">{e.film.title}</a></td>
            <td>{e.film.year or ''}</td>
            <td style="color:#00e054">{rating_stars}</td>
            <td>{'♥' if e.liked else ''}</td>
            <td>{'↻' if e.rewatch else ''}</td>
            <td>{'📝' if e.review_text else ''}</td>
        </tr>
        """

    total_pages = (total + limit - 1) // limit
    prev_link = f'<a href="/diary?page={page-1}">&larr; Prev</a>' if page > 1 else ''
    next_link = f'<a href="/diary?page={page+1}">Next &rarr;</a>' if page < total_pages else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Diary - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1100px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #456; }}
            th {{ background: #1c2228; color: #99aabb; }}
            tr:hover {{ background: #1c2228; }}
            .back {{ margin-bottom: 20px; }}
            .pagination {{ margin-top: 20px; display: flex; justify-content: space-between; }}
            .info {{ color: #678; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/">&larr; Back</a></div>
        <h1>Diary ({total} entries)</h1>
        <table>
            <tr>
                <th>Date</th>
                <th>Film</th>
                <th>Year</th>
                <th>Rating</th>
                <th>Liked</th>
                <th>Rewatch</th>
                <th>Review</th>
            </tr>
            {rows}
        </table>
        <div class="pagination">
            <span>{prev_link}</span>
            <span class="info">Page {page} of {total_pages}</span>
            <span>{next_link}</span>
        </div>
    </body>
    </html>
    """
    return html


@app.get("/watchlist", response_class=HTMLResponse)
def list_watchlist(
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List watchlist items."""
    offset = (page - 1) * limit
    total = db.query(WatchlistItem).count()
    items = (
        db.query(WatchlistItem)
        .order_by(WatchlistItem.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    rows = ""
    for w in items:
        directors = ", ".join([d.get("name", "") for d in (w.film.directors_json or [])[:2]])
        rows += f"""
        <tr>
            <td><a href="/films/{w.film.slug}">{w.film.title}</a></td>
            <td>{w.film.year or ''}</td>
            <td>{directors}</td>
            <td>{w.film.runtime_minutes or ''} min</td>
        </tr>
        """

    total_pages = (total + limit - 1) // limit if total else 1
    prev_link = f'<a href="/watchlist?page={page-1}">&larr; Prev</a>' if page > 1 else ''
    next_link = f'<a href="/watchlist?page={page+1}">Next &rarr;</a>' if page < total_pages else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Watchlist - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1100px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #456; }}
            th {{ background: #1c2228; color: #99aabb; }}
            tr:hover {{ background: #1c2228; }}
            .back {{ margin-bottom: 20px; }}
            .pagination {{ margin-top: 20px; display: flex; justify-content: space-between; }}
            .info {{ color: #678; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/">&larr; Back</a></div>
        <h1>Watchlist ({total} films)</h1>
        <table>
            <tr>
                <th>Film</th>
                <th>Year</th>
                <th>Director(s)</th>
                <th>Runtime</th>
            </tr>
            {rows}
        </table>
        <div class="pagination">
            <span>{prev_link}</span>
            <span class="info">Page {page} of {total_pages}</span>
            <span>{next_link}</span>
        </div>
    </body>
    </html>
    """
    return html


@app.get("/syncs", response_class=HTMLResponse)
def list_syncs(db: Session = Depends(get_db)):
    """List sync history."""
    syncs = db.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(50).all()

    rows = ""
    for s in syncs:
        status_color = {"completed": "#00e054", "failed": "#ff4444", "running": "#ffaa00"}.get(s.status, "#fff")
        rows += f"""
        <tr>
            <td>{s.started_at.strftime('%Y-%m-%d %H:%M')}</td>
            <td>{s.username}</td>
            <td>{s.sync_type}</td>
            <td style="color:{status_color}">{s.status}</td>
            <td>{s.items_processed or 0}</td>
            <td>{s.error_message or ''}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sync History - Your Letterboxd</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1100px; margin: 50px auto; padding: 20px; background: #14181c; color: #fff; }}
            h1 {{ color: #00e054; }}
            a {{ color: #40bcf4; text-decoration: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #456; }}
            th {{ background: #1c2228; color: #99aabb; }}
            tr:hover {{ background: #1c2228; }}
            .back {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/">&larr; Back</a></div>
        <h1>Sync History</h1>
        <table>
            <tr>
                <th>Started</th>
                <th>Username</th>
                <th>Type</th>
                <th>Status</th>
                <th>Items</th>
                <th>Error</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return html


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/sync/{username}")
def trigger_sync(
    username: str,
    background_tasks: BackgroundTasks,
    fetch_details: bool = True
):
    """Trigger a sync for a user (runs in background)."""
    background_tasks.add_task(run_sync, username, fetch_details)
    return {"status": "started", "username": username}


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics."""
    return {
        "users": db.query(User).count(),
        "films": db.query(Film).count(),
        "diary_entries": db.query(DiaryEntry).count(),
        "watchlist_items": db.query(WatchlistItem).count(),
    }
