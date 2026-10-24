"""
pipeline/enrich_movie.py
========================
4-step enrichment for a Movie entity:
  1. Scrape: TMDB metadata + Wikipedia summary
  2. Synthesize: Groq LLM → {description, core_emotional_logic}
  3. Embed: nomic-embed-text-v1.5 → vector(768)
  4. Upsert: to Supabase (idempotent)
"""
from __future__ import annotations

from uuid import uuid4

import psycopg2

from pipeline import db, embed, llm_synthesize
from pipeline.scrapers import tmdb, wiki


def enrich_movie(
    conn: psycopg2.extensions.connection,
    title: str,
    movie_id: Optional[str] = None,
) -> dict:
    """
    Fully enrich a movie and write it to the database.

    Args:
        conn:     Open psycopg3 connection.
        title:    The movie title to enrich (e.g. "Interstellar").
        movie_id: UUID to use. If None, a new UUID is generated.
                  Pass the existing seed UUID to update a hand-entered record.

    Returns:
        The full record dict that was upserted (useful for chaining / logging).
    """
    movie_id = movie_id or str(uuid4())

    # ------------------------------------------------------------------
    # Step 1: Scrape
    # ------------------------------------------------------------------
    print(f"    [1/4] Scraping TMDB for: {title!r}")
    tmdb_data = tmdb.get_movie(title)

    print(f"    [1/4] Fetching Wikipedia summary for: {title!r}")
    wiki_text = wiki.get_wikipedia_summary(f"{title} film")

    raw_facts = {**tmdb_data, "wikipedia_summary": wiki_text}

    # ------------------------------------------------------------------
    # Step 2: LLM synthesis
    # ------------------------------------------------------------------
    print(f"    [2/4] Synthesizing description via LLM …")
    synthesized = llm_synthesize.synthesize("movie", raw_facts)

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
        "id": movie_id,
        "title": tmdb_data.get("title", title),
        "raw_facts": raw_facts,
        "description": synthesized["description"],
        "core_emotional_logic": synthesized["core_emotional_logic"],
        "text_embedding": embedding,
    }
    db.upsert_movie(conn, record)

    print(f"  ✓ Movie done: {record['title']}")
    return record
