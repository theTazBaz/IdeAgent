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
import re
import time
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from tqdm import tqdm
import psycopg2

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


def _register_movie(entry: dict, uuid_val: str, actual_title: str = "") -> None:
    """Register all possible placeholder variations for a movie."""
    title = entry.get("title", "")
    if "placeholder" in entry:
        _id_registry[entry["placeholder"]] = uuid_val
    if title in _MOVIE_PLACEHOLDER:
        _id_registry[_MOVIE_PLACEHOLDER[title]] = uuid_val
    _id_registry[title] = uuid_val
    slug = re.sub(r"[^a-zA-Z0-9]", "", title).lower()
    _id_registry[f"_NEEDS_MOVIE_ID_{slug}"] = uuid_val
    if actual_title and actual_title != title:
        _id_registry[actual_title] = uuid_val
        actual_slug = re.sub(r"[^a-zA-Z0-9]", "", actual_title).lower()
        _id_registry[f"_NEEDS_MOVIE_ID_{actual_slug}"] = uuid_val


def _register_character(entry: dict, uuid_val: str) -> None:
    """Register all possible placeholder variations for a character."""
    name = entry.get("name", "")
    movie_title = entry.get("movie_title", "")
    if "placeholder" in entry:
        _id_registry[entry["placeholder"]] = uuid_val
    if name in _CHAR_PLACEHOLDER:
        _id_registry[_CHAR_PLACEHOLDER[name]] = uuid_val
    _id_registry[name] = uuid_val
    if movie_title:
        _id_registry[f"{name} ({movie_title})"] = uuid_val
    slug = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    _id_registry[f"_NEEDS_ID_{slug}"] = uuid_val
    # Also register first & last name slugs if applicable
    parts = name.split()
    if parts:
        first_slug = re.sub(r"[^a-zA-Z0-9]", "", parts[0]).lower()
        _id_registry[f"_NEEDS_ID_{first_slug}"] = uuid_val
        last_slug = re.sub(r"[^a-zA-Z0-9]", "", parts[-1]).lower()
        _id_registry[f"_NEEDS_ID_{last_slug}"] = uuid_val


def _resolve(value: str, conn: psycopg2.extensions.connection | None = None) -> str:
    """
    Resolve a _NEEDS_* placeholder to a real UUID from the registry or DB fallback.
    Returns the value unchanged if it's already a real UUID (no underscore prefix).
    """
    if isinstance(value, str) and (value.startswith("_NEEDS_") or value in _id_registry):
        resolved = _id_registry.get(value)
        if resolved is None:
            # Case-insensitive fallback
            for k, v in _id_registry.items():
                if k.lower() == value.lower():
                    resolved = v
                    break
        if resolved is None and conn is not None:
            # Fallback to DB lookup if placeholder matches movie or char
            clean = value.replace("_NEEDS_MOVIE_ID_", "").replace("_NEEDS_ID_", "")
            m_id = db.get_movie_by_title(conn, clean)
            if m_id:
                _id_registry[value] = m_id
                return m_id
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


def _ensure_conn(conn: psycopg2.extensions.connection) -> psycopg2.extensions.connection:
    """Return an active DB connection, reconnecting if dropped by pooler."""
    if conn is None or getattr(conn, "closed", 1):
        return db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return db.get_conn()


