# IdeAgent — Build Timeline

| Week | Focus | Key Deliverable |
|------|-------|----------------|
| 1 | DB setup | PostgreSQL + pgvector running, schema DDL, ~5 hand-entered seed entities |
| 2 | Enrichment pipeline | Search scrapers (TMDB, Fandom, Spotify) + LLM synthesis + embeddings stored; ~50 real enriched entities in DB |
| 3–4 | HGAF | Cosine-only baseline wired; graph built from DB; GATConv layer applied; GAT embeddings stored |
| 5 | Trend + scoring | Live trend ingestion, decay function, combined score (lambda_1*cos + lambda_2*T + lambda_3*R) |
| 6 | Reasoning + demo | LLM reasoning scorer (0-1 rubric on core_emotional_logic); thin demo interface |
| 7 | Evaluation | 30-50 hand-labeled validation pairs; Precision@k measured (baseline vs. full pipeline) |
| 8 | Buffer | Polish, report, demo prep |
