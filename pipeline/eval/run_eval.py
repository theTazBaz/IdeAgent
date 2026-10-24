"""
pipeline/eval/run_eval.py
=========================
Step 2 of evaluation: score every system against the human labels.

    python -m pipeline.eval.run_eval

Reads cache.json (from make_pool) and pool.json (labelled by people); makes no
database or LLM calls. Systems compared, all on the same queries:

    naive          cosine on the raw query                      v = f(q)
    rewrite        cosine on the LLM-rewritten query            v = f(g(q, l_ref))
    rewrite+live   + live lookup for references missing from the DB
    R only         rewrite+live shortlist, ranked by the reasoning score alone
    cos + R        rewrite+live shortlist, ranked by  lam_cos*cos + lam_R*R   (no trend term)

Metrics: P@1, P@3, P@5, MRR over queries that have at least one relevant label,
plus a paired-bootstrap 95% interval for the difference from `naive`.
Also prints a lambda sweep for cos + R. With few labelled queries the sweep
overfits easily — treat it as a guide, not a result.
"""
from __future__ import annotations

from statistics import mean

from pipeline import rag
from pipeline.eval import harness
from pipeline.eval.metrics import norm, paired_bootstrap, precision_at_k, reciprocal_rank

KS = (1, 3, 5)


def rankings(rec: dict, lam_cos: float, lam_r: float) -> dict[str, list[str]]:
    v = rec["variants"]
    final = v["rewrite+live"]["results"]
    scores = harness.scores_by_idx(rec)
    r_only = rag.rank_candidates(final, scores, 0.0, 1.0)
    combined = rag.rank_candidates(final, scores, lam_cos, lam_r)
    return {
        "naive": [r["name"] for r in v["naive"]["results"]],
        "rewrite": [r["name"] for r in v["rewrite"]["results"]],
        "rewrite+live": [r["name"] for r in final],
        "R only": [x["name"] for x in r_only],
        "cos + R": [x["name"] for x in combined],
    }


def evaluate(cache: dict, pool: dict, lam_cos: float = rag.LAMBDA_COS, lam_r: float = rag.LAMBDA_R):
    """Return ({system: {metric: [per-query values]}}, queries used, share of top-5 items unlabelled)."""
    per: dict[str, dict[str, list[float]]] = {}
    used, unjudged, slots = [], 0, 0
    for q, p in pool.items():
        rec = cache.get(q)
        relevant = {c["name"] for c in p["candidates"] if c.get("relevant") is True}
        if not rec or "scores" not in rec or not relevant:
            continue
        judged = {norm(c["name"]) for c in p["candidates"] if c.get("relevant") is not None}
        used.append(q)
        for system, ranked in rankings(rec, lam_cos, lam_r).items():
            m = per.setdefault(system, {})
            for k in KS:
                m.setdefault(f"P@{k}", []).append(precision_at_k(ranked, relevant, k))
            m.setdefault("MRR", []).append(reciprocal_rank(ranked, relevant))
            for n in ranked[:5]:
                slots += 1
                unjudged += norm(n) not in judged
    return per, used, (unjudged / slots if slots else 0.0)


def main() -> None:
    cache = harness.load_json(harness.CACHE_PATH, {})
    pool = harness.load_json(harness.POOL_PATH, {})
    if not pool:
        raise SystemExit("No pool.json — run `python -m pipeline.eval.make_pool` and label it first.")

    per, used, unj = evaluate(cache, pool)
    if not used:
        raise SystemExit('No query has a candidate labelled "relevant": true yet — label pool.json first.')

    print(f"\nQueries evaluated: {len(used)} of {len(pool)}   (unlabelled share of top-5 slots: {unj:.0%})")
    cols = [f"P@{k}" for k in KS] + ["MRR"]
    print(f"\n{'system':14}" + "".join(f"{c:>8}" for c in cols) + "   Δ vs naive (95% CI) on P@3")
    for system, m in per.items():
        row = "".join(f"{mean(m[c]):8.3f}" for c in cols)
        if system == "naive":
            tail = ""
        else:
            d, lo, hi = paired_bootstrap(m["P@3"], per["naive"]["P@3"])
            tail = f"   {d:+.3f} [{lo:+.3f}, {hi:+.3f}]"
        print(f"{system:14}{row}{tail}")

    print("\nLambda sweep for 'cos + R'  (lam_cos = 1 - lam_R):")
    print(f"{'lam_R':>7}{'P@1':>8}{'P@3':>8}{'P@5':>8}{'MRR':>8}")
    for i in range(0, 11):
        lr = i / 10
        m = evaluate(cache, pool, 1 - lr, lr)[0]["cos + R"]
        print(f"{lr:7.1f}" + "".join(f"{mean(m[c]):8.3f}" for c in cols))
    print(f"\n(current setting: lam_cos={rag.LAMBDA_COS}, lam_R={rag.LAMBDA_R}; n={len(used)} — small samples overfit)")


if __name__ == "__main__":
    main()
