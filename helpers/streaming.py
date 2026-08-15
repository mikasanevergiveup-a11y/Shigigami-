"""YouTube/SoundCloud stream extraction with search filtering and fallbacks."""

import logging
import unicodedata
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

# Do not force Android/iOS clients here. YouTube increasingly requires
# client-specific PO tokens for those clients; yt-dlp's default client
# selection is safer and can choose clients that do not require a token.
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
    # Node is installed in the Render image and enables yt-dlp's modern
    # YouTube JavaScript challenge support when yt-dlp-ejs is available.
    "js_runtimes": {"node": {}},
}

# These are fallback-only clients. The default yt-dlp client selection is
# attempted first. web_embedded avoids some guest-account restrictions;
# tv is another no-cookie fallback for public videos.
YOUTUBE_FALLBACK_CLIENTS = (
    {"youtube": {"player_client": ["web_embedded"]}},
    {"youtube": {"player_client": ["tv"]}},
)

SHORT_MARKERS = ("#shorts", "#short", "youtube shorts")
MIN_PREFERRED_DURATION = 45


def _normalise_query(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join(value.strip().split()))


def _is_short(info: dict) -> bool:
    page_url = str(info.get("webpage_url") or info.get("original_url") or "").lower()
    title = str(info.get("title") or "").lower()
    path = urlparse(page_url).path.lower()
    return "/shorts/" in path or any(marker in title for marker in SHORT_MARKERS)


def _duration(info: dict) -> int:
    try:
        return int(info.get("duration") or 0)
    except (TypeError, ValueError):
        return 0


def _pick_music_result(entries: list[dict]) -> dict | None:
    candidates = [entry for entry in entries if entry and not _is_short(entry)]
    if not candidates:
        return None

    # Prefer ordinary song-length results. If all remaining results are
    # short/unknown duration, retain the first non-Short result rather than
    # failing an otherwise valid Burmese search.
    preferred = [entry for entry in candidates if _duration(entry) >= MIN_PREFERRED_DURATION]
    return preferred[0] if preferred else candidates[0]


def _format_duration(seconds: int) -> str:
    if not seconds:
        return "Live Stream"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _extract_target(target: str, extra_opts: dict) -> dict:
    opts = {**BASE_YTDL_OPTS}
    if extra_opts:
        opts["extractor_args"] = extra_opts

    with YoutubeDL(opts) as ytdl:
        info = ytdl.extract_info(target, download=False)
        if not info:
            raise RuntimeError("yt-dlp returned no result")

        entries = info.get("entries") if isinstance(info, dict) else None
        if entries is not None:
            result = _pick_music_result([entry for entry in entries if entry])
            if not result:
                raise RuntimeError("YouTube search returned only Shorts or no playable result")
            info = result

        stream_url = info.get("url")
        if not stream_url:
            raise RuntimeError("No playable audio stream URL was returned")

        duration = _duration(info)
        return {
            "title": info.get("title", "Unknown Title"),
            "duration": _format_duration(duration),
            "stream_url": stream_url,
            "url": info.get("webpage_url") or target,
            "thumbnail": info.get("thumbnail") or "https://telegra.ph/file/f02e6503b22c7104e6c38.jpg",
        }


def _is_direct_youtube_short(value: str) -> bool:
    parsed = urlparse(value)
    return "youtube.com" in parsed.netloc.lower() and "/shorts/" in parsed.path.lower()


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
        # Search several candidates and explicitly discourage Shorts. The
        # unmodified query remains as a fallback for Burmese titles whose
        # YouTube search ranking is sensitive to extra English keywords.
        targets = [
            f"ytsearch10:{query} -shorts",
            f"ytsearch10:{query}",
            f"scsearch5:{query}",
        ]

    last_exception: Exception | None = None
    client_options = ({}, *YOUTUBE_FALLBACK_CLIENTS)

    for target in targets:
        if target.startswith("scsearch"):
            option_sets = ({},)
        else:
            option_sets = client_options

        for extra_opts in option_sets:
            try:
                return _extract_target(target, extra_opts)
            except Exception as exc:
                last_exception = exc
                logger.warning("Failed stream extraction target=%r options=%r: %s", target, extra_opts, exc)

    error_text = str(last_exception) if last_exception else "unknown extraction error"
    if any(token in error_text.lower() for token in ("sign in to confirm", "not a bot", "captcha", "po token", "http error 403")):
        raise RuntimeError(
            "YouTube က ဒီ server request ကို verification လုပ်ခိုင်းနေပါသည်။ "
            "ပုံမှန် search ကို fallback ဖြင့် ထပ်စမ်းပြီးဖြစ်သော်လည်း ယခုအချိန်တွင် YouTube ဘက်က request ကန့်သတ်ထားနိုင်ပါသည်။"
        ) from last_exception
    raise RuntimeError(f"သီချင်း ရှာမတွေ့ပါခင်ဗျာ။ ({error_text})") from last_exception


def get_stream_url(url_or_query: str) -> str:
    return extract_stream_info(url_or_query)["stream_url"]


def start_stream(chat_id: int, url_or_query: str) -> str:
    try:
        return get_stream_url(url_or_query)
    except Exception as exc:
        logger.error("Extract Stream Info Error for chat %s: %s", chat_id, exc)
        raise


def stop_stream(chat_id: int):
    # FFmpeg is owned by PyTgCalls; leaving the call stops the active stream.
    return None
