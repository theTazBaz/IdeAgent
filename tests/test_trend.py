"""Offline tests for the trend signal. Run:  python tests/test_trend.py   (no network, no DB)"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import rag, trend


def _reset():
    trend._track_cache.clear()
    trend._chart_cache = None
    trend._warned = False
    trend.MIN_INTERVAL_S = 0.0


def test_title_and_artist_cleaning():
    assert trend.clean_title('WHARF TALK (feat. A$AP Rocky)') == "WHARF TALK"
    assert trend.clean_title('Naina (From "Crew")') == "Naina"
    assert trend.clean_title("Starman - 2012 Remaster") == "Starman"
    assert trend.clean_title("Bohemian Rhapsody") == "Bohemian Rhapsody"
    assert trend.primary_artist("Tyler, The Creator") == "Tyler"   # known limitation, falls back to full name
    assert trend.primary_artist("Metro Boomin & Future") == "Metro Boomin"
    assert trend.split_name("Believer — Imagine Dragons") == ("Believer", "Imagine Dragons")
    assert trend.split_name("A — B — C") == ("A — B", "C")


def test_scales():
    assert trend.popularity(None) == 0.0 and trend.popularity(500) == 0.0
    assert trend.popularity(5_000_000) == 1.0 and trend.popularity(50_000_000) == 1.0
    assert 0 < trend.popularity(100_000) < trend.popularity(1_000_000) < 1
    assert trend.chart_score(None, 1000) == 0.0
    assert trend.chart_score(1, 1000) == 1.0
    assert 0.5 <= trend.chart_score(1000, 1000) < 0.51
    # a chart song with modest popularity beats an evergreen that is not on the chart
    assert trend.trend_score(100_000, 300, 1000) > trend.trend_score(5_000_000, None, 1000)


def _fake_api(calls):
    def call(params):
        calls.append(params["method"])
        if params["method"] == "chart.gettoptracks":
            if params["page"] == 1:
                return {"tracks": {"track": [{"name": "Hot Song (feat. X)", "artist": {"name": "Star"}}]}}
            return {"tracks": {"track": []}}
        if params["track"] == "Hot Song":
            return {"track": {"listeners": "2000000", "playcount": "9"}}
        if params["track"] == "Exit Music (For A Film)":
            return {"track": {"listeners": "2000000"}}
        if params["track"] == "Exit Music":          # what stripping the brackets would wrongly find
            return {"track": {"listeners": "39536"}}
        if params["track"] == "Old Song":
            return {"track": {"listeners": "4000000"}}
        if params["track"] == "Boom":
            raise RuntimeError("network")
        return {"error": 6, "message": "Track not found"}
    return call


def test_get_trends_end_to_end_with_cache_and_neutral_cases():
    _reset()
    os.environ["LASTFM_API_KEY"] = "test"
    calls = []
    orig, trend._call = trend._call, _fake_api(calls)
    try:
        results = [
            {"type": "song", "name": "Hot Song — Star"},
            {"type": "song", "name": "Old Song — Legend"},
            {"type": "song", "name": "Unknown — Nobody"},
            {"type": "song", "name": "Boom — Err"},
            {"type": "movie", "name": "A Movie"},
            {"type": "song", "name": "Exit Music (For A Film) — Radiohead"},
        ]
        t = trend.get_trends(results)
        assert t[5]["listeners"] == 2_000_000         # real title wins over the stripped one
        assert set(t) == {0, 1, 5}                       # unknown, failing and non-song candidates are left out
        assert t[0]["in_chart"] and t[0]["rank"] == 1
        assert not t[1]["in_chart"] and t[1]["listeners"] == 4_000_000
        assert t[0]["score"] > t[1]["score"]          # being on the chart outweighs raw popularity
        n = len(calls)
        trend.get_trends(results)                     # second call: chart and found/not-found tracks are cached
        assert len(calls) - n == 1                    # only the failing lookup is retried
        assert trend.get_trends([{"type": "movie", "name": "M"}]) == {}
    finally:
        trend._call = orig


def test_no_api_key_means_no_trend_and_no_error():
    _reset()
    os.environ.pop("LASTFM_API_KEY", None)
    trend.config.LASTFM_API_KEY = None
    assert trend.get_trends([{"type": "song", "name": "A — B"}]) == {}


def test_chart_failure_falls_back_to_popularity():
    _reset()
    os.environ["LASTFM_API_KEY"] = "test"
    def call(params):
        if params["method"] == "chart.gettoptracks":
            raise RuntimeError("down")
        return {"track": {"listeners": "1000000"}}
    orig, trend._call = trend._call, call
    try:
        t = trend.get_trends([{"type": "song", "name": "S — A"}])
        assert t[0]["in_chart"] is False and t[0]["score"] > 0
    finally:
        trend._call = orig


def _res(n):
    return [{"type": "song", "name": f"S{i}", "similarity": 0.70, "description": "", "core_emotional_logic": ""} for i in range(n)]


def _sc(r):
    return {"dims": {"emotional_match": r, "tone": r, "usability": r}, "r_score": r, "why": "", "idea": ""}


def test_ranking_uses_trend_as_a_nudge_not_an_override():
    res = _res(3)
    scores = {0: _sc(0.90), 1: _sc(0.85), 2: _sc(0.30)}
    base = [x["name"] for x in rag.rank_candidates(res, scores)]
    assert base == ["S0", "S1", "S2"]
    # a tiny fit gap is overturned by a big trend gap ...
    trends = {0: {"score": 0.0}, 1: {"score": 1.0}, 2: {"score": 1.0}}
    assert [x["name"] for x in rag.rank_candidates(res, scores, trends=trends)][0] == "S1"
    # ... but a poor fit is not rescued by trending
    assert [x["name"] for x in rag.rank_candidates(res, scores, trends=trends)][-1] == "S2"


def test_candidates_without_trend_are_not_penalised():
    res = _res(2)
    scores = {0: _sc(0.8), 1: _sc(0.8)}
    r = rag.rank_candidates(res, scores, trends={0: {"score": 0.8}})   # S1 has no trend
    by = {x["name"]: x["score"] for x in r}
    assert abs(by["S0"] - by["S1"]) < 0.02          # neutral: same fit, near-same score
    assert all(0 <= x["score"] <= 1 for x in r)
    # trends=None must reproduce the old two-term ranking exactly (evaluation harness relies on this)
    plain = rag.rank_candidates(res, scores, 0.4, 0.6)
    assert plain[0]["trend"] is None and plain[0]["score"] == round((0.4 * 0.6667 + 0.6 * 0.8) / 1.0, 3)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  ", fn.__name__)
    print(f"{len(fns)} tests passed")
