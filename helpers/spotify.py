"""Optional Spotify catalog search used only to improve song metadata/search ranking.

Spotify never supplies the playback stream here. A matching SoundCloud track is
resolved separately and remains the only audio source used by the bot.
"""

import base64
import logging
import os
import time
from urllib.parse import parse_qs, urlparse

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.spotify.com/v1"
TOKEN_URL = "https://accounts.spotify.com/api/token"
_TOKEN = None
_TOKEN_EXPIRES_AT = 0.0


def _credentials():
    return (
        os.getenv("SPOTIFY_CLIENT_ID", "").strip(),
        os.getenv("SPOTIFY_CLIENT_SECRET", "").strip(),
    )


def spotify_enabled() -> bool:
    client_id, client_secret = _credentials()
    return bool(client_id and client_secret)


def _get_token(force_refresh: bool = False) -> str | None:
    global _TOKEN, _TOKEN_EXPIRES_AT
    if not spotify_enabled():
        return None
    if not force_refresh and _TOKEN and time.time() < _TOKEN_EXPIRES_AT:
        return _TOKEN

    client_id, client_secret = _credentials()
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=12,
    )
    response.raise_for_status()
    data = response.json()
    _TOKEN = data["access_token"]
    _TOKEN_EXPIRES_AT = time.time() + max(int(data.get("expires_in", 3600)) - 60, 60)
    return _TOKEN


def _spotify_get(path: str, params: dict | None = None) -> dict:
    token = _get_token()
    if not token:
        return {}
    response = requests.get(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=12,
    )
    if response.status_code == 401:
        token = _get_token(force_refresh=True)
        response = requests.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=12,
        )
    response.raise_for_status()
    return response.json()


def _track_item(item: dict) -> dict | None:
    name = str(item.get("name") or "").strip()
    artists = [str(artist.get("name") or "").strip() for artist in item.get("artists", [])]
    artists = [artist for artist in artists if artist]
    if not name or not artists:
        return None
    images = item.get("album", {}).get("images") or []
    return {
        "name": name,
        "artists": artists,
        "album": str(item.get("album", {}).get("name") or "").strip(),
        "duration": int(item.get("duration_ms") or 0) // 1000,
        "spotify_url": (item.get("external_urls") or {}).get("spotify", ""),
        "thumbnail": images[0].get("url", "") if images else "",
    }


def search_tracks(query: str, limit: int = 5) -> list[dict]:
    """Return Spotify track metadata; return an empty list when not configured."""
    if not spotify_enabled():
        return []
    try:
        data = _spotify_get(
            "/search",
            params={"q": query, "type": "track", "limit": min(max(limit, 1), 10), "market": "US"},
        )
        results = []
        for item in (data.get("tracks", {}).get("items") or []):
            track = _track_item(item)
            if track:
                results.append(track)
        return results
    except Exception as exc:
        logger.warning("Spotify search unavailable for %r: %s", query, exc)
        return []


def track_from_url(value: str) -> dict | None:
    """Resolve a Spotify track URL to metadata when Spotify credentials exist."""
    try:
        parsed = urlparse(value)
        if parsed.netloc.lower() not in {"open.spotify.com", "www.open.spotify.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[0] != "track":
            return None
        data = _spotify_get(f"/tracks/{parts[1]}", params={"market": "US"})
        return _track_item(data)
    except Exception as exc:
        logger.warning("Spotify track URL lookup failed: %s", exc)
        return None
