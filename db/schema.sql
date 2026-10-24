-- =============================================================================
-- IdeAgent — PostgreSQL + pgvector Schema
-- Embedding model : nomic-embed-text-v1.5  (768 dims)
-- Run this in Supabase SQL Editor (Project → SQL Editor → New Query)
-- =============================================================================

-- 0. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;


-- =============================================================================
-- 1. MOVIES  (top-level parent)
-- =============================================================================
CREATE TABLE IF NOT EXISTS movies (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title                TEXT        NOT NULL,
    raw_facts            JSONB,                          -- raw search results (TMDB, Wikipedia)
    description          TEXT,                          -- LLM-synthesized enriched description
    core_emotional_logic TEXT,                          -- one-sentence central tension/decision
    text_embedding       vector(768),                   -- nomic-embed-text-v1.5 of description
    gat_embedding        vector(768),                   -- populated by HGAF step (Week 3-4), NULL until then
    created_at           TIMESTAMPTZ DEFAULT now()
);


-- =============================================================================
-- 2. CHARACTERS  (child of Movie)
-- Rule: description holds ONLY individual traits — never relational logic
-- =============================================================================
CREATE TABLE IF NOT EXISTS characters (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id             UUID        NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    name                 TEXT        NOT NULL,
    raw_facts            JSONB,
    description          TEXT,                          -- individual traits only
    core_emotional_logic TEXT,
    text_embedding       vector(768),
    gat_embedding        vector(768),                   -- NULL until HGAF step
    created_at           TIMESTAMPTZ DEFAULT now()
);


-- =============================================================================
-- 3. RELATIONSHIPS  (child of Movie, references exactly two Characters)
-- Holds all relational/narrative logic between two characters
-- =============================================================================
CREATE TABLE IF NOT EXISTS relationships (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id             UUID        NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    character_id_a       UUID        NOT NULL REFERENCES characters(id),
    character_id_b       UUID        NOT NULL REFERENCES characters(id),
    label                TEXT,                          -- e.g. "Batman & Joker"
    description          TEXT,                          -- relational logic between the two
    core_emotional_logic TEXT,
    text_embedding       vector(768),
    gat_embedding        vector(768),
    created_at           TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT different_characters CHECK (character_id_a <> character_id_b)
);


-- =============================================================================
-- 4. SONGS  (standalone, top-level — not nested under any movie)
-- =============================================================================
CREATE TABLE IF NOT EXISTS songs (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title                TEXT        NOT NULL,
    artist               TEXT        NOT NULL,
    raw_facts            JSONB,
    description          TEXT,
    core_emotional_logic TEXT,
    text_embedding       vector(768),
    -- Trend columns: logic deferred to Week 5
    -- trend_score: last raw value fetched from trending API (can rise or fall)
    -- trend_refreshed_at: when it was last fetched; staleness discount applied at query time
    trend_score          FLOAT,
    trend_refreshed_at   TIMESTAMPTZ,
    created_at           TIMESTAMPTZ DEFAULT now()
);


-- =============================================================================
-- 5. INDEXES
-- =============================================================================

-- HNSW vector indexes (approximate nearest-neighbor search)
-- text_embedding: used from Week 2 onward (cosine baseline)
-- gat_embedding: used from Week 4 onward (after HGAF fusion)

CREATE INDEX IF NOT EXISTS idx_movies_text_emb       ON movies       USING hnsw (text_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_movies_gat_emb        ON movies       USING hnsw (gat_embedding  vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_characters_text_emb   ON characters   USING hnsw (text_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_characters_gat_emb    ON characters   USING hnsw (gat_embedding  vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_relationships_text_emb ON relationships USING hnsw (text_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_relationships_gat_emb  ON relationships USING hnsw (gat_embedding  vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_songs_text_emb        ON songs        USING hnsw (text_embedding vector_cosine_ops);

-- B-tree indexes for FK joins
CREATE INDEX IF NOT EXISTS idx_characters_movie_id       ON characters    (movie_id);
CREATE INDEX IF NOT EXISTS idx_relationships_movie_id    ON relationships (movie_id);
CREATE INDEX IF NOT EXISTS idx_relationships_char_a      ON relationships (character_id_a);
CREATE INDEX IF NOT EXISTS idx_relationships_char_b      ON relationships (character_id_b);
