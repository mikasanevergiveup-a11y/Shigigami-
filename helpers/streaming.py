"""YouTube/SoundCloud stream extraction with resilient search fallbacks."""

import base64
import logging
import os
import tempfile
import unicodedata
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

BASE_YTDL_OPTS = {
    "format": "bestaudio[acodec!=none]/bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "geo_bypass": True,
    "retries": 2,
    "fragment_retries": 2,
    "socket_timeout": 20,
    "js_runtimes": {"node": {}},
}

# Do not force Android/iOS clients. Those clients can require client-bound
# PO tokens and may return LOGIN_REQUIRED for a public video.
YOUTUBE_FALLBACK_CLIENTS = (
    {},
    {"youtube": {"player_client": ["web_embedded"]}},
    {"youtube": {"player_client": ["tv"]}},
)

SHORT_MARKERS = ("#shorts", "#short", "youtube shorts")
MIN_PREFERRED_DURATION = 45
_COOKIE_FILE: str | None = None


def _normalise_query(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join(value.strip().split()))


def _cookie_file_from_env() -> str | None:
    """Materialize an optional base64 Netscape cookie file without committing it."""
    global _COOKIE_FILE
    encoded = os.getenv("YOUTUBE_COOKIES_B64", "").strip()
    if not encoded:
        return None
    if _COOKIE_FILE and os.path.exists(_COOKIE_FILE):
        return _COOKIE_FILE
    try:
        data = base64.b64decode(encoded, validate=True)
        if not data.startswith(b"# Netscape HTTP Cookie File"):
            raise ValueError("not a Netscape cookie file")
        fd, path = tempfile.mkstemp(prefix="youtube-", suffix=".cookies")
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(path, 0o600)
        _COOKIE_FILE = path
        return path
    except Exception as exc:
        logger.warning("Ignoring invalid YOUTUBE_COOKIES_B64: %s", exc)
        return None


def _yt_opts(extra_extractor_args: dict | None = None, *, flat_search: bool = False) -> dict:
    opts = dict(BASE_YTDL_OPTS)
    cookie_file = _cookie_file_from_env()
    if cookie_file:
        opts["cookiefile"] = cookie_file
    if flat_search:
        # Search metadata must be collected without extracting the first video.
        # This lets us skip one blocked/unavailable result and try the next one.
        opts.pop("format", None)
        opts["extract_flat"] = "in_playlist"
        opts["ignoreerrors"] = True
    if extra_extractor_args:
        opts["extractor_args"] = extra_extractor_args
    return opts


def _is_short(info: dict) -> bool:
    page_url = str(info.get("webpage_url") or info.get("original_url") or info.get("url") or "").lower()
    title = str(info.get("title") or "").lower()
    path = urlparse(page_url).path.lower()
    return "/shorts/" in path or any(marker in title for marker in SHORT_MARKERS)


def _duration(info: dict) -> int:
    try:
        return int(info.get("duration") or 0)
    except (TypeError, ValueError):
        return 0


def _candidate_url(entry: dict) -> str | None:
    value = entry.get("webpage_url") or entry.get("original_url") or entry.get("url")
    if not value:
        video_id = entry.get("id")
        if video_id:
            value = f"https://www.youtube.com/watch?v={video_id}"
    if not isinstance(value, str):
        return None
    if value.startswith("https://www.youtube.com/watch?") or value.startswith("https://youtu.be/"):
        return value
    return None


def _ordered_candidates(entries: list[dict]) -> list[str]:
    valid = [entry for entry in entries if entry and not _is_short(entry) and _candidate_url(entry)]
    preferred = [entry for entry in valid if _duration(entry) >= MIN_PREFERRED_DURATION]
    ordered = preferred + [entry for entry in valid if entry not in preferred]
    return [_candidate_url(entry) for entry in ordered if _candidate_url(entry)]


def _format_duration(seconds: int) -> str:
    if not seconds:
        return "Live Stream"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _extract_video(video_url: str, extra_opts: dict | None = None) -> dict:
    with YoutubeDL(_yt_opts(extra_opts)) as ytdl:
        info = ytdl.extract_info(video_url, download=False)
    if not info:
        raise RuntimeError("yt-dlp returned no video information")
    stream_url = info.get("url")
    if not stream_url:
        raise RuntimeError("No playable audio stream URL was returned")
    return {
        "title": info.get("title", "Unknown Title"),
        "duration": _format_duration(_duration(info)),
        "stream_url": stream_url,
        "url": info.get("webpage_url") or video_url,
        "thumbnail": info.get("thumbnail") or "https://telegra.ph/file/f02e6503b22c7104e6c38.jpg",
    }


