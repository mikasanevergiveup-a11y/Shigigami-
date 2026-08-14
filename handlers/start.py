"""
/start handler — sends welcome banner + inline keyboard.
"""
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
)

import config
from helpers.decorators import force_join

logger = logging.getLogger(__name__)

WELCOME_TEXT = """✦ **WELCOME TO MUSIC BOT** ✦

Hey {first_name}!
I am your premium music companion for Telegram Voice Chats.

🚀 Fast • 🎧 High Quality Audio
🧠 Smart Queue • ⚡️ Powerful Playback
👥 Group Friendly • 📻 24/7 Music

───────────────────────
👤 **Your Profile**
User: {mention}
ID: `{user_id}`

Use /help to view all available commands.

⚡️ Powered by {powered_by}"""

WELCOME_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("↗ Channels",  url=config.CHANNEL_LINK),
            InlineKeyboardButton("📢 Updates",   url=config.UPDATES_LINK),
        ],
        [
            InlineKeyboardButton("🐺 Owner",    url=config.OWNER_LINK),
            InlineKeyboardButton("💬 Support",  url=config.SUPPORT_LINK),
        ],
        [
            InlineKeyboardButton("🟢 Help & Commands", callback_data="help_menu"),
        ],
    ]
)


def register_start(bot: Client) -> None:

    @bot.on_message(filters.command("start") & (filters.private | filters.group))
    @force_join
    async def start_handler(client: Client, message: Message):
        user = message.from_user
        text = WELCOME_TEXT.format(
            first_name=user.first_name,
            mention=user.mention,
            user_id=user.id,
            powered_by=config.POWERED_BY,
        )

        banner = config.BANNER_PATH
        if os.path.isfile(banner):
            await message.reply_photo(
                photo=banner,
                caption=text,
                reply_markup=WELCOME_BUTTONS,
                quote=True,
            )
        else:
            await message.reply_text(
                text,
                reply_markup=WELCOME_BUTTONS,
                quote=True,
            )
