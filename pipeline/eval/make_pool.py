"""
pipeline/eval/make_pool.py
==========================
Step 1 of evaluation: build the sheet that humans label.

    python -m pipeline.eval.make_pool              # all queries in queries.json
    python -m pipeline.eval.make_pool --limit 5    # try a few first

For every query it runs all retrieval variants (cached in cache.json, so it is
resumable if Groq rate-limits you) and writes pool.json: the union of every
variant's top results. Open pool.json and set  "relevant": true / false  on each
candidate. Existing labels are kept when you rerun this.

Labels must come from people — nothing here guesses relevance.
"""
from __future__ import annotations

import argparse

from pipeline.eval import harness
from pipeline.eval.metrics import dedupe, norm


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queries", default=str(harness.QUERIES_PATH))
    ap.add_argument("--limit", type=int, default=None, help="only the first N queries")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and recollect everything")
    args = ap.parse_args()

    from pathlib import Path
    queries = harness.load_json(Path(args.queries), [])
    cache = harness.collect_all(queries, refresh=args.refresh, limit=args.limit)
    pool = harness.load_json(harness.POOL_PATH, {})

    for q in queries:
        rec = cache.get(q)
        if not rec or "scores" not in rec:
            continue
        names, types = [], {}
        for v in rec["variants"].values():
            for r in v["results"]:
                names.append(r["name"])
                types[norm(r["name"])] = r["type"]
        old = {norm(c["name"]): c.get("relevant") for c in pool.get(q, {}).get("candidates", [])}
        pool[q] = {
            "intent": rec["intent"],
            "candidates": [
                {"name": n, "type": types[norm(n)], "relevant": old.get(norm(n))}
                for n in dedupe(names)
            ],
        }

    harness.save_json(harness.POOL_PATH, pool)
    labelled = sum(1 for p in pool.values() for c in p["candidates"] if c["relevant"] is not None)
    total = sum(len(p["candidates"]) for p in pool.values())
    print(f"\nWrote {harness.POOL_PATH}  ({len(pool)} queries, {labelled}/{total} candidates labelled)")


if __name__ == "__main__":
    main()
