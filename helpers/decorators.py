"""
Shared decorators used across handlers.
"""
import functools
import logging
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, ChannelInvalid
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

import config

logger = logging.getLogger(__name__)


def force_join(func):
    """
    Decorator that checks whether the invoking user has joined the
    mandatory channel before allowing any command to proceed.
    """
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else None
        if user_id is None:
            return await func(client, message, *args, **kwargs)

        try:
            member = await client.get_chat_member(
                f"@{config.FORCE_JOIN_CHANNEL}", user_id
            )
            # If user is banned / left, treat as not joined
            if member.status.value in ("left", "banned", "kicked"):
                raise UserNotParticipant
        except (UserNotParticipant, ChannelInvalid, Exception) as exc:
            if not isinstance(exc, UserNotParticipant):
                # Some other error — log and let through to avoid false blocks
                logger.warning("force_join check error: %s", exc)
                return await func(client, message, *args, **kwargs)

            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("📢 Join Channel", url=config.FORCE_JOIN_LINK),
                        InlineKeyboardButton("🔄 Try Again", callback_data="check_join"),
                    ]
                ]
            )
            await message.reply_text(
                "⚠️ **Access Restricted!**\n\n"
                "You must join our channel to use this bot.\n\n"
                f"👉 {config.FORCE_JOIN_LINK}",
                reply_markup=buttons,
                quote=True,
            )
            return  # halt command execution

        return await func(client, message, *args, **kwargs)

    return wrapper


def admin_only(func):
    """
    Decorator that allows only group admins (or the bot owner) to run a command.
    Falls through in private chats.
    """
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        if not message.chat or message.chat.type.value == "private":
            return await func(client, message, *args, **kwargs)

        user_id = message.from_user.id if message.from_user else None
        if user_id is None:
            await message.reply_text(
                "🥺 ဒီ command ကို သုံးဖို့ admin account နဲ့ ပြန်ပို့ပေးပါရှင်။",
                quote=True,
            )
            return

        try:
            member = await client.get_chat_member(message.chat.id, user_id)
            status = str(getattr(getattr(member, "status", ""), "value", member.status)).lower()
            if status not in ("administrator", "creator"):
                await message.reply_text(
                    "🚫 **Admin only ပါရှင်**\n"
                    "ဒီ command ကို Group Admin များသာ သုံးနိုင်ပါတယ်နော် ✨",
                    quote=True,
                )
                return
        except Exception as exc:
            logger.exception("admin_only permission check failed: %s", exc)
            await message.reply_text(
                "⚠️ Admin permission စစ်မရသေးပါရှင်။ Bot ကို Group Admin လုပ်ပေးပြီး ထပ်စမ်းပေးနော်။",
                quote=True,
            )
            return

        return await func(client, message, *args, **kwargs)

    return wrapper
