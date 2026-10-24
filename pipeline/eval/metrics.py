"""
pipeline/eval/metrics.py
========================
Pure ranking metrics. No database, no LLM.
"""
from __future__ import annotations

import random
from statistics import mean


def norm(name: str) -> str:
    return " ".join(name.lower().split())


def dedupe(ranked: list[str]) -> list[str]:
    """Drop repeated names, keeping the first (the DB holds duplicate rows)."""
    seen, out = set(), []
    for n in ranked:
        k = norm(n)
        if k not in seen:
            seen.add(k)
            out.append(n)
    return out


def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the top-k slots that hold a relevant item (short lists are penalised)."""
    rel = {norm(r) for r in relevant}
    return sum(1 for n in dedupe(ranked)[:k] if norm(n) in rel) / k


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    rel = {norm(r) for r in relevant}
    for i, n in enumerate(dedupe(ranked), 1):
        if norm(n) in rel:
            return 1.0 / i
    return 0.0


def paired_bootstrap(a: list[float], b: list[float], n: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """
    Mean of (a - b) over queries with a 95% percentile-bootstrap interval.
    a and b are per-query scores for two systems, in the same query order.
    """
    assert len(a) == len(b) and a, "need equal-length, non-empty score lists"
    diffs = [x - y for x, y in zip(a, b)]
    rng = random.Random(seed)
    means = sorted(mean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return mean(diffs), means[int(0.025 * n)], means[int(0.975 * n) - 1]