def _search_youtube_candidates(query: str) -> list[str]:
    targets = (f"ytsearch10:{query} -shorts", f"ytsearch10:{query}")
    candidates: list[str] = []
    for target in targets:
        try:
            with YoutubeDL(_yt_opts(flat_search=True)) as ytdl:
                info = ytdl.extract_info(target, download=False)
            entries = [entry for entry in (info.get("entries") or []) if entry]
            for candidate in _ordered_candidates(entries):
                if candidate not in candidates:
                    candidates.append(candidate)
        except Exception as exc:
            logger.warning("YouTube metadata search failed for %r: %s", target, exc)
    return candidates


def _is_direct_youtube_short(value: str) -> bool:
    parsed = urlparse(value)
    return "youtube.com" in parsed.netloc.lower() and "/shorts/" in parsed.path.lower()


def _is_verification_error(error_text: str) -> bool:
    lowered = error_text.lower()
    return any(token in lowered for token in ("sign in to confirm", "not a bot", "captcha", "po token", "http error 403", "login_required"))


def extract_stream_info(url_or_query: str) -> dict:
    """Return a playable non-Short audio stream for a URL or search query."""
    query = _normalise_query(url_or_query)
    if not query:
        raise ValueError("Search query is empty")

    if _is_direct_youtube_short(query):
        raise ValueError("YouTube Shorts link များကို music playback အတွက် မဖွင့်ပါ။ သီချင်းအပြည့်အစုံ link/query ဖြင့် ထပ်စမ်းပါ။")

    if query.startswith("http://") or query.startswith("https://"):
        targets = [query]
    else:
        youtube_candidates = _search_youtube_candidates(query)
        last_exception: Exception | None = None
        for candidate in youtube_candidates:
            for extra_opts in YOUTUBE_FALLBACK_CLIENTS:
                try:
                    return _extract_video(candidate, extra_opts)
                except Exception as exc:
                    last_exception = exc
                    logger.warning("YouTube candidate failed %r: %s", candidate, exc)

        # YouTube search may be blocked while SoundCloud is still available.
        targets = [f"scsearch5:{query}"]
        for target in targets:
            try:
                with YoutubeDL(_yt_opts()) as ytdl:
                    info = ytdl.extract_info(target, download=False)
                entries = [entry for entry in (info.get("entries") or []) if entry]
                for entry in entries:
                    candidate = entry.get("webpage_url") or entry.get("url")
                    if candidate:
                        try:
                            return _extract_video(candidate)
                        except Exception as exc:
                            last_exception = exc
                            logger.warning("SoundCloud candidate failed %r: %s", candidate, exc)
            except Exception as exc:
                last_exception = exc
                logger.warning("SoundCloud search failed for %r: %s", query, exc)

        error_text = str(last_exception) if last_exception else "no playable result"
        if _is_verification_error(error_text):
            raise RuntimeError(
                "YouTube က ဒီ server request ကို verification လုပ်ခိုင်းနေပါသည်။ "
                "နောက်ထပ် သီချင်းအမည်/artist ဖြင့် ထပ်စမ်းပါ သို့မဟုတ် YouTube link အပြည့်အစုံ ပို့ပါ။"
            ) from last_exception
        raise RuntimeError(f"သီချင်း ရှာမတွေ့ပါခင်ဗျာ။ ({error_text})") from last_exception

    last_exception: Exception | None = None
    for extra_opts in YOUTUBE_FALLBACK_CLIENTS:
        try:
            return _extract_video(query, extra_opts)
        except Exception as exc:
            last_exception = exc
            logger.warning("Direct stream extraction failed %r: %s", query, exc)
    raise RuntimeError("ဒီ link ကို ဖွင့်မရပါ။ ပုံမှန် YouTube video link သို့မဟုတ် သီချင်းအမည်ဖြင့် ထပ်စမ်းပါ။") from last_exception


def get_stream_url(url_or_query: str) -> str:
    return extract_stream_info(url_or_query)["stream_url"]


def start_stream(chat_id: int, url_or_query: str) -> str:
    try:
        return get_stream_url(url_or_query)
    except Exception as exc:
        logger.error("Extract Stream Info Error for chat %s: %s", chat_id, exc)
        raise


def stop_stream(chat_id: int):
    return None
