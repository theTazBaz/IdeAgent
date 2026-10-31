import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def deduplicate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set in .env")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    print("=== DEDUPLICATION REPORT ===")

    # -------------------------------------------------------------
    # 1. Deduplicate Characters
    # -------------------------------------------------------------
    cur.execute("""
        SELECT movie_id, LOWER(name), COUNT(*) 
        FROM characters 
        GROUP BY movie_id, LOWER(name) 
        HAVING COUNT(*) > 1
    """)
    char_dup_groups = cur.fetchall()
    print(f"Found {len(char_dup_groups)} duplicated character groups.")

    total_chars_deleted = 0
    for movie_id, lower_name, count in char_dup_groups:
        cur.execute("""
            SELECT id, text_embedding IS NOT NULL as has_emb, created_at
            FROM characters
            WHERE movie_id = %s AND LOWER(name) = %s
            ORDER BY (text_embedding IS NOT NULL) DESC, created_at ASC
        """, (movie_id, lower_name))
        rows = cur.fetchall()
        canonical_id = rows[0][0]
        dup_ids = [r[0] for r in rows[1:]]

        for dup_id in dup_ids:
            # Re-point relationships
            cur.execute("""
                UPDATE relationships SET character_id_a = %s WHERE character_id_a = %s
            """, (canonical_id, dup_id))
            cur.execute("""
                UPDATE relationships SET character_id_b = %s WHERE character_id_b = %s
            """, (canonical_id, dup_id))
            # Delete dup character
            cur.execute("DELETE FROM characters WHERE id = %s", (dup_id,))
            total_chars_deleted += 1

    print(f"Deleted {total_chars_deleted} duplicate character rows.")

    # -------------------------------------------------------------
    # 2. Deduplicate Relationships
    # -------------------------------------------------------------
    cur.execute("""
        SELECT movie_id, LEAST(character_id_a, character_id_b), GREATEST(character_id_a, character_id_b), COUNT(*)
        FROM relationships
        GROUP BY movie_id, LEAST(character_id_a, character_id_b), GREATEST(character_id_a, character_id_b)
        HAVING COUNT(*) > 1
    """)
    rel_dup_groups = cur.fetchall()
    print(f"Found {len(rel_dup_groups)} duplicated relationship groups.")

    total_rels_deleted = 0
    for movie_id, char_min, char_max, count in rel_dup_groups:
        cur.execute("""
            SELECT id, text_embedding IS NOT NULL as has_emb, created_at
            FROM relationships
            WHERE movie_id = %s 
              AND LEAST(character_id_a, character_id_b) = %s
              AND GREATEST(character_id_a, character_id_b) = %s
            ORDER BY (text_embedding IS NOT NULL) DESC, created_at ASC
        """, (movie_id, char_min, char_max))
        rows = cur.fetchall()
        canonical_id = rows[0][0]
        dup_ids = [r[0] for r in rows[1:]]

        for dup_id in dup_ids:
            cur.execute("DELETE FROM relationships WHERE id = %s", (dup_id,))
            total_rels_deleted += 1

    print(f"Deleted {total_rels_deleted} duplicate relationship rows.")

    # -------------------------------------------------------------
    # 3. Deduplicate Songs
    # -------------------------------------------------------------
    cur.execute("""
        SELECT LOWER(title), LOWER(artist), COUNT(*)
        FROM songs
        GROUP BY LOWER(title), LOWER(artist)
        HAVING COUNT(*) > 1
    """)
    song_dup_groups = cur.fetchall()
    print(f"Found {len(song_dup_groups)} duplicated song groups.")

    total_songs_deleted = 0
    for lower_title, lower_artist, count in song_dup_groups:
        cur.execute("""
            SELECT id, text_embedding IS NOT NULL as has_emb, created_at
            FROM songs
            WHERE LOWER(title) = %s AND LOWER(artist) = %s
            ORDER BY (text_embedding IS NOT NULL) DESC, created_at ASC
        """, (lower_title, lower_artist))
        rows = cur.fetchall()
        canonical_id = rows[0][0]
        dup_ids = [r[0] for r in rows[1:]]

        for dup_id in dup_ids:
            cur.execute("DELETE FROM songs WHERE id = %s", (dup_id,))
            total_songs_deleted += 1

    print(f"Deleted {total_songs_deleted} duplicate song rows.")

    # Commit the cleanups
    conn.commit()

    # -------------------------------------------------------------
    # 4. Enforce Unique Constraints in Postgres
    # -------------------------------------------------------------
    print("\nApplying unique indexes to prevent future duplicates...")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_movies_title ON movies (LOWER(title));")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_characters_movie_name ON characters (movie_id, LOWER(name));")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_relationships_pair ON relationships (movie_id, LEAST(character_id_a, character_id_b), GREATEST(character_id_a, character_id_b));")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_songs_title_artist ON songs (LOWER(title), LOWER(artist));")
    conn.commit()
    print("Unique indexes successfully created in PostgreSQL!")

    # Final summary counts
    cur.execute("""
        SELECT 'movies', COUNT(*) FROM movies
        UNION ALL SELECT 'characters', COUNT(*) FROM characters
        UNION ALL SELECT 'relationships', COUNT(*) FROM relationships
        UNION ALL SELECT 'songs', COUNT(*) FROM songs
    """)
    print("\n=== FINAL DEDUPLICATED COUNTS ===")
    for tbl, count in cur.fetchall():
        print(f"  {tbl:<15}: {count}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    deduplicate()

