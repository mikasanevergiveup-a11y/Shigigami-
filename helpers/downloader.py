"""
yt-dlp wrapper for downloading audio/video streams.
"""
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
    "geo_bypass": True,
}


async def search_youtube(query: str) -> dict:
    """
    Search YouTube for a query and return metadata for the top result.
    Returns dict with keys: title, url, duration, thumbnail.
    """
    opts = {
        **YDL_BASE_OPTS,
        "default_search": "ytsearch1",
        "skip_download": True,
        "extract_flat": False,
    }

    def _search():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info and info["entries"]:
                return info["entries"][0]
            return info

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _search)
        return {
            "title":     info.get("title", "Unknown"),
            "url":       info.get("webpage_url") or info.get("url"),
            "duration":  info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
        }
    except Exception as exc:
        raise DownloadError(f"Search failed: {exc}") from exc


async def download_audio(url: str) -> tuple[str, dict]:
    """
    Download best audio from *url* into DOWNLOADS_DIR.
    Returns (local_file_path, info_dict).
    """
    uid = uuid.uuid4().hex
    out_tmpl = os.path.join(config.DOWNLOADS_DIR, f"{uid}.%(ext)s")

    opts = {
        **YDL_BASE_OPTS,
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _download)
    except Exception as exc:
        raise DownloadError(f"Download failed: {exc}") from exc

    local_file = os.path.join(config.DOWNLOADS_DIR, f"{uid}.mp3")
    if not os.path.isfile(local_file):
        # Fallback: look for any file with that uid prefix
        for fname in os.listdir(config.DOWNLOADS_DIR):
            if fname.startswith(uid):
                local_file = os.path.join(config.DOWNLOADS_DIR, fname)
                break
        else:
            raise DownloadError("Downloaded file not found on disk.")

    return local_file, {
        "title":     info.get("title", "Unknown"),
        "url":       info.get("webpage_url") or url,
        "duration":  info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
    }


async def download_video(url: str) -> tuple[str, dict]:
    """
    Download best video+audio from *url* into DOWNLOADS_DIR as mp4.
    Returns (local_file_path, info_dict).
    """
    uid = uuid.uuid4().hex
    out_tmpl = os.path.join(config.DOWNLOADS_DIR, f"{uid}.%(ext)s")

    opts = {
        **YDL_BASE_OPTS,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_tmpl,
        "merge_output_format": "mp4",
    }

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _download)
    except Exception as exc:
        raise DownloadError(f"Video download failed: {exc}") from exc

    local_file = os.path.join(config.DOWNLOADS_DIR, f"{uid}.mp4")
    if not os.path.isfile(local_file):
        for fname in os.listdir(config.DOWNLOADS_DIR):
            if fname.startswith(uid):
                local_file = os.path.join(config.DOWNLOADS_DIR, fname)
                break
        else:
            raise DownloadError("Downloaded video file not found on disk.")

    return local_file, {
        "title":     info.get("title", "Unknown"),
        "url":       info.get("webpage_url") or url,
        "duration":  info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
    }
