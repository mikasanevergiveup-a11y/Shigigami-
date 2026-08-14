async def _check_cb_control(client, cq) -> bool:
    """Return True if the button presser is a group admin."""
    try:
        # Determine the chat_id from the callback data
        chat_id = int(cq.data.split("_")[1])
        member = await client.get_chat_member(chat_id, cq.from_user.id)
        
        # Pyrogram version အဟောင်း/အသစ် ၂ ခုလုံးမှာ Admin စစ်ဆေးမှု မမှားစေရန်
        status_str = str(member.status).lower()
        if "administrator" in status_str or "creator" in status_str or "owner" in status_str:
            return True
    except Exception as exc:
        logger.error(f"Error checking admin status: {exc}")
        
    await cq.answer("🚫 Only admins can use playback controls.", show_alert=True)
    return False


def register_callbacks(bot,call_factory=None):
    
    # ── Stop ──────────────────────────────────────────────────────────────────
    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("stop_"))
    async def stop_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.split("_")[1])
        clear_queue(chat_id)
        await stop_playback(chat_id)
        await cq.message.edit_text("⏹ **Playback stopped and queue cleared.**")
        await cq.answer("⏹ Stopped!")

    # ── Loop toggle ───────────────────────────────────────────────────────────
    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("loop_"))
    async def loop_cb(client, cq):
        if not await _check_cb_control(client, cq):
            return
        chat_id = int(cq.data.split("_")[1])
        state = toggle_loop(chat_id)
        status = "enabled 🔂" if state else "disabled 🔁"
        await cq.message.edit_reply_markup(now_playing_markup(chat_id))
        await cq.answer(f"Loop {status}")

    # ── Queue view ────────────────────────────────────────────────────────────
    @bot.on_callback_query(lambda _, cq: cq.data and cq.data.startswith("queue_"))
    async def queue_cb(client, cq):
        chat_id = int(cq.data.split("_")[1])
        current = get_current(chat_id)
        upcoming = queue_list(chat_id)

        if not current and not upcoming:
            return await cq.answer("📭 Queue is empty.", show_alert=True)

        lines = []
        if current:
            lines.append(f"▶️ Now: {current['title']} [{fmt_duration(current.get('duration', 0))}]")
        for i, t in enumerate(upcoming[:7], 1):
            lines.append(f"{i}. {t['title']} [{fmt_duration(t.get('duration', 0))}]")
        if len(upcoming) > 7:
            lines.append(f"… +{len(upcoming)-7} more")

        await cq.answer("\n".join(lines)[:200], show_alert=True)
        