"""
pipeline/enrich_song.py
========================
4-step enrichment for a Song entity:
  1. Scrape: Spotify metadata + Wikipedia summary
  2. Synthesize: Gemini Flash → {description, core_emotional_logic}
  3. Embed: nomic-embed-text-v1.5 → vector(768)
  4. Upsert: to Supabase (idempotent)

Note: trend_score is NOT set here — that's a Week 5 concern.
The column is left NULL by upsert and the HNSW index handles NULLs fine.
"""
from __future__ import annotations

from uuid import uuid4

import psycopg2

from pipeline import db, embed, llm_synthesize
from pipeline.scrapers import spotify, wiki


def enrich_song(
    conn: psycopg2.extensions.connection,
    title: str,
    artist: str,
    song_id: str | None = None,
) -> dict:
    """
    Fully enrich a song and write it to the database.

    Args:
        conn:     Open psycopg3 connection.
        title:    Song title (e.g. "Blinding Lights").
        artist:   Artist name (e.g. "The Weeknd").
        song_id:  UUID to use. Generates a new one if None.
                  Pass the existing seed UUID to update a hand-entered record.

    Returns:
        The full record dict that was upserted.
    """
    song_id = song_id or str(uuid4())

    # ------------------------------------------------------------------
    # Step 1: Scrape
    # ------------------------------------------------------------------
    print(f"    [1/4] Fetching Spotify data for: {title!r} by {artist!r}")
    spotify_data = spotify.get_track(title, artist)

    print(f"    [1/4] Fetching Wikipedia summary for: {title!r}")
    wiki_text = wiki.get_wikipedia_summary(f"{title} {artist} song")

    raw_facts = {**spotify_data, "wikipedia_summary": wiki_text}

    # ------------------------------------------------------------------
    # Step 2: LLM synthesis
    # ------------------------------------------------------------------
    print(f"    [2/4] Synthesizing description via LLM …")
    synthesized = llm_synthesize.synthesize("song", raw_facts)

    # ------------------------------------------------------------------
    # Step 3: Embed
    # ------------------------------------------------------------------
    print(f"    [3/4] Embedding description …")
    embedding = embed.embed_text(synthesized["description"])

    # ------------------------------------------------------------------
    # Step 4: Upsert
    # ------------------------------------------------------------------
    print(f"    [4/4] Upserting to DB …")
    record = {
        "id": song_id,
        "title": spotify_data.get("title", title),
        "artist": spotify_data.get("artist", artist),
        "raw_facts": raw_facts,
        "description": synthesized["description"],
        "core_emotional_logic": synthesized["core_emotional_logic"],
        "text_embedding": embedding,
    }
    db.upsert_song(conn, record)

    print(f"  ✓ Song done: {record['title']} — {record['artist']}")
    return record
