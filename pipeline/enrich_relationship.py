"""
pipeline/enrich_relationship.py
================================
4-step enrichment for a Relationship entity:
  1. Scrape: Pull both characters' already-enriched descriptions from DB
             + Wikipedia search for the character dynamic (optional)
  2. Synthesize: Groq LLM → {description, core_emotional_logic}
  3. Embed: nomic-embed-text-v1.5 → vector(768)
  4. Upsert: to Supabase (idempotent)

Important: Relationships must be enriched AFTER both characters are enriched,
because Step 1 reads character descriptions from the DB.
The batch runner (run_batch.py) enforces this order automatically.
"""
from __future__ import annotations

from uuid import uuid4

import psycopg2

from pipeline import db, embed, llm_synthesize
from pipeline.scrapers import wiki


def enrich_relationship(
    conn: psycopg2.extensions.connection,
    character_id_a: str,
    character_id_b: str,
    movie_id: str,
    label: str,
    relationship_id: str | None = None,
    search_query: str | None = None,
) -> dict:
    """
    Fully enrich a relationship and write it to the database.

    Args:
        conn:             Open psycopg3 connection.
        character_id_a:   UUID of the first character (must already be enriched).
        character_id_b:   UUID of the second character (must already be enriched).
        movie_id:         UUID of the parent movie.
        label:            Human-readable label, e.g. "Batman & Joker".
        relationship_id:  UUID to use. Generates a new one if None.
        search_query:     Optional Wikipedia search query for the dynamic,
                          e.g. "Batman Joker dynamic relationship". Falls back
                          to an empty string if omitted or not found.

    Returns:
        The full record dict that was upserted.
    """
    relationship_id = relationship_id or str(uuid4())

    # ------------------------------------------------------------------
    # Step 1: Scrape
    # ------------------------------------------------------------------
    print(f"    [1/4] Fetching character descriptions from DB for: {label!r}")
    char_a = db.get_character(conn, character_id_a)
    char_b = db.get_character(conn, character_id_b)

    if char_a is None:
        raise ValueError(
            f"Character {character_id_a!r} not found in DB. "
            "Enrich both characters before enriching their relationship."
        )
    if char_b is None:
        raise ValueError(
            f"Character {character_id_b!r} not found in DB. "
            "Enrich both characters before enriching their relationship."
        )

    wiki_text = ""
    if search_query:
        print(f"    [1/4] Fetching Wikipedia for: {search_query!r}")
        wiki_text = wiki.get_wikipedia_summary(search_query)

    raw_facts = {
        "label": label,
        "character_a": char_a,
        "character_b": char_b,
        "wikipedia": wiki_text,
    }

    # ------------------------------------------------------------------
    # Step 2: LLM synthesis
    # ------------------------------------------------------------------
    print(f"    [2/4] Synthesizing description via LLM …")
    synthesized = llm_synthesize.synthesize("relationship", raw_facts)

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
        "id": relationship_id,
        "movie_id": movie_id,
        "character_id_a": character_id_a,
        "character_id_b": character_id_b,
        "label": label,
        "raw_facts": raw_facts,
        "description": synthesized["description"],
        "core_emotional_logic": synthesized["core_emotional_logic"],
        "text_embedding": embedding,
    }
    db.upsert_relationship(conn, record)

    print(f"  ✓ Relationship done: {label}")
    return record
