"""
pipeline/search_db.py
=====================
Database helpers for the RAG search pipeline.

Two entry points:
  - get_entity_by_name()  → exact, then fuzzy, lookup of a named entity
  - vector_search()       → pgvector cosine similarity across all tables
"""
from __future__ import annotations

import re

import psycopg2
import numpy as np

from pipeline import db, embed


# ------------------------------------------------------------------
# Name lookup (exact first, then fuzzy)
# ------------------------------------------------------------------
_LOOKUPS = [
    ("movie",        "movies",        "title"),
    ("character",    "characters",    "name"),
    ("relationship", "relationships", "label"),
    ("song",         "songs",         "title"),
]


_MIN_FUZZY_CHARS = 3     # shorter queries only match exactly
_MIN_COVERAGE = 0.5      # query words must make up at least half of the matched name


def _words(text: str) -> list[str]:
    """Lowercase words with punctuation and a leading 'the' removed."""
    n = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text.lower())
    words = n.split()
    if len(words) > 1 and words[0] == "the":
        words = words[1:]
    return words


def _normalise(name: str) -> str:
    return " ".join(_words(name))


def _fuzzy_score(query: str, candidate: str) -> float | None:
    """
    Score how well `candidate` matches `query`, or None if it isn't a match.

    Every query word must appear in the candidate as a WHOLE word (so "Up" does
    not match "Superman"), and the query words must cover at least half of the
    candidate's words (so "Up" does not match "Pump It Up"). Bracketed parts of
    the candidate such as "(feat. X)" are ignored when counting.
    """
    q = _words(query)
    if not q or len(" ".join(q)) < _MIN_FUZZY_CHARS:
        return None
    c = _words(re.sub(r"[\(\[].*?[\)\]]", " ", candidate))
    if not c or not all(w in c for w in q):
        return None
    coverage = len(set(q)) / len(set(c))
    return coverage if coverage >= _MIN_COVERAGE else None


def get_entity_by_name(conn: psycopg2.extensions.connection, name: str) -> dict | None:
    """
    Find one entity (movie, character, relationship or song) matching `name`.

    Tries a case-insensitive exact match across all tables first, then a
    whole-word fuzzy match ("Joker" ~ "The Joker", "Dr Brand" ~ "Dr. Amelia
    Brand"; see _fuzzy_score). The best-covering, then shortest, name wins.

    Returns a dict with keys: id, type, name, description, core_emotional_logic
    or None if nothing is found.
    """
    with conn.cursor() as cur:
        # Pass 1: exact (case-insensitive)
        for entity_type, table, col in _LOOKUPS:
            cur.execute(
                f"SELECT id, {col}, description, core_emotional_logic FROM {table} "
                f"WHERE LOWER({col}) = LOWER(%s) LIMIT 1",
                (name,),
            )
            row = cur.fetchone()
            if row:
                return _row_to_entity(entity_type, row)

        # Pass 2: fuzzy — whole-word match, scored by how much of the name the query covers
        tokens = _words(name)
        if not tokens or len(" ".join(tokens)) < _MIN_FUZZY_CHARS:
            return None
        best = None  # ((coverage, -len(name)), entity)
        for entity_type, table, col in _LOOKUPS:
            cond = " AND ".join([f"LOWER({col}) LIKE %s"] * len(tokens))
            cur.execute(
                f"SELECT id, {col}, description, core_emotional_logic FROM {table} "
                f"WHERE {col} IS NOT NULL AND {cond}",
                [f"%{t}%" for t in tokens],
            )
            for row in cur.fetchall():
                score = _fuzzy_score(name, row[1])
                if score is None:
                    continue
                key = (score, -len(row[1]))
                if best is None or key > best[0]:
                    best = (key, _row_to_entity(entity_type, row))
        return best[1] if best else None


def _row_to_entity(entity_type: str, row: tuple) -> dict:
    return {
        "id":                  str(row[0]),
        "type":                entity_type,
        "name":                row[1],
        "description":         row[2],
        "core_emotional_logic": row[3],
    }


# ------------------------------------------------------------------
# Vector similarity search
# ------------------------------------------------------------------
def vector_search(
    conn: psycopg2.extensions.connection,
    query_text: str,
    filter_type: str | None = None,
    top_k: int = 5,
    exclude_id: str | None = None,
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
        exclude_id:  Optional – id of an entity to leave out (the reference
                     entity, so it doesn't come back as its own match).

    Returns:
        List of dicts: {type, name, description, core_emotional_logic, similarity}
    """
    query_vec = embed.embed_text(query_text, is_query=True)
    vec = db._vec(query_vec)

    # Build the UNION ALL query — optionally filter to one table
    subqueries = {
        "movies":        "SELECT id, 'movie'        AS type, title        AS name, description, core_emotional_logic, text_embedding FROM movies",
        "characters":    "SELECT id, 'character'    AS type, name         AS name, description, core_emotional_logic, text_embedding FROM characters",
        "relationships": "SELECT id, 'relationship' AS type, label        AS name, description, core_emotional_logic, text_embedding FROM relationships",
        "songs":         "SELECT id, 'song'         AS type, title || ' — ' || artist AS name, description, core_emotional_logic, text_embedding FROM songs",
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
      AND (%s::text IS NULL OR id::text <> %s)
    ORDER BY similarity DESC
    LIMIT %s;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (vec, exclude_id, exclude_id, top_k))
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
