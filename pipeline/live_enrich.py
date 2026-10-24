"""
pipeline/live_enrich.py
=======================
Query-time enrichment for a reference entity that is NOT in the database.

Runs the same scrape -> LLM-synthesise steps as the offline enrichers, but
keeps the result in memory only. Nothing is written to the database.

    entity = enrich_live("Titanic", "movie")
    # {"id": None, "type": "movie", "name": "Titanic", "description": ...,
    #  "core_emotional_logic": ..., "source": "live", "sources": "TMDB and Wikipedia"}

Returns None whenever the entity cannot be grounded (no API result, the
result does not match the name asked for, missing keys, network errors), so
the caller can fall back to low-confidence handling.
"""
from __future__ import annotations

from pipeline import llm_synthesize
from pipeline.scrapers import spotify, tmdb, wiki
from pipeline.search_db import _fuzzy_score

_MAX_CACHE = 128
_cache: dict[tuple, dict] = {}   # successes only, so a transient failure is retried


def _matches(asked: str, found: str | None) -> bool:
    """True if the API's result is plausibly the thing the user asked about."""
    return bool(found) and _fuzzy_score(asked, found) is not None


def _movie(name: str) -> dict | None:
    data = tmdb.get_movie(name)
    if not _matches(name, data.get("title")):
        print(f"       live: TMDB returned {data.get('title')!r}, which is not {name!r} — ignoring.")
        return None
    wiki_text = wiki.get_wikipedia_summary(f"{data['title']} film")
    facts = {**data, "wikipedia_summary": wiki_text}
    out = llm_synthesize.synthesize("movie", facts)
    return {"name": data["title"], "type": "movie", "sources": "TMDB and Wikipedia", **out}


def _character(name: str, movie_title: str) -> dict | None:
    ctx = tmdb.get_character_context(name, movie_title)
    if not _matches(movie_title, ctx.get("source_movie")):
        print(f"       live: TMDB returned {ctx.get('source_movie')!r}, which is not {movie_title!r} — ignoring.")
        return None
    wiki_text = wiki.get_wikipedia_summary(f"{name} {ctx['source_movie']} character")
    if not wiki_text and not ctx.get("in_tmdb_cast"):
        return None  # nothing about the character itself to ground on
    facts = {"character_name": name, "movie_context": ctx, "wikipedia": wiki_text, "fandom": ""}
    out = llm_synthesize.synthesize("character", facts)
    return {"name": name, "type": "character", "sources": "TMDB and Wikipedia", **out}


def _song(name: str, artist: str | None) -> dict | None:
    data = spotify.get_track(name, artist or "")
    if not _matches(name, data.get("title")):
        print(f"       live: Spotify returned {data.get('title')!r}, which is not {name!r} — ignoring.")
        return None
    wiki_text = wiki.get_wikipedia_summary(f"{data['title']} {data['artist']} song")
    facts = {**data, "wikipedia_summary": wiki_text}
    out = llm_synthesize.synthesize("song", facts)
    return {"name": data["title"], "type": "song", "sources": "Spotify and Wikipedia", **out}


def enrich_live(name: str, kind: str | None = None, context: str | None = None) -> dict | None:
    """
    Look up `name` live and return an entity dict, or None if it can't be grounded.

    kind:    "movie", "character" or "song" (defaults to "movie" when unknown).
    context: the movie title for a character, or the artist for a song.
    """
    kind = (kind or "movie").lower()
    key = (kind, name.strip().lower(), (context or "").strip().lower())
    if key in _cache:
        return _cache[key]

    try:
        if kind == "movie":
            found = _movie(name)
        elif kind == "character":
            found = _character(name, context) if context else None
        elif kind == "song":
            found = _song(name, context)
        else:
            return None
    except Exception as exc:  # network, missing API key, bad LLM JSON ...
        print(f"       live: lookup for {name!r} failed — {type(exc).__name__}: {str(exc)[:120]}")
        return None

    if not found:
        return None
    entity = {"id": None, "source": "live", **found}
    if len(_cache) >= _MAX_CACHE:
        _cache.pop(next(iter(_cache)))
    _cache[key] = entity
    return entity