def run(batch_path: Path, dry_run: bool = False, only: str | None = None) -> None:
    batch = load_batch(batch_path)

    only_set = set(only.lower().split(",")) if only else None

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
    movies = batch.get("movies", []) if (only_set is None or "movies" in only_set or "film" in only_set) else []
    if movies:
        print(f"🎬  Movies ({len(movies)} entries)")
    for entry in tqdm(movies, desc="  Movies", unit="movie"):
        for attempt in range(3):
            try:
                conn = _ensure_conn(conn)
                entity_id = entry.get("id")
                existing_id = entity_id if (entity_id and db.is_enriched(conn, "movies", entity_id)) else db.get_movie_by_title(conn, entry["title"])
                if existing_id:
                    tqdm.write(f"  ⏭  Skip (already enriched): {entry['title']}")
                    skipped += 1
                    # Still register the ID so characters can reference it
                    _register_movie(entry, existing_id)
                    break
                tqdm.write(f"\n→ Enriching movie: {entry['title']}")
                record = enrich_movie(conn, title=entry["title"], movie_id=entity_id)
                done += 1
                # Register the new UUID for downstream use
                _register_movie(entry, record["id"], record.get("title", ""))
                time.sleep(4.2)
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as conn_err:
                tqdm.write(f"  🔄  DB connection drop: {conn_err} — reconnecting (attempt {attempt+1}/3)")
                time.sleep(2.0)
                conn = db.get_conn()
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn = _ensure_conn(conn)
                tqdm.write(f"  ❌  FAILED: {entry['title']} — {e}")
                break

    # ------------------------------------------------------------------
    # 2. Characters  (after movies — same conn, movie rows now exist)
    # ------------------------------------------------------------------
    characters = batch.get("characters", []) if (only_set is None or "characters" in only_set or "film" in only_set) else []
    if characters:
        print(f"\n🧑  Characters ({len(characters)} entries)")
    for entry in tqdm(characters, desc="  Characters", unit="char"):
        for attempt in range(3):
            try:
                conn = _ensure_conn(conn)
                entity_id = entry.get("id")
                try:
                    movie_id = _resolve(entry["movie_id"], conn)
                except ValueError as e:
                    tqdm.write(f"  ⏭  Skip (dependency not met): {entry['name']} — {e}")
                    skipped += 1
                    break
                existing_id = entity_id if (entity_id and db.is_enriched(conn, "characters", entity_id)) else db.get_character_by_name(conn, entry["name"], movie_id)
                if existing_id:
                    tqdm.write(f"  ⏭  Skip (already enriched): {entry['name']}")
                    skipped += 1
                    # Still register for downstream relationships
                    _register_character(entry, existing_id)
                    break
                tqdm.write(f"\n→ Enriching character: {entry['name']} ({entry['movie_title']})")
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
                _register_character(entry, record["id"])
                time.sleep(4.2)
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as conn_err:
                tqdm.write(f"  🔄  DB connection drop: {conn_err} — reconnecting (attempt {attempt+1}/3)")
                time.sleep(2.0)
                conn = db.get_conn()
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn = _ensure_conn(conn)
                tqdm.write(f"  ❌  FAILED: {entry['name']} — {e}")
                break

    # ------------------------------------------------------------------
    # 3. Relationships  (after characters)
    # ------------------------------------------------------------------
    relationships = batch.get("relationships", []) if (only_set is None or "relationships" in only_set or "film" in only_set) else []
    if relationships:
        print(f"\n🔗  Relationships ({len(relationships)} entries)")
    for entry in tqdm(relationships, desc="  Relationships", unit="rel"):
        for attempt in range(3):
            try:
                conn = _ensure_conn(conn)
                entity_id = entry.get("id")
                try:
                    char_a = _resolve(entry["character_id_a"], conn)
                    char_b = _resolve(entry["character_id_b"], conn)
                    movie_id = _resolve(entry["movie_id"], conn)
                except ValueError as e:
                    tqdm.write(f"  ⏭  Skip (dependencies not met): {entry['label']} — {e}")
                    skipped += 1
                    break
                existing_id = entity_id if (entity_id and db.is_enriched(conn, "relationships", entity_id)) else db.get_relationship_by_chars(conn, char_a, char_b)
                if existing_id:
                    tqdm.write(f"  ⏭  Skip (already enriched): {entry['label']}")
                    skipped += 1
                    break
                tqdm.write(f"\n→ Enriching relationship: {entry['label']}")
                enrich_relationship(
                    conn,
                    character_id_a=char_a,
                    character_id_b=char_b,
                    movie_id=movie_id,
                    label=entry["label"],
                    relationship_id=entity_id,
                    search_query=entry.get("search_query"),
                )
                done += 1
                time.sleep(4.2)
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as conn_err:
                tqdm.write(f"  🔄  DB connection drop: {conn_err} — reconnecting (attempt {attempt+1}/3)")
                time.sleep(2.0)
                conn = db.get_conn()
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn = _ensure_conn(conn)
                tqdm.write(f"  ❌  FAILED: {entry['label']} — {e}")
                break

    # ------------------------------------------------------------------
    # 4. Songs  (fully independent)
    # ------------------------------------------------------------------
    songs = batch.get("songs", []) if (only_set is None or "songs" in only_set or "music" in only_set) else []
    if songs:
        print(f"\n🎵  Songs ({len(songs)} entries)")
    for entry in tqdm(songs, desc="  Songs", unit="song"):
        for attempt in range(3):
            try:
                conn = _ensure_conn(conn)
                entity_id = entry.get("id")
                existing_id = entity_id if (entity_id and db.is_enriched(conn, "songs", entity_id)) else db.get_song_by_title_artist(conn, entry["title"], entry["artist"])
                if existing_id:
                    tqdm.write(f"  ⏭  Skip (already enriched): {entry['title']} — {entry['artist']}")
                    skipped += 1
                    break
                tqdm.write(f"\n→ Enriching song: {entry['title']} — {entry['artist']}")
                enrich_song(
                    conn,
                    title=entry["title"],
                    artist=entry["artist"],
                    song_id=entity_id,
                )
                done += 1
                # Respect rate limits for Groq Qwen TPM
                time.sleep(9.5)
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as conn_err:
                tqdm.write(f"  🔄  DB connection drop: {conn_err} — reconnecting (attempt {attempt+1}/3)")
                time.sleep(2.0)
                conn = db.get_conn()
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn = _ensure_conn(conn)
                tqdm.write(f"  ❌  FAILED: {entry['title']} — {e}")
                break

    try:
        conn.close()
    except Exception:
        pass


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
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Comma-separated entities to enrich: 'movies,characters,relationships', 'film', or 'songs'",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌  Batch file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"\n🚀  IdeAgent Enrichment Pipeline")
    print(f"    Batch file : {args.input}")
    print(f"    Embed model: nomic-embed-text-v1.5 (local)")
    print(f"    LLM model  : {config.LLM_MODEL}\n")

    run(batch_path=args.input, dry_run=args.dry_run, only=args.only)


if __name__ == "__main__":
    main()
