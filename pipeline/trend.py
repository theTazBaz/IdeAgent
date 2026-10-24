"""
pipeline/trend.py
=================
Live trend signal for songs, from Last.fm. Read-only: nothing is written to the
database, and results are cached in memory.

    trends = get_trends(results)     # {index into results: {...}} for songs only

For each song the signal T is in [0, 1]:

    P  popularity   log-scaled distinct listeners (track.getInfo)
    C  chart        1.0 at #1 down to 0.5 at #N of Last.fm's current global chart, 0 if absent
    T = 0.35*P + 0.65*C

The chart carries more weight because popularity is all-time (it favours
evergreen songs), while the chart reflects what is being played now.

Anything that goes wrong — no API key, network error, a song Last.fm does not
know — just leaves that song without a trend, which the ranking treats as
neutral. The question never fails because of trend data.

Because values are fetched live there is no staleness to decay. If scores are
ever stored in the database, apply T = T0 * exp(-k * age) at query time.
"""
from __future__ import annotations

import math
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from pipeline import config

API_URL = "https://ws.audioscrobbler.com/2.0/"
TRACK_TTL_S = 24 * 3600
CHART_TTL_S = 6 * 3600
CHART_PAGES, CHART_PAGE_SIZE = 5, 200          # top 1000
MIN_INTERVAL_S = 0.22                          # stay under Last.fm's ~5 requests/second
TIMEOUT_S = 8.0

LISTENERS_FLOOR, LISTENERS_CEIL = 1_000, 5_000_000
W_POPULARITY, W_CHART = 0.35, 0.65

_lock = threading.Lock()
_next_slot = 0.0
_track_cache: dict[tuple[str, str], tuple[float, dict | None]] = {}
_chart_cache: tuple[float, dict[tuple[str, str], int]] | None = None
_warned = False


# ------------------------------------------------------------------
# Matching helpers
# ------------------------------------------------------------------
def clean_title(title: str) -> str:
    """Strip '(feat. X)', '(From "...")', '[Remix]' and '- 2012 Remaster' style suffixes."""
    t = re.sub(r"\s*[\(\[].*?[\)\]]", "", title)
    t = re.sub(r"\s+-\s+(.*?(remaster|version|edit|mix|live|from|mono|stereo|radio|single).*)$", "", t, flags=re.I)
    return t.strip()


def primary_artist(artist: str) -> str:
    return re.split(r"\s*(?:,|&| feat\.| ft\.| x )\s*", artist, flags=re.I)[0].strip()


def split_name(name: str) -> tuple[str, str]:
    """Song results are named 'title — artist'."""
    title, _, artist = name.rpartition(" — ")
    return (title, artist) if title else (name, "")


def _key(title: str, artist: str) -> tuple[str, str]:
    return clean_title(title).lower(), primary_artist(artist).lower()


# ------------------------------------------------------------------
# HTTP
# ------------------------------------------------------------------
def _api_key() -> str | None:
    return os.environ.get("LASTFM_API_KEY") or getattr(config, "LASTFM_API_KEY", None)


def _call(params: dict) -> dict:
    """One rate-limited Last.fm call. Raises on network / HTTP errors."""
    global _next_slot
    with _lock:
        wait = _next_slot - time.monotonic()
        _next_slot = max(time.monotonic(), _next_slot) + MIN_INTERVAL_S
    if wait > 0:
        time.sleep(wait)
    r = httpx.get(API_URL, params={**params, "api_key": _api_key(), "format": "json"}, timeout=TIMEOUT_S)
    if r.status_code >= 500:
        r.raise_for_status()
    return r.json()


# ------------------------------------------------------------------
# Signals
# ------------------------------------------------------------------
def _listeners(title: str, artist: str) -> int | None:
    """Distinct listeners, or None if Last.fm does not know the track. Cached."""
    key = _key(title, artist)
    hit = _track_cache.get(key)
    if hit and time.monotonic() - hit[0] < TRACK_TTL_S:
        return hit[1]["listeners"] if hit[1] else None

    # The title as stored first ("Exit Music (For A Film)" is the real name), then with
    # "(feat. X)" / "(From ...)" / remaster suffixes stripped; primary artist, then as stored.
    value = None
    for t in dict.fromkeys([title, clean_title(title)]):
        for a in dict.fromkeys([primary_artist(artist), artist]):
            data = _call({"method": "track.getInfo", "track": t, "artist": a, "autocorrect": 1})
            if "track" in data:
                value = {"listeners": int(data["track"].get("listeners") or 0)}
                break
        if value:
            break
    _track_cache[key] = (time.monotonic(), value)   # "not found" is cached too; errors raise and are not
    return value["listeners"] if value else None


def _chart() -> dict[tuple[str, str], int]:
    """{(title, artist): rank} for Last.fm's current global top tracks. Cached."""
    global _chart_cache
    if _chart_cache and time.monotonic() - _chart_cache[0] < CHART_TTL_S:
        return _chart_cache[1]
    ranks: dict[tuple[str, str], int] = {}
    for page in range(1, CHART_PAGES + 1):
        data = _call({"method": "chart.gettoptracks", "limit": CHART_PAGE_SIZE, "page": page})
        for t in data.get("tracks", {}).get("track", []):
            ranks.setdefault(_key(t["name"], t["artist"]["name"]), len(ranks) + 1)
    _chart_cache = (time.monotonic(), ranks)
    return ranks


def popularity(listeners: int | None) -> float:
    if not listeners or listeners <= LISTENERS_FLOOR:
        return 0.0
    return min(1.0, math.log10(listeners / LISTENERS_FLOOR) / math.log10(LISTENERS_CEIL / LISTENERS_FLOOR))


def chart_score(rank: int | None, size: int) -> float:
    if rank is None:
        return 0.0
    return 0.5 + 0.5 * (1 - (rank - 1) / max(size, 1))


def trend_score(listeners: int | None, rank: int | None, size: int) -> float:
    return W_POPULARITY * popularity(listeners) + W_CHART * chart_score(rank, size)


# ------------------------------------------------------------------
# Public
# ------------------------------------------------------------------
def get_trends(results: list[dict]) -> dict[int, dict]:
    """
    Trend info for the songs among `results`, keyed by index into `results`:
        {"score": 0..1, "listeners": int|None, "in_chart": bool, "rank": int|None}
    Songs Last.fm cannot place are left out (neutral). Never raises.
    """
    global _warned
    songs = [(i, *split_name(r["name"])) for i, r in enumerate(results) if r["type"] == "song"]
    if not songs:
        return {}
    if not _api_key():
        if not _warned:
            print("       trend: LASTFM_API_KEY not set — ranking without a trend signal.")
            _warned = True
        return {}

    try:
        ranks = _chart()
    except Exception as exc:
        print(f"       trend: chart unavailable ({type(exc).__name__}) — using popularity only.")
        ranks = {}

    def one(item):
        i, title, artist = item
        try:
            listeners = _listeners(title, artist)
        except Exception as exc:
            print(f"       trend: lookup failed for {title!r} ({type(exc).__name__}).")
            return i, None
        rank = ranks.get(_key(title, artist))
        if listeners is None and rank is None:
            return i, None
        return i, {
            "score": round(trend_score(listeners, rank, len(ranks)), 3),
            "listeners": listeners,
            "in_chart": rank is not None,
            "rank": rank,
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        return {i: t for i, t in pool.map(one, songs) if t}
