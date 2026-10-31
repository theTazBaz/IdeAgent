"""
pipeline/enrich_character.py
=============================
4-step enrichment for a Character entity:
  1. Scrape: TMDB movie context + Wikipedia character summary + optional Fandom page
  2. Synthesize: Gemini Flash → {description, core_emotional_logic}
  3. Embed: nomic-embed-text-v1.5 → vector(768)
  4. Upsert: to Supabase (idempotent)

Design note: The description field must contain ONLY individual traits.
Relational logic (e.g. "loves Tony but stays distant") belongs on a
Relationship record — never here. The LLM prompt enforces this rule.
"""
from __future__ import annotations

from uuid import uuid4

import psycopg2

from pipeline import db, embed, llm_synthesize
from pipeline.scrapers import tmdb, wiki


def enrich_character(
    conn: psycopg2.extensions.connection,
    name: str,
    movie_id: str,
    movie_title: str,
    character_id: str | None = None,
    fandom_wiki: str | None = None,
    fandom_slug: str | None = None,
) -> dict:
    """
    Fully enrich a character and write it to the database.

    Args:
        conn:          Open psycopg3 connection.
        name:          Character name (e.g. "Tony Stark").
        movie_id:      UUID of the parent movie (must already exist in DB).
        movie_title:   Title of the parent movie (for TMDB context query).
        character_id:  UUID to use. Generates a new one if None.
        fandom_wiki:   Fandom subdomain, e.g. "dccomics". Optional.
        fandom_slug:   Fandom article slug, e.g. "Batman". Optional.

    Returns:
        The full record dict that was upserted.
    """
    character_id = character_id or db.get_character_by_name(conn, name, movie_id) or str(uuid4())

    # ------------------------------------------------------------------
    # Step 1: Scrape
    # ------------------------------------------------------------------
    print(f"    [1/4] Fetching TMDB movie context for: {name!r}")
    movie_ctx = tmdb.get_character_context(name, movie_title)

    print(f"    [1/4] Fetching Wikipedia summary for: {name!r}")
    wiki_text = wiki.get_wikipedia_summary(f"{name} {movie_title} character")

    fandom_text = ""
    if fandom_wiki and fandom_slug:
        print(f"    [1/4] Fetching Fandom ({fandom_wiki}) page for: {fandom_slug!r}")
        fandom_text = wiki.get_fandom_page(fandom_slug, fandom_wiki)

    raw_facts = {
        "character_name": name,
        "movie_context": movie_ctx,
        "wikipedia": wiki_text,
        "fandom": fandom_text,
    }

    # ------------------------------------------------------------------
    # Step 2: LLM synthesis
    # ------------------------------------------------------------------
    print(f"    [2/4] Synthesizing description via LLM …")
    synthesized = llm_synthesize.synthesize("character", raw_facts)

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
        "id": character_id,
        "movie_id": movie_id,
        "name": name,
        "raw_facts": raw_facts,
        "description": synthesized["description"],
        "core_emotional_logic": synthesized["core_emotional_logic"],
        "text_embedding": embedding,
    }
    db.upsert_character(conn, record)

    print(f"  ✓ Character done: {name} ({movie_title})")
    return record
