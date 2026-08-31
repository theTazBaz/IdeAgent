"""
pipeline/search_db.py
=====================
Database helpers for the RAG search pipeline.

Two entry points:
  - get_entity_by_name()  → exact-text lookup of a named entity
  - vector_search()       → pgvector cosine similarity across all tables
"""
from __future__ import annotations

import psycopg2
import numpy as np

from pipeline import db, embed


# ------------------------------------------------------------------
# Exact-name lookup
# ------------------------------------------------------------------
def get_entity_by_name(conn: psycopg2.extensions.connection, name: str) -> dict | None:
    """
    Find one entity (movie, character, or song) whose title/name is a
    case-insensitive match for `name`.

    Returns a dict with keys: type, name, description, core_emotional_logic
    or None if nothing is found.
    """
    searches = [
        ("movie",    "SELECT 'movie', title, description, core_emotional_logic FROM movies     WHERE LOWER(title) = LOWER(%s) LIMIT 1"),
        ("character","SELECT 'character', name,  description, core_emotional_logic FROM characters WHERE LOWER(name)  = LOWER(%s) LIMIT 1"),
        ("song",     "SELECT 'song',  title, description, core_emotional_logic FROM songs      WHERE LOWER(title) = LOWER(%s) LIMIT 1"),
    ]
    with conn.cursor() as cur:
        for entity_type, sql in searches:
            cur.execute(sql, (name,))
            row = cur.fetchone()
            if row:
                return {
                    "type":                entity_type,
                    "name":                row[1],
                    "description":         row[2],
                    "core_emotional_logic": row[3],
                }
    return None


# ------------------------------------------------------------------
# Vector similarity search
# ------------------------------------------------------------------
def vector_search(
    conn: psycopg2.extensions.connection,
    query_text: str,
    filter_type: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Embed `query_text` and run a cosine similarity search across all tables.

    Args:
        conn:        Open psycopg2 connection.
        query_text:  The search string to embed (should be a dense description,
                     NOT the raw user question).
        filter_type: Optional – one of "movies", "characters",
                     "relationships", "songs" to restrict the search.
        top_k:       Number of results to return.

    Returns:
        List of dicts: {type, name, description, core_emotional_logic, similarity}
    """
    query_vec = embed.embed_text(query_text, is_query=True)
    vec = db._vec(query_vec)

    # Build the UNION ALL query — optionally filter to one table
    subqueries = {
        "movies":        "SELECT 'movie'        AS type, title        AS name, description, core_emotional_logic, text_embedding FROM movies",
        "characters":    "SELECT 'character'    AS type, name         AS name, description, core_emotional_logic, text_embedding FROM characters",
        "relationships": "SELECT 'relationship' AS type, label        AS name, description, core_emotional_logic, text_embedding FROM relationships",
        "songs":         "SELECT 'song'         AS type, title || ' — ' || artist AS name, description, core_emotional_logic, text_embedding FROM songs",
    }

    if filter_type and filter_type in subqueries:
        union_sql = subqueries[filter_type]
    else:
        union_sql = "\n    UNION ALL\n    ".join(subqueries.values())

    sql = f"""
    WITH combined AS (
        {union_sql}
    )
    SELECT type, name, description, core_emotional_logic,
           1 - (text_embedding <=> %s::vector) AS similarity
    FROM combined
    WHERE text_embedding IS NOT NULL
    ORDER BY similarity DESC
    LIMIT %s;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (vec, top_k))
        rows = cur.fetchall()

    return [
        {
            "type":                row[0],
            "name":                row[1],
            "description":         row[2],
            "core_emotional_logic": row[3],
            "similarity":          float(row[4]),
        }
        for row in rows
    ]
