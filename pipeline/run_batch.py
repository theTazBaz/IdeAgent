"""
pipeline/run_batch.py
=====================
CLI entry point for the Week 2 enrichment pipeline.

Usage:
    python -m pipeline.run_batch                        # uses data/batch.json
    python -m pipeline.run_batch --input data/batch.json
    python -m pipeline.run_batch --dry-run              # check DB connectivity only

Processing order (enforced):
    1. movies        → must exist before characters
    2. characters    → must exist before relationships
    3. relationships → depend on characters being in DB
    4. songs         → fully independent

Idempotency:
    Already-enriched entities (text_embedding IS NOT NULL) are skipped.
    Re-running the script is always safe.

ID Registry:
    When the pipeline enriches a new movie or character, the returned UUID is
    stored in a registry keyed by the _NEEDS_* placeholder strings used in
    batch.json. This lets character entries reference their movie_id and
    relationship entries reference character UUIDs without hard-coding them.
"""
from __future__ import annotations

import argparse
import json
import time
import sys
from pathlib import Path

from tqdm import tqdm

from pipeline import config, db
from pipeline.enrich_movie import enrich_movie
from pipeline.enrich_character import enrich_character
from pipeline.enrich_relationship import enrich_relationship
from pipeline.enrich_song import enrich_song

# Registry: placeholder_key → real UUID (populated during movie/character enrichment)
_id_registry: dict[str, str] = {}

# Mapping: movie title → placeholder key used in batch.json
_MOVIE_PLACEHOLDER: dict[str, str] = {
    "Interstellar":                      "_NEEDS_MOVIE_ID_interstellar",
    "La La Land":                        "_NEEDS_MOVIE_ID_lalaland",
    "Everything Everywhere All at Once": "_NEEDS_MOVIE_ID_eeaao",
    "Parasite":                          "_NEEDS_MOVIE_ID_parasite",
    "Coco":                              "_NEEDS_MOVIE_ID_coco",
}

# Mapping: character name → placeholder key used in batch.json
_CHAR_PLACEHOLDER: dict[str, str] = {
    "Alfred Pennyworth":  "_NEEDS_ID_alfred",
    "Cooper":             "_NEEDS_ID_cooper",
    "Murph":              "_NEEDS_ID_murph",
    "Dr. Amelia Brand":   "_NEEDS_ID_brand",
    "Mia Dolan":          "_NEEDS_ID_mia",
    "Sebastian Wilder":   "_NEEDS_ID_sebastian",
    "Evelyn Wang":        "_NEEDS_ID_evelyn",
    "Joy Wang":           "_NEEDS_ID_joy",
    "Waymond Wang":       "_NEEDS_ID_waymond",
    "Ki-woo Kim":         "_NEEDS_ID_kiwoo",
    "Park Dong-ik":       "_NEEDS_ID_park",
    "Miguel Rivera":      "_NEEDS_ID_miguel",
    "Hector Rivera":      "_NEEDS_ID_hector",
}


def _resolve(value: str) -> str:
    """
    Resolve a _NEEDS_* placeholder to a real UUID from the registry.
    Returns the value unchanged if it's already a real UUID (no underscore prefix).
    """
    if isinstance(value, str) and value.startswith("_NEEDS_"):
        resolved = _id_registry.get(value)
        if resolved is None:
            raise ValueError(
                f"Unresolved placeholder {value!r}. "
                "Make sure the entity it depends on was enriched first."
            )
        return resolved
    return value


# ------------------------------------------------------------------
# Default batch file path (relative to project root)
# ------------------------------------------------------------------
DEFAULT_BATCH = Path(__file__).parent.parent / "data" / "batch.json"


