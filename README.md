# IdeAgent

> **An AI agent for creator content idea generation, grounded in real data — not LLM memory.**

IdeAgent helps short-film and reel creators plan content built around movies, characters, and music. Given a character, movie, or song, it recommends fitting pairings (song, style, structure) grounded in live trend data and retrieved facts, returning a **ranked list of suggestions with rationale** — never a single definitive answer.

**Team**: Tejas Bajaj, Aditi Pandey, Sinchana  
**Scope**: Course project, 6–8 weeks  
**Base paper**: TTMR++ (Doh, Lee, Jeong, Nam — ICASSP 2024)

---

## Table of Contents

- [Core Design Principle](#core-design-principle)
- [Data Model](#data-model)
- [Enrichment Pipeline](#enrichment-pipeline)
- [Live Trend Layer](#live-trend-layer)
- [Matching Methodology](#matching-methodology)
- [Model Contributions](#model-contributions)
- [Scoring Function](#scoring-function)
- [Database](#database)
- [Evaluation](#evaluation)
- [Relation to Base Paper](#relation-to-base-paper)
- [Feasibility Plan](#feasibility-plan)
- [Design Decisions: What Was Explicitly Rejected](#design-decisions-what-was-explicitly-rejected)

---

## Core Design Principle

> **The LLM is a synthesis and reasoning layer — never the source of truth for current information.**

Relying on an LLM's memory for "what's trending" or "what this character is about" causes staleness and hallucination. IdeAgent's pipeline is:

```
Retrieve grounded facts (APIs, search, structured metadata)
    -> LLM synthesizes enriched descriptions from those facts
        -> Embed & match via vector similarity
            -> LLM reasons over the shortlist
                -> Ranked output with rationale
```

The LLM never authors facts from scratch — it only synthesizes and reasons over retrieved data.

---

## Data Model

The schema is **hierarchical**, not a flat entity list. This distinction is critical.

### Movie (top-level parent)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `title` | text | Movie title |
| `description` | text | Enriched description (synthesized from TMDB/Wikipedia) |
| `embedding` | vector | Text embedding of the description |

### Character (child of Movie)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `movie_id` | UUID FK -> Movie | Parent movie |
| `description` | text | **Individual traits only** — never relational logic |
| `embedding` | vector | Text embedding of the description |

### Relationship (child of Movie, references exactly two Characters)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `movie_id` | UUID FK -> Movie | Parent movie |
| `character_ids` | UUID[2] | Exactly two character references |
| `description` | text | Relational/narrative logic between the two characters |
| `embedding` | vector | Text embedding of the description |

### Song (standalone, top-level)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `description` | text | Enriched description (synthesized from Spotify metadata + search) |
| `embedding` | vector | Text embedding of the description |
| `trend_score` | float | Current decay-weighted trend signal |
| `trend_updated_at` | timestamp | Last trend refresh time |

### Critical Design Rule: The Relational Logic Boundary

Relational logic (e.g., "loves them but stays distant to protect them") must **never** appear in a Character's own `description`. It belongs **strictly on the Relationship record**.

This matters because:
- A query for a character alone should not surface matches that only make sense given a specific relationship.
- Character embeddings reflect what is true of that character in isolation.
- Relationship embeddings reflect what is true of the dynamic between two characters.

---

## Enrichment Pipeline

Every entity type (Movie, Character, Relationship, Song) goes through the same **4-step offline enrichment process**. This runs once per entity, is cached, and is **never re-run live at query time**.

```
Step 1: Input
  Just a name — e.g. "Tony Stark", "Interstellar", "Blinding Lights"

Step 2: Search (retrieve grounded facts)
  Movies/Characters: TMDB, Wikipedia, Fandom wikis, TV Tropes
  Songs:             Spotify API (audio features), trending-audio APIs

Step 3: LLM Synthesis
  An LLM synthesizes the raw search results into a structured description.
  Always grounded in what was retrieved — never from the LLM's internal knowledge.
  Critically, the output includes a "core emotional logic" field:
    -> One sentence capturing the central emotional decision or tension.
    -> This enables deep matching, not just mood/genre tag matching.

Step 4: Embed
  The enriched description is embedded using a shared text embedding model.
  Same model for both songs and character/movie entities — both sides are text.
```

### Why "core emotional logic" matters

Generic mood/genre tags (e.g., "melancholic", "hopeful") produce shallow matches — many songs and characters share the same mood without sharing any deeper resonance. The `core_emotional_logic` field (e.g., "chooses to let go in order to give someone a chance at a better future") enables the system to find matches that share a genuine emotional decision, not just a surface-level energy.

---

## Live Trend Layer

Trending signals (audio trends, sports events, movie releases) need to refresh fast and cannot go through the heavy LLM enrichment pipeline. They are handled separately via a **decay-weighted trend log**.

### Decay formula

```
T(c, t) = T_0 * e^(-k*(t - t_0))
```

Where:
- `T_0` — initial trend score when the signal was captured
- `t_0` — timestamp when the trend was recorded
- `t`   — current time
- `k`   — decay constant (controls how fast trends fade)

Old trends fade automatically — no manual pruning required. The `trend_score` on each Song record reflects the current decayed value.

---

## Matching Methodology: Retrieve-Then-Reason

### Phase 1: Broad Retrieval
- Vector similarity search over all candidate embeddings (top-K candidates)
- Similarity score is the primary signal
- Boosted by the live `trend_score` from the trend layer

### Phase 2: LLM Reasoning over the Shortlist
- The top-K candidates are passed to an LLM with both `core_emotional_logic` strings (query entity vs. candidate)
- The LLM scores each pair on a structured rubric (0–1 alignment), with written justification
- Distinguishes deep matches (shared emotional decision) from shallow matches (shared surface trait or energy only)

### Output
A **ranked list** of suggestions, each with a written rationale. Never a single "the one" answer.

---

## Model Contributions

Three model-level contributions differentiate IdeAgent from a simple embedding similarity baseline.

### 1. Heterogeneous Graph-Attention Fusion (HGAF)

The Movie / Character / Relationship / Song schema is treated as a **heterogeneous graph**. A Character's final embedding is computed via a Graph Attention Network (PyTorch Geometric GATConv) that attends over its Movie and Relationship neighbors.

This means a Character's embedding is informed by its narrative context — without embedding relational logic directly into its text description.

Math (standard GAT):
```
Attention logit:   e_ij = LeakyReLU(a^T [W*e_i || W*e_j])
Attention weight:  alpha_ij = softmax_j(e_ij)
Node update:       h_i = sigma(sum_j alpha_ij * W*e_j)
```

### 2. Decay-Weighted Temporal Trend Fusion

The exponential decay trend score `T(c, t)` is integrated directly into the final scoring function as a weighted component — not used as a metadata filter or binary flag.

### 3. Narrative-Logic-Conditioned Reasoning Score

A single structured, rubric-based LLM call that compares two `core_emotional_logic` strings and outputs a 0–1 score with justification.

> Scope note: A trained cross-encoder was considered and rejected as infeasible for a 6–8 week / 3-person project. A prompted LLM scoring approach delivers the same capability at reasonable cost.

---

## Scoring Function

```
Score(q, c) = lambda_1 * cos(h_q, h_c)  +  lambda_2 * T(c, t)  +  lambda_3 * R(logic_q, logic_c)
```

| Term | Description |
|------|-------------|
| `cos(h_q, h_c)` | Cosine similarity between GAT-fused embeddings of query and candidate |
| `T(c, t)` | Decay-weighted trend score of the candidate |
| `R(logic_q, logic_c)` | Narrative-logic reasoning score (0–1, from prompted LLM) |
| `lambda_1, lambda_2, lambda_3` | Weights calibrated against hand-labeled validation set (not hardcoded) |

Weights are calibrated against ~30–50 hand-labeled (query, candidate) pairs with known-good alignment judgements.

---

## Database

**PostgreSQL + pgvector** — chosen over dedicated vector databases (Pinecone, Chroma, Qdrant).

### Why PostgreSQL over a vector-only DB?

The schema has real relational structure:
- `Character.movie_id -> Movie.id`
- `Relationship.movie_id -> Movie.id`
- `Relationship.character_ids[2] -> Character.id`

Using a dedicated vector DB would require syncing IDs across two systems. PostgreSQL + pgvector handles joins, vector search, and trend filtering in a single query.

**Indexing**: HNSW index on every embedding column.

**Scale note**: Chroma is acceptable for early prototyping. Pinecone/Qdrant are the right answer for production scale. For this project, pgvector is the correct tradeoff.

---

## Evaluation

**Metric**: Precision@k on a hand-labeled validation set (~30–50 pairs).

**Baseline**: Cosine similarity only (no HGAF, no trend scoring, no reasoning scorer).

**Full pipeline**: HGAF-fused embeddings + trend score + narrative-logic reasoning score.

The validation set consists of hand-labeled (query entity, candidate song) pairs where the correct match is known. Precision@k measures how often a known-good match appears in the top-k results.

---

## Relation to Base Paper

**TTMR++** — *"Enriching Music Descriptions with a Finetuned-LLM and Metadata for Text-to-Music Retrieval"*  
Doh, Lee, Jeong, Nam — ICASSP 2024  
[arXiv:2410.03264](https://arxiv.org/abs/2410.03264) | [Code](https://github.com/seungheondoh/music-text-representation-pp)

TTMR++ enriches sparse song metadata into rich text descriptions via a finetuned LLM, then performs text-to-music retrieval via a contrastively-trained cross-modal encoder.

### What IdeAgent inherits
- The LLM-enrichment technique: turning sparse metadata into rich text descriptions for retrieval.

### How IdeAgent extends TTMR++
| Dimension | TTMR++ | IdeAgent |
|-----------|--------|----------|
| Entity types | Songs only | Movies, Characters, Relationships, Songs |
| Knowledge source | Static | Static (entities) + live trend signals |
| Output | Retrieval ranking | Generative content ideas with rationale |
| Graph structure | None | Heterogeneous graph (HGAF) |
| Trend integration | None | Decay-weighted temporal fusion |
| Reasoning | Embedding similarity | Narrative-logic-conditioned LLM scoring |

---

## Feasibility Plan

| Week | Milestone |
|------|-----------|
| 1–2 | Schema + pgvector setup; data collection (~50–100 movies/characters/relationships, ~100 songs); enrichment pipeline |
| 3–4 | HGAF fusion layer (PyTorch Geometric); wire into retrieval; cosine-only baseline |
| 5 | Trend decay scoring + combined score integration |
| 6 | Prompted reasoning scorer; simple demo interface |
| 7 | Build ~30–50 hand-labeled validation pairs; measure Precision@k vs baseline |
| 8 | Buffer, polish, report and demo prep |

---

## Design Decisions: What Was Explicitly Rejected

| Decision | What Was Rejected | Why |
|----------|------------------|-----|
| Reasoning scorer | Training a custom cross-encoder from scratch | Too expensive for 6–8 week / 3-person scope |
| Character descriptions | Including relational logic in a Character's own description | Leaks relationship-specific context into individual entity embeddings; breaks character-only queries |
| Trend data | Relying on LLM memory for "what's trending" | LLM knowledge is static; causes staleness and hallucination |
| Output format | Returning a single "best" recommendation | Definitive answers are false precision; ranked list is correct |
| Vector database | Pinecone / Chroma / Qdrant as primary store | Requires ID syncing across two systems; pgvector handles joins + vector search + trend filtering together |
