"""Offline tests for pipeline/search_db.py. Run:  python tests/test_search_db.py   (no DB, no model)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import embed, search_db
from pipeline.search_db import _fuzzy_score


def test_fuzzy_matches_whole_words_only():
    assert _fuzzy_score("Joker", "The Joker") == 1.0
    assert _fuzzy_score("the joker", "The Joker") == 1.0
    assert _fuzzy_score("Dr Brand", "Dr. Amelia Brand") is not None
    assert _fuzzy_score("Hawayein", 'Hawayein (From "Jab Harry Met Sejal")') == 1.0
    for q, c in [("Up", "Superman"), ("Her", "Hermione"), ("Her", "Mother"), ("Joker", "OK"), ("Up", "Pump It Up")]:
        assert _fuzzy_score(q, c) is None, (q, c)
    assert _fuzzy_score("it", "It") is None            # too short to fuzzy-match


class FakeCursor:
    """Answers the two queries vector_search makes."""

    def __init__(self, rows, excluded_rows):
        self.rows, self.excluded_rows, self.last = rows, excluded_rows, None

    def __enter__(self): return self
    def __exit__(self, *a): return False

    def execute(self, sql, params=None):
        self.last = "lookup" if "WHERE id::text = %s" in sql else "search"
        self.params = params

    def fetchall(self):
        return self.excluded_rows if self.last == "lookup" else self.rows


class FakeConn:
    def __init__(self, rows, excluded_rows=()):
        self.cur = FakeCursor(rows, list(excluded_rows))

    def cursor(self): return self.cur


def _row(name, sim, t="song"):
    return (t, name, "desc", "logic", sim)


def test_repeated_rows_are_collapsed_and_top_k_is_still_filled():
    embed.embed_text = lambda text, is_query=False: [0.0] * 768
    rows = [_row("A — X", .9), _row("A — X", .9), _row("A — X", .89), _row("B — Y", .8), _row("C — Z", .7), _row("D — W", .6)]
    out = search_db.vector_search(FakeConn(rows), "q", top_k=3)
    assert [r["name"] for r in out] == ["A — X", "B — Y", "C — Z"]
    assert out[0]["similarity"] == 0.9                       # the best-scoring copy is the one kept


def test_all_copies_of_the_reference_entity_are_excluded():
    embed.embed_text = lambda text, is_query=False: [0.0] * 768
    rows = [_row("Alfred", .9, "character"), _row("Alfred", .88, "character"), _row("Bruce", .8, "character")]
    conn = FakeConn(rows, excluded_rows=[("character", "Alfred")])
    out = search_db.vector_search(conn, "q", top_k=5, exclude_id="some-id")
    assert [r["name"] for r in out] == ["Bruce"]


def test_same_name_in_different_tables_is_not_a_duplicate():
    embed.embed_text = lambda text, is_query=False: [0.0] * 768
    rows = [_row("Coco", .9, "movie"), _row("Coco", .8, "character")]
    assert len(search_db.vector_search(FakeConn(rows), "q", top_k=5)) == 2


def test_fetches_extra_rows_to_make_up_for_duplicates():
    embed.embed_text = lambda text, is_query=False: [0.0] * 768
    conn = FakeConn([_row("A", .9)])
    search_db.vector_search(conn, "q", top_k=4)
    assert conn.cur.params[-1] == 4 * search_db._DUP_FACTOR


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  ", fn.__name__)
    print(f"{len(fns)} tests passed")
