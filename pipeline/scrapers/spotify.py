"""
pipeline/scrapers/spotify.py
=============================
Spotify API scraper for song metadata and audio features.

Uses the Client Credentials OAuth2 flow — no user login required.
Free dev app: https://developer.spotify.com/dashboard

Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env.
"""
from __future__ import annotations

import base64
import time

import httpx

from pipeline import config

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_BASE = "https://api.spotify.com/v1"

# Simple in-memory token cache (tokens expire in 3600s)
_token_cache: dict[str, float | str] = {}


def _get_token() -> str:
    """Fetch or return cached OAuth2 client credentials token."""
    now = time.time()
    if _token_cache.get("token") and now < float(_token_cache.get("expires_at", 0)):
        return str(_token_cache["token"])

    client_id = config.require(
        "SPOTIFY_CLIENT_ID",
        config.SPOTIFY_CLIENT_ID,
        hint="Create a free dev app at: https://developer.spotify.com/dashboard",
    )
    client_secret = config.require(
        "SPOTIFY_CLIENT_SECRET",
        config.SPOTIFY_CLIENT_SECRET,
        hint="Create a free dev app at: https://developer.spotify.com/dashboard",
    )

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            SPOTIFY_TOKEN_URL,
            headers={"Authorization": f"Basic {creds}"},
            data={"grant_type": "client_credentials"},
        )
        r.raise_for_status()
        data = r.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600) - 60
    return str(_token_cache["token"])


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


# ------------------------------------------------------------------
# Track
# ------------------------------------------------------------------
def get_track(title: str, artist: str) -> dict:
    """
    Fetch Spotify metadata for a track.

    Returns a dict with keys:
      title, artist, album, release_date, popularity, duration_ms
    """
    track = None
    for attempt in range(4):
        try:
            with httpx.Client(timeout=15.0) as client:
                # Step 1: search
                r = client.get(
                    f"{SPOTIFY_BASE}/search",
                    headers=_auth_headers(),
                    params={
                        "q": f'track:"{title}" artist:"{artist}"',
                        "type": "track",
                        "limit": 1,
                    },
                )
                if r.status_code == 429:
                    wait_s = int(r.headers.get("Retry-After", 5))
                    time.sleep(wait_s)
                    continue
                r.raise_for_status()
                items = r.json().get("tracks", {}).get("items", [])
                if not items:
                    # Fallback: broader search
                    r = client.get(
                        f"{SPOTIFY_BASE}/search",
                        headers=_auth_headers(),
                        params={"q": f"{title} {artist}", "type": "track", "limit": 1},
                    )
                    if r.status_code == 429:
                        wait_s = int(r.headers.get("Retry-After", 5))
                        time.sleep(wait_s)
                        continue
                    r.raise_for_status()
                    items = r.json().get("tracks", {}).get("items", [])
                if not items:
                    raise ValueError(f"No Spotify results for: {title!r} by {artist!r}")

                track = items[0]
                break
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_s = int(e.response.headers.get("Retry-After", 5))
                time.sleep(wait_s)
                continue
            raise

    if not track:
        raise ValueError(f"Spotify request failed after retries for: {title!r} by {artist!r}")

    return {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "release_date": track["album"].get("release_date", ""),
        "popularity": track.get("popularity", 0),
        "duration_ms": track.get("duration_ms", 0),
    }
