"""
pipeline/eval/harness.py
========================
Collects, per query, everything the evaluation needs and caches it on disk so
that reruns are free and a rate-limited run can simply be resumed.

Per query it stores:
  intent                 step A output (shared by every variant)
  variants.naive         cosine search on the RAW query            v = f(q)
  variants.rewrite       cosine search on the LLM-rewritten query  v = f(g(q, l_ref))
  variants.rewrite+live  same, plus the live lookup for references missing from the DB
  scores                 the reasoning-scorer output for the rewrite+live shortlist

Everything read here is read-only: database SELECTs plus LLM / TMDB calls.
"""
from __future__ import annotations

import json
from pathlib import Path

from pipeline import db, llm, rag

EVAL_DIR = Path(__file__).resolve().parent
CACHE_PATH = EVAL_DIR / "cache.json"
QUERIES_PATH = EVAL_DIR / "queries.json"
POOL_PATH = EVAL_DIR / "pool.json"


def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _slim(results: list[dict]) -> list[dict]:
    return [{"name": r["name"], "type": r["type"], "similarity": r["similarity"]} for r in results]


def collect(conn, client, query: str, rec: dict | None = None) -> dict:
    """Fill in whatever is missing from `rec` for this query and return it."""
    rec = rec or {}
    variants = rec.setdefault("variants", {})

    if "intent" not in rec:
        rec["intent"] = rag.step_a_extract_intent(client, query)
    intent = rec["intent"]

    if "naive" not in variants:
        r = rag.retrieve(conn, client, query, rewrite=False, intent=intent)
        variants["naive"] = {"search_string": r["search_string"], "entity_source": None, "results": _slim(r["results"])}

    full = None  # full-text results of the final (rewrite+live) shortlist, needed to score
    if "rewrite" not in variants:
        r = rag.retrieve(conn, client, query, rewrite=True, live=False, intent=intent)
        variants["rewrite"] = {
            "search_string": r["search_string"],
            "entity_source": "database" if r["entity"] else None,
            "results": _slim(r["results"]),
        }
        full = r

    if "rewrite+live" not in variants:
        needs_live = bool(intent.get("reference_entity")) and variants["rewrite"]["entity_source"] is None
        if needs_live:
            r = rag.retrieve(conn, client, query, rewrite=True, live=True, intent=intent)
            variants["rewrite+live"] = {
                "search_string": r["search_string"],
                "entity_source": r["entity"].get("source") if r["entity"] else None,
                "results": _slim(r["results"]),
            }
            full = r
        else:  # nothing differs from plain rewrite
            variants["rewrite+live"] = dict(variants["rewrite"])

    if "scores" not in rec:
        if full is None or variants["rewrite+live"]["results"] != _slim(full["results"]):
            full = rag.retrieve(conn, client, query, rewrite=True, live=True, intent=intent)
        _, scores = rag.score_candidates(client, query, full["results"], write_text=False)
        rec["scores"] = [{"idx": i, **sc} for i, sc in scores.items()]
    return rec


def scores_by_idx(rec: dict) -> dict[int, dict]:
    return {s["idx"]: {k: v for k, v in s.items() if k != "idx"} for s in rec["scores"]}


def collect_all(queries: list[str], *, refresh: bool = False, limit: int | None = None) -> dict:
    """Collect every query (resumable); returns the whole cache."""
    # Rate limits are per minute — be willing to wait a full minute rather than fail.
    llm.MAX_WAIT_S = 75.0
    llm.MAX_ATTEMPTS = 6

    cache = {} if refresh else load_json(CACHE_PATH, {})
    client = llm.get_client()
    conn = db.get_conn()
    try:
        conn.rollback()
        conn.set_session(readonly=True)  # belt and braces: the harness never writes
        todo = queries[:limit] if limit else queries
        for n, q in enumerate(todo, 1):
            print(f"\n[{n}/{len(todo)}] {q}")
            try:
                cache[q] = collect(conn, client, q, cache.get(q))
            except llm.LLMError as exc:
                print(f"   ⚠️  stopped on {q!r}: {exc.user_message}  (rerun to resume)")
                break
            finally:
                save_json(CACHE_PATH, cache)
    finally:
        conn.close()
    return cache
