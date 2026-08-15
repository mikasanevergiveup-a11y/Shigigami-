"""SoundCloud-only audio search and stream extraction."""

import logging
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

BASE_YTDL_OPTS = {
    "format": "bestaudio[acodec!=none]/bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "quiet": True,
    "no_warnings": True,
    "retries": 2,
    "fragment_retries": 2,
    "socket_timeout": 25,
    "source_address": "0.0.0.0",
}

MUSIC_MARKERS = (
    "official audio", "music video", "lyric video", "lyrics", "audio",
    "song", "music", "cover", "remix", "acoustic", "karaoke", "ost",
    "soundtrack", "live performance", "မြန်မာသီချင်း", "သီချင်း",
)
NON_MUSIC_MARKERS = (
    "podcast", "reaction", "review", "tutorial", "interview", "news",
    "documentary", "gameplay", "walkthrough", "vlog", "trailer", "teaser",
    "short film", "episode", "sermon", "motivation", "speech", "lecture",
)

SOUNDCLOUD_HOSTS = {"soundcloud.com", "www.soundcloud.com", "on.soundcloud.com"}


def _normalise_query(value: str) -> str:
    return " ".join(value.strip().split())


def _is_soundcloud_url(value: str) -> bool:
    try:
        host = (urlparse(value).hostname or "").lower()
        return host in SOUNDCLOUD_HOSTS or host.endswith(".soundcloud.com")
    except Exception:
        return False


def _duration(info: dict) -> int:
    try:
        return int(float(info.get("duration") or 0))
    except (TypeError, ValueError):
        return 0


def _format_duration(seconds: int) -> str:
    if not seconds:
        return "Live Stream"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _music_score(entry: dict) -> int:
    title = str(entry.get("title") or "").lower()
    score = sum(4 for marker in MUSIC_MARKERS if marker in title)
    score -= sum(6 for marker in NON_MUSIC_MARKERS if marker in title)
    if _duration(entry) >= 45:
        score += 2
    return score


def _stream_result(info: dict, source_url: str) -> dict:
    if not info:
        raise RuntimeError("SoundCloud က track information မပြန်ပေးပါ")
    stream_url = info.get("url")
    if not stream_url:
        raise RuntimeError("ဒီ SoundCloud track ကို playable audio မရပါ")
    return {
        "title": info.get("title", "Unknown Title"),
        "duration": _format_duration(_duration(info)),
        "stream_url": stream_url,
        "url": info.get("webpage_url") or source_url,
        "thumbnail": info.get("thumbnail") or "https://telegra.ph/file/f02e6503b22c7104e6c38.jpg",
        "source": "SoundCloud",
    }


def _extract_soundcloud_url(track_url: str) -> dict:
    if not _is_soundcloud_url(track_url):
        raise ValueError("SoundCloud link သာ အသုံးပြုနိုင်ပါသည်")
    with YoutubeDL(dict(BASE_YTDL_OPTS, ignoreerrors=False)) as ytdl:
        info = ytdl.extract_info(track_url, download=False)
    return _stream_result(info, track_url)


def _search_soundcloud(query: str) -> dict:
    last_error: Exception | None = None
    for target in (f"scsearch10:{query}", f"scsearch10:{query} song"):
        try:
            with YoutubeDL(BASE_YTDL_OPTS) as ytdl:
                info = ytdl.extract_info(target, download=False)
            entries = [entry for entry in (info.get("entries") or []) if entry and entry.get("url")]
            ranked = sorted(
                enumerate(entries),
                key=lambda item: (-_music_score(item[1]), -_duration(item[1]), item[0]),
            )
            for _, entry in ranked:
                try:
                    return _stream_result(entry, entry.get("webpage_url") or entry.get("url"))
                except Exception as exc:
                    last_error = exc
                    logger.warning("SoundCloud entry unavailable: %s", exc)
        except Exception as exc:
            last_error = exc
            logger.warning("SoundCloud search failed for %r: %s", query, exc)
    if last_error:
        raise RuntimeError(f"SoundCloud မှ playable သီချင်း မတွေ့ပါ ({last_error})") from last_error
    raise RuntimeError("SoundCloud မှ playable သီချင်း မတွေ့ပါ")


def extract_stream_info(url_or_query: str) -> dict:
    """Return a SoundCloud audio stream for a track URL or search query."""
    query = _normalise_query(url_or_query)
    if not query:
        raise ValueError("သီချင်းအမည် မထည့်ရသေးပါ")
    if query.startswith(("http://", "https://")):
        if not _is_soundcloud_url(query):
            raise ValueError("SoundCloud link သာ အသုံးပြုနိုင်ပါသည်။ SoundCloud သီချင်းအမည်ဖြင့်လည်း ရှာနိုင်ပါသည်။")
        return _extract_soundcloud_url(query)
    return _search_soundcloud(query)


def get_stream_url(url_or_query: str) -> str:
    return extract_stream_info(url_or_query)["stream_url"]


def start_stream(chat_id: int, url_or_query: str) -> str:
    try:
        return get_stream_url(url_or_query)
    except Exception as exc:
        logger.error("SoundCloud stream error for chat %s: %s", chat_id, exc)
        raise


def stop_stream(chat_id: int):
    return None
