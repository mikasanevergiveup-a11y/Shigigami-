"""
/help command handler.
Also provides the text shown when the "Help & Commands" inline button is pressed.
"""
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
)
from helpers.decorators import force_join

HELP_TEXT = """🎵 **MUSIC BOT — COMMAND GUIDE**

━━━━━━━━━━━━━━━━━━━━━━
👥 **MEMBER COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
🎵 `/play <song name / link>` — Play music in group VC
🎬 `/vplay <video name / link>` — Play video stream in VC
📋 `/queue` — View the upcoming song queue
🎧 `/song <name>` — Download & send an audio file
🏓 `/ping` — Check bot response speed

━━━━━━━━━━━━━━━━━━━━━━
🔐 **ADMIN ONLY COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
⏸ `/pause` — Pause the current stream
▶️ `/resume` — Resume paused playback
⏭ `/skip` — Skip to the next song
⏹ `/end` or `/stop` — Stop VC streaming & clear queue
🔊 `/volume <1-200>` — Adjust playback volume
✅ `/auth <user>` — Authorize a user for admin commands
❌ `/unauth <user>` — Remove a user's authorization

━━━━━━━━━━━━━━━━━━━━━━
⚡️ Powered by @Mount_lvy"""

HELP_BACK_BUTTONS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("« Back", callback_data="back_home")]
    ]
)


def register_help(bot: Client) -> None:

    @bot.on_message(filters.command("help") & (filters.private | filters.group))
    @force_join
    async def help_command(client: Client, message: Message):
        await message.reply_text(
            HELP_TEXT,
            reply_markup=HELP_BACK_BUTTONS,
            quote=True,
        )
