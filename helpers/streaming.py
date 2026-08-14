import os
import asyncio
import logging
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

# Full Song (သီချင်းအပြည့်အစုံ) ရရှိစေရန် YTDL Options ပြင်ဆင်ချက်
YTDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "geo_bypass": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "ios"],
            "player_skip": ["webpage", "configs"],
        }
    },
}


def extract_stream_info(url_or_query: str) -> dict:
    """
    YouTube / SoundCloud မှ Full Song Stream URL, Thumbnail နှင့် Track Info များကို ဆွဲထုတ်ပေးသည်။
    """
    if url_or_query.startswith("http"):
        search_targets = [url_or_query]
    else:
        # Full Song ရရှိရန် 1. YouTube Standard Search, 2. SoundCloud Search
        search_targets = [
            f"ytsearch1:{url_or_query}",
            f"scsearch1:{url_or_query}",
        ]

    last_exception = None

    for target in search_targets:
        try:
            with YoutubeDL(YTDL_OPTS) as ytdl:
                info = ytdl.extract_info(target, download=False)

                if "entries" in info and len(info["entries"]) > 0:
                    info = info["entries"][0]

                stream_url = info.get("url")
                if stream_url:
                    # Duration စက္ကန့်မှ (MM:SS) သို့ ပြောင်းခြင်း
                    dur_sec = info.get("duration", 0)
                    if dur_sec:
                        m, s = divmod(int(dur_sec), 60)
                        h, m = divmod(m, 60)
                        duration_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                    else:
                        duration_str = "Live Stream"

                    thumb = info.get("thumbnail") or "https://telegra.ph/file/f02e6503b22c7104e6c38.jpg"

                    return {
                        "title": info.get("title", "Unknown Title"),
                        "duration": duration_str,
                        "stream_url": stream_url,
                        "url": info.get("webpage_url", url_or_query),
                        "thumbnail": thumb,
                    }
        except Exception as e:
            last_exception = e
            logger.warning(f"Failed searching with target '{target}': {e}")
            continue

    raise Exception(f"သီချင်း ရှာမတွေ့ပါခင်ဗျာ။ ({last_exception})")


def get_stream_url(url_or_query: str) -> str:
    info = extract_stream_info(url_or_query)
    return info["stream_url"]


def start_stream(chat_id: int, url_or_query: str) -> str:
    try:
        return get_stream_url(url_or_query)
    except Exception as e:
        logger.error(f"Extract Stream Info Error: {e}")
        raise Exception(f"Stream URL ရှာမတွေ့ပါခင်ဗျာ။ ({e})")


def stop_stream(chat_id: int):
    pass
    