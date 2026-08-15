"""Group moderation, mention-all, identity, and ping commands."""

import asyncio
import logging
import time
from collections import defaultdict
from html import escape
from typing import Dict, Optional, Set, Tuple

from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, Message, User

from helpers.decorators import admin_only

logger = logging.getLogger(__name__)

# In-memory state. It intentionally resets on a service redeploy.
KNOWN_MEMBERS: Dict[int, Dict[int, str]] = defaultdict(dict)
WARNINGS: Dict[Tuple[int, int], int] = defaultdict(int)
MENTION_TASKS: Dict[int, Tuple[asyncio.Task, asyncio.Event]] = {}


def _remember(message: Message) -> None:
    user = message.from_user
    if user and message.chat:
        name = " ".join(part for part in (user.first_name, user.last_name) if part).strip()
        KNOWN_MEMBERS[message.chat.id][user.id] = name or user.username or str(user.id)


def _display_name(user: User) -> str:
    return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.username or str(user.id)


async def _resolve_target(client: Client, message: Message) -> Optional[User]:
    """Resolve a replied-to user or the first username/user-id argument."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if len(message.command) < 2:
        return None

    raw = message.command[1].strip()
    if raw.startswith("@"):
        raw = raw[1:]

    try:
        return await client.get_users(int(raw))
    except (TypeError, ValueError):
        pass
    except Exception:
        return None

    try:
        return await client.get_users(raw)
    except Exception:
        return None


async def _cancel_mentions(chat_id: int) -> bool:
    running = MENTION_TASKS.pop(chat_id, None)
    if not running:
        return False
    task, stop_event = running
    stop_event.set()
    if not task.done():
        task.cancel()
    return True


async def _send_mentions(client: Client, chat_id: int, announcement: str, user_ids: Set[int], stop_event: asyncio.Event) -> None:
    """Send mention chunks and stop promptly when the admin cancels them."""
    members = KNOWN_MEMBERS.get(chat_id, {})
    mentions = [
        f'<a href="tg://user?id={user_id}">{escape(members.get(user_id, str(user_id)))}</a>'
        for user_id in sorted(user_ids)
        if user_id in members
    ]

    chunks = []
    current = f"📢 <b>{escape(announcement)}</b>\n\n"
    for mention in mentions:
        if len(current) + len(mention) + 1 > 3500:
            chunks.append(current)
            current = ""
        current += mention + " "
    if current.strip():
        chunks.append(current)

    try:
        for chunk in chunks:
            if stop_event.is_set():
                return
            await client.send_message(chat_id, chunk, parse_mode="html", disable_web_page_preview=True)
            await asyncio.sleep(0.35)
    except asyncio.CancelledError:
        logger.info("Mention-all cancelled for chat %s", chat_id)
        raise
    except Exception:
        logger.exception("Mention-all failed for chat %s", chat_id)
    finally:
        current_task = asyncio.current_task()
        active = MENTION_TASKS.get(chat_id)
        if active and active[0] is current_task:
            MENTION_TASKS.pop(chat_id, None)


def _full_permissions() -> ChatPermissions:
    return ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_send_polls=True,
        can_invite_users=True,
    )


def register_moderation(app: Client) -> None:
    """Register moderation and utility commands."""

    @app.on_message(filters.group, group=99)
    async def member_tracker(client: Client, message: Message):
        _remember(message)

    @app.on_message(filters.command("id") & (filters.private | filters.group))
    async def id_command(client: Client, message: Message):
        _remember(message)
        target = await _resolve_target(client, message)
        if target:
            await message.reply_text(
                f"🆔 **User ID:** `{target.id}`\n"
                f"👤 **Name:** {target.mention}"
            )
            return
        await message.reply_text(
            f"🆔 **Your ID:** `{message.from_user.id if message.from_user else 'Unknown'}`\n"
            f"💬 **Chat ID:** `{message.chat.id}`\n"
            f"📌 **Chat type:** `{message.chat.type.value}`"
        )

    @app.on_message(filters.command("ping") & (filters.private | filters.group))
    async def ping_command(client: Client, message: Message):
        started = time.perf_counter()
        response = await message.reply_text("🏓 **Pong! စစ်ဆေးနေပါသည်...**")
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        await response.edit_text(f"🏓 **Pong!**\n⚡ Response time: `{elapsed} ms`\n🟢 Bot is online.")

    @app.on_message(filters.command("ban") & filters.group)
    @admin_only
    async def ban_command(client: Client, message: Message):
        target = await _resolve_target(client, message)
        if not target:
            return await message.reply_text("အသုံးပြုပုံ: `/ban username` သို့မဟုတ် user message ကို reply လုပ်ပြီး `/ban` ပို့ပါ။")
        try:
            await client.ban_chat_member(message.chat.id, target.id)
            await message.reply_text(f"🚫 {target.mention} ကို ban လုပ်လိုက်ပါပြီ။")
        except Exception as exc:
            await message.reply_text(f"❌ Ban မလုပ်နိုင်ပါ: `{exc}`")

    @app.on_message(filters.command("unban") & filters.group)
    @admin_only
    async def unban_command(client: Client, message: Message):
        target = await _resolve_target(client, message)
        if not target:
            return await message.reply_text("အသုံးပြုပုံ: `/unban username` သို့မဟုတ် user message ကို reply လုပ်ပြီး `/unban` ပို့ပါ။")
        try:
            await client.unban_chat_member(message.chat.id, target.id, only_if_banned=True)
            await message.reply_text(f"✅ {target.mention} ကို unban လုပ်လိုက်ပါပြီ။")
        except Exception as exc:
            await message.reply_text(f"❌ Unban မလုပ်နိုင်ပါ: `{exc}`")

    @app.on_message(filters.command("warn") & filters.group)
    @admin_only
    async def warn_command(client: Client, message: Message):
        target = await _resolve_target(client, message)
        if not target:
            return await message.reply_text("အသုံးပြုပုံ: `/warn username` သို့မဟုတ် user message ကို reply လုပ်ပြီး `/warn` ပို့ပါ။")
        key = (message.chat.id, target.id)
        WARNINGS[key] += 1
        await message.reply_text(f"⚠️ {target.mention} ကို warn လုပ်လိုက်ပါပြီ။ စုစုပေါင်း warning: `{WARNINGS[key]}`")

    @app.on_message(filters.command("resetwarn") & filters.group)
    @admin_only
    async def resetwarn_command(client: Client, message: Message):
        target = await _resolve_target(client, message)
        if not target:
            return await message.reply_text("အသုံးပြုပုံ: `/resetwarn username` သို့မဟုတ် user message ကို reply လုပ်ပြီး `/resetwarn` ပို့ပါ။")
        WARNINGS.pop((message.chat.id, target.id), None)
        await message.reply_text(f"✅ {target.mention} ၏ warning များကို reset လုပ်လိုက်ပါပြီ။")

    @app.on_message(filters.command("mute") & filters.group)
    @admin_only
    async def mute_member_command(client: Client, message: Message):
        # No target means the existing music mute command may handle playback mute.
        target = await _resolve_target(client, message)
        if not target:
            return
        try:
            await client.restrict_chat_member(
                message.chat.id,
                target.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            await message.reply_text(f"🔇 {target.mention} ကို group ထဲမှာ mute လုပ်လိုက်ပါပြီ။")
        except Exception as exc:
            await message.reply_text(f"❌ Mute မလုပ်နိုင်ပါ: `{exc}`")

    @app.on_message(filters.command("unmute") & filters.group)
    @admin_only
    async def unmute_member_command(client: Client, message: Message):
        target = await _resolve_target(client, message)
        if not target:
            return
        try:
            await client.restrict_chat_member(
                message.chat.id,
                target.id,
                permissions=_full_permissions(),
            )
            await message.reply_text(f"🔊 {target.mention} ကို unmute လုပ်လိုက်ပါပြီ။")
        except Exception as exc:
            await message.reply_text(f"❌ Unmute မလုပ်နိုင်ပါ: `{exc}`")

    @app.on_message(filters.command("all") & filters.group)
    @admin_only
    async def all_command(client: Client, message: Message):
        announcement = ""
        if len(message.command) > 1:
            announcement = message.text.split(None, 1)[1].strip()
        elif message.reply_to_message:
            announcement = (message.reply_to_message.text or message.reply_to_message.caption or "").strip()
        if not announcement:
            return await message.reply_text("အသုံးပြုပုံ: `/all good night guys`\nသို့မဟုတ် စာတစ်စောင်ကို reply လုပ်ပြီး `/all` ပို့ပါ။")

        await _cancel_mentions(message.chat.id)
        user_ids = set(KNOWN_MEMBERS.get(message.chat.id, {}))
        if message.from_user:
            user_ids.add(message.from_user.id)
            _remember(message)
        if not user_ids:
            return await message.reply_text("ဒီ group မှာ mention လုပ်ရန် သိမ်းထားသော member မရှိသေးပါ။")

        stop_event = asyncio.Event()
        task = asyncio.create_task(_send_mentions(client, message.chat.id, announcement, user_ids, stop_event))
        MENTION_TASKS[message.chat.id] = (task, stop_event)
        await message.reply_text(f"📢 `{len(user_ids)}` ယောက်ကို mention စတင်ပို့နေပါပြီ။ ရပ်ရန် `/stop` ပို့ပါ။")

    @app.on_message(filters.command("stop") & filters.group)
    @admin_only
    async def stop_mentions_command(client: Client, message: Message):
        if await _cancel_mentions(message.chat.id):
            await message.reply_text("🛑 Member mention လုပ်နေမှုကို ချက်ချင်းရပ်လိုက်ပါပြီ။")
