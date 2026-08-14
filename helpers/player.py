import asyncio
import logging
from typing import Any, Dict
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from helpers.queue import get_queue, clear_queue, set_current
from helpers.streaming import start_stream, stop_stream

logger = logging.getLogger(__name__)

# Global variables
_bot: Any = None
_pytgcalls: Any = None
_current: Dict[int, dict] = {}


def set_refs(bot: Client, pytgcalls: Any) -> None:
    """Set global references for Bot and PyTgCalls instances."""
    global _bot, _pytgcalls
    _bot = bot
    _pytgcalls = pytgcalls
    logger.info("✅ PyTgCalls instance successfully attached to player helper!")


def fmt_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "Live Stream"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def now_playing_markup(chat_id: int) -> InlineKeyboardMarkup:
    """Generate Inline Keyboard buttons for music controls."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸ Pause", callback_data=f"pause_{chat_id}"),
                InlineKeyboardButton("▶️ Resume", callback_data=f"resume_{chat_id}"),
                InlineKeyboardButton("⏭ Skip", callback_data=f"skip_{chat_id}"),
            ],
            [
                InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{chat_id}"),
            ],
        ]
    )


def _get_stream_object(fifo_path: str) -> Any:
    """Dynamically create stream object without triggering Linter red squiggles."""
    try:
        from pytgcalls.types import MediaStream
        return MediaStream(fifo_path)
    except Exception:
        try:
            from pytgcalls.types import AudioPiped
            return AudioPiped(fifo_path)
        except Exception as e:
            logger.warning(f"Could not load pytgcalls stream types: {e}")
            return fifo_path


async def pause_playback(chat_id: int) -> bool:
    """Pause the current stream."""
    if _pytgcalls:
        try:
            if hasattr(_pytgcalls, "pause_stream"):
                return await _pytgcalls.pause_stream(chat_id)
            elif hasattr(_pytgcalls, "pause"):
                return await _pytgcalls.pause(chat_id)
        except Exception as e:
            logger.error(f"Error pausing stream in {chat_id}: {e}")
    return False


async def resume_playback(chat_id: int) -> bool:
    """Resume the paused stream."""
    if _pytgcalls:
        try:
            if hasattr(_pytgcalls, "resume_stream"):
                return await _pytgcalls.resume_stream(chat_id)
            elif hasattr(_pytgcalls, "resume"):
                return await _pytgcalls.resume(chat_id)
        except Exception as e:
            logger.error(f"Error resuming stream in {chat_id}: {e}")
    return False


async def set_volume(chat_id: int, volume: int) -> bool:
    """Set playback volume (1-200)."""
    if _pytgcalls:
        try:
            if hasattr(_pytgcalls, "change_volume_call"):
                return await _pytgcalls.change_volume_call(chat_id, volume)
            elif hasattr(_pytgcalls, "set_volume"):
                return await _pytgcalls.set_volume(chat_id, volume)
        except Exception as e:
            logger.error(f"Error setting volume in {chat_id}: {e}")
    return False


async def mute_playback(chat_id: int) -> bool:
    """Mute current stream."""
    if _pytgcalls:
        try:
            if hasattr(_pytgcalls, "mute_stream"):
                return await _pytgcalls.mute_stream(chat_id)
        except Exception as e:
            logger.error(f"Error muting stream in {chat_id}: {e}")
    return False


async def unmute_playback(chat_id: int) -> bool:
    """Unmute current stream."""
    if _pytgcalls:
        try:
            if hasattr(_pytgcalls, "unmute_stream"):
                return await _pytgcalls.unmute_stream(chat_id)
        except Exception as e:
            logger.error(f"Error unmuting stream in {chat_id}: {e}")
    return False


async def stop_playback(chat_id: int) -> None:
    """Stop stream, clear queue, and leave voice chat."""
    stop_stream(chat_id)
    clear_queue(chat_id)
    if chat_id in _current:
        del _current[chat_id]

    if _pytgcalls:
        try:
            if hasattr(_pytgcalls, "leave_call"):
                await _pytgcalls.leave_call(chat_id)
            elif hasattr(_pytgcalls, "leave_group_call"):
                await _pytgcalls.leave_group_call(chat_id)
        except Exception as exc:
            logger.error(f"Error leaving call for {chat_id}: {exc}")


async def play_next(chat_id: int):
    """Play the next track in queue or stop if empty."""
    q_data = get_queue(chat_id)

    if isinstance(q_data, list) and len(q_data) > 0:
        next_track = q_data.pop(0)
        await play_track(chat_id, next_track)
        return next_track
    else:
        await stop_playback(chat_id)
        return None


async def play_track(chat_id: int, track: dict) -> None:
    """Start playing a track in the specified chat using pytgcalls."""
    if not _pytgcalls:
        raise Exception("PyTgCalls is not initialized! (set_refs was not called)")

    fifo_path = start_stream(chat_id, track["stream_url"])

    # Wait 1s for FFmpeg buffer
    await asyncio.sleep(1)

    _current[chat_id] = track
    set_current(chat_id, track)

    stream_obj = _get_stream_object(fifo_path)

    try:
        if hasattr(_pytgcalls, "play"):
            await _pytgcalls.play(chat_id, stream_obj)
        elif hasattr(_pytgcalls, "join_group_call"):
            await _pytgcalls.join_group_call(chat_id, stream_obj)
    except Exception:
        try:
            if hasattr(_pytgcalls, "change_stream"):
                await _pytgcalls.change_stream(chat_id, stream_obj)
        except Exception as e:
            logger.error(f"Error playing track in {chat_id}: {e}")
            raise
            