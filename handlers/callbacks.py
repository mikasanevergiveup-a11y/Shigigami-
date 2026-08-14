import logging

import config
from helpers.player import (
    fmt_duration,
    mute_playback,
    now_playing_markup,
    pause_playback,
    play_next,
    resume_playback,
    set_volume,
    stop_playback,
    unmute_playback,
)
from helpers.queue import clear_queue, get_current, is_loop, queue_list, toggle_loop

logger = logging.getLogger(__name__)


async def _check_cb_control(client, cq) -> bool:
    """Return True when the callback presser is a group admin/owner."""
    try:
        chat_id = int(cq.data.rsplit("_", 1)[1])
        member = await client.get_chat_member(chat_id, cq.from_user.id)
        status = str(member.status).lower()
        if any(role in status for role in ("administrator", "creator", "owner")):
            return True
    except Exception as exc:
        logger.warning("Could not verify callback permissions: %s", exc)

    await cq.answer("🚫 Only group admins can use playback controls.", show_alert=True)
    return False


def register_callbacks(bot, call_factory=None):
    """Register all inline playback controls on the bot client."""

    @bot.on_callback_query(lambda _, cq: cq.data == "check_join")
    async def check_join_cb(client, cq):
        """Re-check force-join status without requiring a new /start or /help."""
        try:
            member = await client.get_chat_member(
                f"@{config.FORCE_JOIN_CHANNEL}",
                cq.from_user.id,
            )
            status = str(member.status).lower()
            if any(role in status for role in ("member", "administrator", "creator", "owner")):
                await cq.answer("✅ Verification complete")
                try:
                    await cq.message.delete()
                except Exception:
                    pass
                return
        except Exception as exc:
            logger.warning("check_join failed: %s", exc)
        await cq.answer("❌ Please join the channel first, then try again.", show_alert=True)

    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("pause_"))
    async def pause_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.rsplit("_", 1)[1])
        ok = await pause_playback(chat_id)
        await cq.answer("⏸ Paused" if ok else "Unable to pause", show_alert=not ok)

    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("resume_"))
    async def resume_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.rsplit("_", 1)[1])
        ok = await resume_playback(chat_id)
        await cq.answer("▶️ Resumed" if ok else "Unable to resume", show_alert=not ok)

    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("skip_"))
    async def skip_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.rsplit("_", 1)[1])
        try:
            track = await play_next(chat_id)
            if track:
                await cq.answer(f"⏭ {track.get('title', 'Next track')}")
            else:
                await cq.answer("Queue is empty", show_alert=True)
        except Exception as exc:
            logger.error("Skip callback failed: %s", exc)
            await cq.answer("❌ Could not skip", show_alert=True)

    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("stop_"))
    async def stop_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.rsplit("_", 1)[1])
        await stop_playback(chat_id)
        await cq.answer("⏹ Stopped and queue cleared")
        try:
            await cq.message.edit_reply_markup(None)
        except Exception:
            pass

    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("loop_"))
    async def loop_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.rsplit("_", 1)[1])
        state = toggle_loop(chat_id)
        await cq.answer("🔂 Loop enabled" if state else "🔁 Loop disabled")

    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("queue_"))
    async def queue_cb(client, cq):
        chat_id = int(cq.data.rsplit("_", 1)[1])
        current = get_current(chat_id)
        upcoming = queue_list(chat_id)
        if not current and not upcoming:
            return await cq.answer("📭 Queue is empty.", show_alert=True)

        lines = []
        if current:
            lines.append(
                f"▶️ Now: {current.get('title', 'Unknown')} "
                f"[{fmt_duration(current.get('duration', 0))}]"
            )
        for index, track in enumerate(upcoming[:7], 1):
            lines.append(
                f"{index}. {track.get('title', 'Unknown')} "
                f"[{fmt_duration(track.get('duration', 0))}]"
            )
        if len(upcoming) > 7:
            lines.append(f"… +{len(upcoming) - 7} more")
        await cq.answer("\n".join(lines)[:200], show_alert=True)

    return True
