"""Offline tests for the evaluation package. Run:  python -m pytest tests   (or python tests/test_eval.py)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import rag
from pipeline.eval import harness, run_eval
from pipeline.eval.metrics import dedupe, paired_bootstrap, precision_at_k, reciprocal_rank


def test_dedupe_keeps_first_and_ignores_case():
    assert dedupe(["A", "b", "a", "B ", "c"]) == ["A", "b", "c"]


def test_precision_and_mrr():
    ranked = ["x", "a", "y", "b"]
    assert precision_at_k(ranked, {"a", "b"}, 1) == 0.0
    assert precision_at_k(ranked, {"a", "b"}, 2) == 0.5
    assert precision_at_k(ranked, {"a", "b"}, 4) == 0.5
    assert reciprocal_rank(ranked, {"a", "b"}) == 0.5
    assert reciprocal_rank(ranked, {"zzz"}) == 0.0


def test_duplicates_do_not_inflate_precision():
    assert precision_at_k(["a", "a", "a"], {"a"}, 3) == 1 / 3


def test_short_list_is_penalised():
    assert precision_at_k(["a"], {"a"}, 5) == 0.2


def test_bootstrap_detects_a_clear_gain_and_no_gain():
    d, lo, hi = paired_bootstrap([1.0] * 20, [0.0] * 20)
    assert d == 1.0 and lo == 1.0 and hi == 1.0
    d, lo, hi = paired_bootstrap([0.5, 0.0, 1.0, 0.5] * 5, [0.5, 1.0, 0.0, 0.5] * 5)
    assert lo < 0 < hi


def _results(names, sims):
    return [{"name": n, "type": "song", "similarity": s} for n, s in zip(names, sims)]


def _record(naive, rewrite, scores):
    """Synthetic cache record: R knows 'good' is the right answer, cosine does not."""
    v = {
        "naive": {"results": _results(naive, [0.7, 0.69, 0.68, 0.67])},
        "rewrite": {"results": _results(rewrite, [0.7, 0.69, 0.68, 0.67])},
    }
    v["rewrite+live"] = v["rewrite"]
    return {"intent": {}, "variants": v, "scores": scores}


def test_evaluate_ranks_systems_and_reports_unjudged():
    names = ["bad1", "bad2", "good", "bad3"]
    scores = [
        {"idx": 0, "dims": {"emotional_match": .2, "tone": .2, "usability": .2}, "r_score": .2, "why": "", "idea": ""},
        {"idx": 1, "dims": {"emotional_match": .1, "tone": .1, "usability": .1}, "r_score": .1, "why": "", "idea": ""},
        {"idx": 2, "dims": {"emotional_match": .9, "tone": .9, "usability": .9}, "r_score": .9, "why": "", "idea": ""},
        {"idx": 3, "dims": {"emotional_match": .1, "tone": .1, "usability": .1}, "r_score": .1, "why": "", "idea": ""},
    ]
    cache = {"q": _record(names, names, scores)}
    pool = {"q": {"candidates": [
        {"name": "good", "relevant": True}, {"name": "bad1", "relevant": False},
        {"name": "bad2", "relevant": False}, {"name": "bad3", "relevant": None},
    ]}}
    per, used, unj = run_eval.evaluate(cache, pool)
    assert used == ["q"]
    assert per["naive"]["P@1"] == [0.0]            # cosine ranks 'bad1' first
    assert per["R only"]["P@1"] == [1.0]           # the reasoning score finds 'good'
    assert per["cos + R"]["P@1"] == [1.0]
    assert 0 < unj < 1                              # 'bad3' sits in the top 5 unlabelled


def test_queries_without_a_relevant_label_are_skipped():
    cache = {"q": _record(["a", "b", "c", "d"], ["a", "b", "c", "d"], [])}
    pool = {"q": {"candidates": [{"name": "a", "relevant": False}]}}
    assert run_eval.evaluate(cache, pool)[1] == []


def test_collect_reuses_cache_and_skips_duplicate_live_variant(monkeypatch=None):
    calls = {"intent": 0, "retrieve": [], "score": 0}
    full = [{"name": "A", "type": "song", "similarity": .7, "description": "d", "core_emotional_logic": "l"}]

    def fake_intent(client, q):
        calls["intent"] += 1
        return {"reference_entity": None}

    def fake_retrieve(conn, client, q, **kw):
        calls["retrieve"].append((kw.get("rewrite"), kw.get("live")))
        return {"intent": kw["intent"], "entity": None, "search_string": q, "results": full}

    def fake_score(client, q, results, **kw):
        calls["score"] += 1
        return "s", {0: {"dims": {"emotional_match": 1, "tone": 1, "usability": 1}, "r_score": 1.0, "why": "", "idea": ""}}

    orig = (rag.step_a_extract_intent, rag.retrieve, rag.score_candidates)
    rag.step_a_extract_intent, rag.retrieve, rag.score_candidates = fake_intent, fake_retrieve, fake_score
    try:
        rec = harness.collect(None, None, "a question")
        assert calls["intent"] == 1 and calls["score"] == 1
        # no reference named -> naive + rewrite only; the live variant is a copy
        assert calls["retrieve"] == [(False, None), (True, False)]
        assert rec["variants"]["rewrite+live"]["results"] == rec["variants"]["rewrite"]["results"]
        again = harness.collect(None, None, "a question", rec)   # fully cached: nothing runs
        assert calls["intent"] == 1 and calls["score"] == 1 and len(calls["retrieve"]) == 2
        assert again is rec
    finally:
        rag.step_a_extract_intent, rag.retrieve, rag.score_candidates = orig


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  ", fn.__name__)
    print(f"{len(fns)} tests passed")