def load_batch(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(batch_path: Path, dry_run: bool = False) -> None:
    batch = load_batch(batch_path)

    print("\n🔌  Connecting to database …")
    conn = db.get_conn()
    print("  ✓  Connected.\n")

    if dry_run:
        print("✅  Dry run — DB connection OK. Exiting without enriching anything.")
        conn.close()
        return

    # Count totals for summary
    total_entities = (
        len(batch.get("movies", []))
        + len(batch.get("characters", []))
        + len(batch.get("relationships", []))
        + len(batch.get("songs", []))
    )
    done = 0
    skipped = 0

    # ------------------------------------------------------------------
    # 1. Movies
    # ------------------------------------------------------------------
    movies = batch.get("movies", [])
    if movies:
        print(f"🎬  Movies ({len(movies)} entries)")
    for entry in tqdm(movies, desc="  Movies", unit="movie"):
        entity_id = entry.get("id")
        if entity_id and db.is_enriched(conn, "movies", entity_id):
            tqdm.write(f"  ⏭  Skip (already enriched): {entry['title']}")
            skipped += 1
            # Still register the ID so characters can reference it
            placeholder = _MOVIE_PLACEHOLDER.get(entry["title"])
            if placeholder:
                _id_registry[placeholder] = entity_id
            continue
        tqdm.write(f"\n→ Enriching movie: {entry['title']}")
        try:
            record = enrich_movie(conn, title=entry["title"], movie_id=entity_id)
            done += 1
            # Register the new UUID for downstream use
            placeholder = _MOVIE_PLACEHOLDER.get(entry["title"])
            if placeholder:
                _id_registry[placeholder] = record["id"]
            time.sleep(4.2)
        except Exception as e:
            conn.rollback()
            tqdm.write(f"  ❌  FAILED: {entry['title']} — {e}")

    # ------------------------------------------------------------------
    # 2. Characters  (after movies — same conn, movie rows now exist)
    # ------------------------------------------------------------------
    characters = batch.get("characters", [])
    if characters:
        print(f"\n🧑  Characters ({len(characters)} entries)")
    for entry in tqdm(characters, desc="  Characters", unit="char"):
        entity_id = entry.get("id")
        if entity_id and db.is_enriched(conn, "characters", entity_id):
            tqdm.write(f"  ⏭  Skip (already enriched): {entry['name']}")
            skipped += 1
            # Still register for downstream relationships
            placeholder = _CHAR_PLACEHOLDER.get(entry["name"])
            if placeholder:
                _id_registry[placeholder] = entity_id
            continue
        tqdm.write(f"\n→ Enriching character: {entry['name']} ({entry['movie_title']})")
        try:
            movie_id = _resolve(entry["movie_id"])
            record = enrich_character(
                conn,
                name=entry["name"],
                movie_id=movie_id,
                movie_title=entry["movie_title"],
                character_id=entity_id,
                fandom_wiki=entry.get("fandom_wiki"),
                fandom_slug=entry.get("fandom_slug"),
            )
            done += 1
            # Register the new UUID for downstream relationships
            placeholder = _CHAR_PLACEHOLDER.get(entry["name"])
            if placeholder:
                _id_registry[placeholder] = record["id"]
            time.sleep(4.2)
        except Exception as e:
            conn.rollback()
            tqdm.write(f"  ❌  FAILED: {entry['name']} — {e}")

    # ------------------------------------------------------------------
    # 3. Relationships  (after characters)
    # ------------------------------------------------------------------
    relationships = batch.get("relationships", [])
    if relationships:
        print(f"\n🔗  Relationships ({len(relationships)} entries)")
    for entry in tqdm(relationships, desc="  Relationships", unit="rel"):
        entity_id = entry.get("id")
        if entity_id and db.is_enriched(conn, "relationships", entity_id):
            tqdm.write(f"  ⏭  Skip (already enriched): {entry['label']}")
            skipped += 1
            continue
        tqdm.write(f"\n→ Enriching relationship: {entry['label']}")
        try:
            enrich_relationship(
                conn,
                character_id_a=_resolve(entry["character_id_a"]),
                character_id_b=_resolve(entry["character_id_b"]),
                movie_id=_resolve(entry["movie_id"]),
                label=entry["label"],
                relationship_id=entity_id,
                search_query=entry.get("search_query"),
            )
            done += 1
            time.sleep(4.2)
        except Exception as e:
            conn.rollback()
            tqdm.write(f"  ❌  FAILED: {entry['label']} — {e}")

    # ------------------------------------------------------------------
    # 4. Songs  (fully independent)
    # ------------------------------------------------------------------
    songs = batch.get("songs", [])
    if songs:
        print(f"\n🎵  Songs ({len(songs)} entries)")
    for entry in tqdm(songs, desc="  Songs", unit="song"):
        entity_id = entry.get("id")
        if entity_id and db.is_enriched(conn, "songs", entity_id):
            tqdm.write(f"  ⏭  Skip (already enriched): {entry['title']} — {entry['artist']}")
            skipped += 1
            continue
        tqdm.write(f"\n→ Enriching song: {entry['title']} — {entry['artist']}")
        try:
            enrich_song(
                conn,
                title=entry["title"],
                artist=entry["artist"],
                song_id=entity_id,
            )
            done += 1
            time.sleep(4.2)
        except Exception as e:
            conn.rollback()
            tqdm.write(f"  ❌  FAILED: {entry['title']} — {e}")

    conn.close()


    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"  ✅  Done!  {done} enriched  |  {skipped} skipped  |  {total_entities} total")
    print(f"{'='*50}\n")
    print("Run this SQL in Supabase to verify embedding coverage:")
    print("""
  SELECT 'movies'        AS tbl, COUNT(*) total, COUNT(text_embedding) embedded FROM movies
  UNION ALL
  SELECT 'characters',          COUNT(*),        COUNT(text_embedding)          FROM characters
  UNION ALL
  SELECT 'relationships',       COUNT(*),        COUNT(text_embedding)          FROM relationships
  UNION ALL
  SELECT 'songs',               COUNT(*),        COUNT(text_embedding)          FROM songs;
""")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="IdeAgent enrichment pipeline — batch runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pipeline.run_batch                    # enrich everything in data/batch.json
  python -m pipeline.run_batch --dry-run          # just check DB connection
  python -m pipeline.run_batch --input my.json    # use a custom batch file
""",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_BATCH,
        help="Path to the batch JSON file (default: data/batch.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test DB connection only — do not enrich anything",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌  Batch file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"\n🚀  IdeAgent Enrichment Pipeline")
    print(f"    Batch file : {args.input}")
    print(f"    Embed model: nomic-embed-text-v1.5 (local)")
    print(f"    LLM model  : {config.LLM_MODEL}\n")

    run(batch_path=args.input, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
