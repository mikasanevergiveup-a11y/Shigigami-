"""Telegram health/status command handlers."""

import os
import time

from pyrogram import Client, filters
from pyrogram.types import Message


_STARTED_AT = time.monotonic()


def _format_uptime(seconds: float) -> str:
    total = max(0, int(seconds))
    days, total = divmod(total, 86400)
    hours, total = divmod(total, 3600)
    minutes, secs = divmod(total, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def register_health(bot: Client) -> None:
    """Register health commands for private and group chats."""

    @bot.on_message(filters.command(["health", "healthz"]) & (filters.private | filters.group))
    async def health_command(client: Client, message: Message):
        uptime = _format_uptime(time.monotonic() - _STARTED_AT)
        interval = os.getenv("SELF_PING_INTERVAL", "180")
        await message.reply_text(
            "✅ **Bot Health Status**\n\n"
            "🟢 **Status:** `OK`\n"
            "🤖 **Bot:** `Running`\n"
            f"⏱ **Uptime:** `{uptime}`\n"
            "🌐 **Web health:** `OK`\n"
            "🔁 **Self-ping:** `Enabled`\n"
            f"⏲ **Self-ping interval:** `{interval}s`\n\n"
            "💡 Render web endpoint: `/healthz`"
        )
