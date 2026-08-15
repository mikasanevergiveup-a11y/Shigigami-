"""SoundCloud-only download helpers used by optional bot features."""

import asyncio
import os
import uuid

import yt_dlp

import config


class DownloadError(Exception):
    pass


YDL_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "nocheckcertificate": True,
    "noplaylist": True,
    "retries": 2,
    "socket_timeout": 25,
}


def _is_soundcloud_url(url: str) -> bool:
    lowered = (url or "").lower()
    return "soundcloud.com/" in lowered or "on.soundcloud.com/" in lowered


def _ensure_soundcloud(url: str) -> None:
    if not _is_soundcloud_url(url):
        raise DownloadError("SoundCloud link သာ အသုံးပြုနိုင်ပါသည်။")


async def download_audio(url: str) -> tuple[str, dict]:
    """Download a SoundCloud audio track into the configured downloads folder."""
    _ensure_soundcloud(url)
    uid = uuid.uuid4().hex
    out_tmpl = os.path.join(config.DOWNLOADS_DIR, f"{uid}.%(ext)s")
    opts = {
        **YDL_BASE_OPTS,
        "format": "bestaudio[acodec!=none]/bestaudio/best",
        "outtmpl": out_tmpl,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    def _download():
        with yt_dlp.YoutubeDL(opts) as ytdl:
            return ytdl.extract_info(url, download=True)

    try:
        info = await asyncio.to_thread(_download)
    except Exception as exc:
        raise DownloadError(f"SoundCloud audio download failed: {exc}") from exc

    local_file = os.path.join(config.DOWNLOADS_DIR, f"{uid}.mp3")
    if not os.path.isfile(local_file):
        matches = [name for name in os.listdir(config.DOWNLOADS_DIR) if name.startswith(uid)]
        if not matches:
            raise DownloadError("Downloaded audio file not found on disk.")
        local_file = os.path.join(config.DOWNLOADS_DIR, matches[0])

    return local_file, {
        "title": info.get("title", "Unknown"),
        "url": info.get("webpage_url") or url,
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "source": "SoundCloud",
    }


async def download_video(url: str) -> tuple[str, dict]:
    """Reject video downloads because this bot is intentionally SoundCloud-audio-only."""
    _ensure_soundcloud(url)
    raise DownloadError("ဒီ bot version သည် audio music အတွက်သာ ဖြစ်ပါသည်။ `/play` ကို အသုံးပြုပါ။")
