"""
pipeline/db.py
==============
PostgreSQL + pgvector connection and upsert helpers.

Uses psycopg2 (more broadly compatible than psycopg3 on msys2/MinGW Python).
pgvector adapter: pip install pgvector  (works with both psycopg2 and psycopg3).

All upsert functions are idempotent — safe to re-run on already-enriched
entities. If an entity already exists and has a text_embedding, the runner
will skip it before calling here, but the ON CONFLICT clause protects us
regardless.
"""
import json
from typing import Optional

import numpy as np
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector

from pipeline import config


# ------------------------------------------------------------------
# Connection factory
# ------------------------------------------------------------------
def get_conn() -> psycopg2.extensions.connection:
    """Open a new psycopg2 connection with pgvector registered."""
    db_url = config.require(
        "DATABASE_URL",
        config.DATABASE_URL,
        hint="Find it in: Supabase Dashboard → Project Settings → Database → Connection string → URI",
    )
    conn = psycopg2.connect(db_url)
    register_vector(conn)
    return conn


def _vec(embedding: list[float]) -> np.ndarray:
    """Convert a Python float list to a float32 numpy array for pgvector."""
    return np.array(embedding, dtype=np.float32)


# ------------------------------------------------------------------
# Check helpers (used by run_batch to skip already-enriched entities)
# ------------------------------------------------------------------
def is_enriched(conn: psycopg2.extensions.connection, table: str, entity_id: str) -> bool:
    """Return True if the entity has a non-NULL text_embedding in DB."""
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT 1 FROM {table} WHERE id = %s AND text_embedding IS NOT NULL",
            (entity_id,),
        )
        return cur.fetchone() is not None


def get_movie_by_title(conn: psycopg2.extensions.connection, title: str) -> Optional[str]:
    """Return movie ID if movie exists and has embedding, else None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM movies WHERE LOWER(title) = LOWER(%s) AND text_embedding IS NOT NULL LIMIT 1",
            (title,),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None


def get_character_by_name(conn: psycopg2.extensions.connection, name: str, movie_id: str) -> Optional[str]:
    """Return character ID if character exists and has embedding, else None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM characters WHERE LOWER(name) = LOWER(%s) AND movie_id = %s AND text_embedding IS NOT NULL LIMIT 1",
            (name, movie_id),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None


def get_relationship_by_chars(conn: psycopg2.extensions.connection, char_a: str, char_b: str) -> Optional[str]:
    """Return relationship ID if relationship exists and has embedding, else None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM relationships WHERE ((character_id_a = %s AND character_id_b = %s) OR (character_id_a = %s AND character_id_b = %s)) AND text_embedding IS NOT NULL LIMIT 1",
            (char_a, char_b, char_b, char_a),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None


def get_song_by_title_artist(conn: psycopg2.extensions.connection, title: str, artist: str) -> Optional[str]:
    """Return song ID if song exists and has embedding, else None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM songs WHERE LOWER(title) = LOWER(%s) AND LOWER(artist) = LOWER(%s) AND text_embedding IS NOT NULL LIMIT 1",
            (title, artist),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None


# ------------------------------------------------------------------
# Upsert: Movie
# ------------------------------------------------------------------
def upsert_movie(conn: psycopg2.extensions.connection, record: dict) -> None:
    """
    Insert or update a movie row.
    record keys: id, title, raw_facts (dict), description, core_emotional_logic, text_embedding (list[float])
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO movies
                (id, title, raw_facts, description, core_emotional_logic, text_embedding)
            VALUES
                (%(id)s, %(title)s, %(raw_facts)s, %(description)s, %(core_emotional_logic)s, %(text_embedding)s)
            ON CONFLICT (id) DO UPDATE SET
                raw_facts            = EXCLUDED.raw_facts,
                description          = EXCLUDED.description,
                core_emotional_logic = EXCLUDED.core_emotional_logic,
                text_embedding       = EXCLUDED.text_embedding
            """,
            {
                **record,
                "raw_facts": json.dumps(record["raw_facts"]),
                "text_embedding": _vec(record["text_embedding"]),
            },
        )
    conn.commit()


# ------------------------------------------------------------------
# Upsert: Character
# ------------------------------------------------------------------
def upsert_character(conn: psycopg2.extensions.connection, record: dict) -> None:
    """
    Insert or update a character row.
    record keys: id, movie_id, name, raw_facts, description, core_emotional_logic, text_embedding
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO characters
                (id, movie_id, name, raw_facts, description, core_emotional_logic, text_embedding)
            VALUES
                (%(id)s, %(movie_id)s, %(name)s, %(raw_facts)s, %(description)s, %(core_emotional_logic)s, %(text_embedding)s)
            ON CONFLICT (id) DO UPDATE SET
                raw_facts            = EXCLUDED.raw_facts,
                description          = EXCLUDED.description,
                core_emotional_logic = EXCLUDED.core_emotional_logic,
                text_embedding       = EXCLUDED.text_embedding
            """,
            {
                **record,
                "raw_facts": json.dumps(record["raw_facts"]),
                "text_embedding": _vec(record["text_embedding"]),
            },
        )
    conn.commit()


# ------------------------------------------------------------------
# Upsert: Relationship
# ------------------------------------------------------------------
def upsert_relationship(conn: psycopg2.extensions.connection, record: dict) -> None:
    """
    Insert or update a relationship row.
    record keys: id, movie_id, character_id_a, character_id_b, label,
                 raw_facts, description, core_emotional_logic, text_embedding
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO relationships
                (id, movie_id, character_id_a, character_id_b, label,
                 description, core_emotional_logic, text_embedding)
            VALUES
                (%(id)s, %(movie_id)s, %(character_id_a)s, %(character_id_b)s, %(label)s,
                 %(description)s, %(core_emotional_logic)s, %(text_embedding)s)
            ON CONFLICT (id) DO UPDATE SET
                description          = EXCLUDED.description,
                core_emotional_logic = EXCLUDED.core_emotional_logic,
                text_embedding       = EXCLUDED.text_embedding
            """,
            {
                **record,
                "text_embedding": _vec(record["text_embedding"]),
            },
        )
    conn.commit()


# ------------------------------------------------------------------
# Upsert: Song
# ------------------------------------------------------------------
def upsert_song(conn: psycopg2.extensions.connection, record: dict) -> None:
    """
    Insert or update a song row.
    record keys: id, title, artist, raw_facts, description, core_emotional_logic, text_embedding
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO songs
                (id, title, artist, raw_facts, description, core_emotional_logic, text_embedding)
            VALUES
                (%(id)s, %(title)s, %(artist)s, %(raw_facts)s, %(description)s, %(core_emotional_logic)s, %(text_embedding)s)
            ON CONFLICT (id) DO UPDATE SET
                raw_facts            = EXCLUDED.raw_facts,
                description          = EXCLUDED.description,
                core_emotional_logic = EXCLUDED.core_emotional_logic,
                text_embedding       = EXCLUDED.text_embedding
            """,
            {
                **record,
                "raw_facts": json.dumps(record["raw_facts"]),
                "text_embedding": _vec(record["text_embedding"]),
            },
        )
    conn.commit()


# ------------------------------------------------------------------
# Fetch character descriptions (used by relationship enricher)
# ------------------------------------------------------------------
def get_character(conn: psycopg2.extensions.connection, character_id: str) -> Optional[dict]:
    """Return {name, description, core_emotional_logic} for a character, or None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, description, core_emotional_logic FROM characters WHERE id = %s",
            (character_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {"name": row[0], "description": row[1], "core_emotional_logic": row[2]}
