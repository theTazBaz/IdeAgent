"""
pipeline/scrapers/tmdb.py
==========================
TMDB API scraper for movie metadata and cast information.

Free API key (no credit card): https://www.themoviedb.org/settings/api
Uses the v3 API key method — pass as ?api_key= query param.
(The Bearer/JWT method is a separate "Read Access Token" from the TMDB dashboard;
 the shorter 32-char hex key is the classic v3 API key and uses the query param.)
"""
from __future__ import annotations

import time

import httpx

from pipeline import config

TMDB_BASE = "https://api.themoviedb.org/3"
_MAX_RETRIES = 3
_RETRY_DELAY = 1.5  # seconds between retries


def _api_key() -> str:
    return config.require(
        "TMDB_API_KEY",
        config.TMDB_API_KEY,
        hint="Free API key (no credit card): https://www.themoviedb.org/settings/api",
    )


def _get(client: httpx.Client, url: str, extra_params: dict | None = None) -> httpx.Response:
    """GET with api_key injected and retry on connection/transport errors."""
    params = {"api_key": _api_key(), **(extra_params or {})}
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_exc = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY * (attempt + 1))
    raise last_exc  # type: ignore[misc]


# ------------------------------------------------------------------
# Movie
# ------------------------------------------------------------------
def get_movie(title: str) -> dict:
    """
    Fetch rich metadata for a movie from TMDB.

    Returns a dict with keys:
      title, overview, release_year, genres, runtime_minutes,
      vote_average, director, top_cast (list of up to 8 names), tagline
    """
    with httpx.Client(timeout=15.0) as client:
        # Step 1: search
        r = _get(client, f"{TMDB_BASE}/search/movie", {"query": title, "include_adult": "false"})
        results = r.json().get("results", [])
        if not results:
            raise ValueError(f"No TMDB results for movie: {title!r}")
        movie_id = results[0]["id"]

        # Step 2: details
        r = _get(client, f"{TMDB_BASE}/movie/{movie_id}")
        details = r.json()

        # Step 3: credits
        r = _get(client, f"{TMDB_BASE}/movie/{movie_id}/credits")
        credits = r.json()

    top_cast = [c["name"] for c in credits.get("cast", [])[:8]]
    director = next(
        (c["name"] for c in credits.get("crew", []) if c["job"] == "Director"),
        None,
    )

    return {
        "title": details.get("title"),
        "overview": details.get("overview"),
        "release_year": (details.get("release_date") or "")[:4],
        "genres": [g["name"] for g in details.get("genres", [])],
        "runtime_minutes": details.get("runtime"),
        "vote_average": details.get("vote_average"),
        "tagline": details.get("tagline"),
        "director": director,
        "top_cast": top_cast,
    }


# ------------------------------------------------------------------
# Character (pulls movie context for grounding)
# ------------------------------------------------------------------
def get_character_context(character_name: str, movie_title: str) -> dict:
    """
    Retrieve the movie's TMDB metadata as context for a character.

    We don't have character-level endpoints in TMDB, so we use the movie
    details + cast presence as grounding for the character description.
    The character's own traits come primarily from Wikipedia/Fandom scraping.
    """
    movie = get_movie(movie_title)
    in_cast = character_name.lower() in " ".join(movie["top_cast"]).lower()
    return {
        "character_name": character_name,
        "source_movie": movie["title"],
        "movie_overview": movie["overview"],
        "movie_genres": movie["genres"],
        "movie_release_year": movie["release_year"],
        "director": movie["director"],
        "in_tmdb_cast": in_cast,
    }
