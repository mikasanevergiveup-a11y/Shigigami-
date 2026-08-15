import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from helpers.streaming import extract_stream_info
from helpers.player import (
    play_track, 
    now_playing_markup, 
    fmt_duration,
    pause_playback, 
    resume_playback, 
    stop_playback, 
    play_next
)
from helpers.queue import add_to_queue, get_queue, get_current, clear_queue

logger = logging.getLogger(__name__)

# Owner Username
OWNER_USERNAME = "Mount_lvy"

# Start Banner Image URL
START_IMAGE_URL = "https://telegra.ph/file/f02e6503b22c7104e6c38.jpg"

MUSIC_HELP_TEXT = """✨ **MUSIC BOT — အသုံးပြုနိုင်သော Commands** ✨

━━━━━━━━━━━━━━━━━━━━━━
📌 **အထွေထွေ Commands**
━━━━━━━━━━━━━━━━━━━━━━
• `/start` — Bot ကို စတင်ရန်
• `/help` — ဒီ command list ကို ကြည့်ရန်

━━━━━━━━━━━━━━━━━━━━━━
👥 **Member Commands**
━━━━━━━━━━━━━━━━━━━━━━
• `/play <သီချင်းအမည် သို့မဟုတ် link>` — Voice Chat တွင် သီချင်းဖွင့်ရန်
• `/vplay <ဗီဒီယိုအမည် သို့မဟုတ် link>` — Voice Chat တွင် video stream ဖွင့်ရန်
• `/queue` သို့မဟုတ် `/list` — လက်ရှိ queue ကို ကြည့်ရန်

━━━━━━━━━━━━━━━━━━━━━━
🔐 **Playback/Admin Commands**
━━━━━━━━━━━━━━━━━━━━━━
• `/pause` — လက်ရှိ playback ကို ခဏရပ်ရန်
• `/resume` — ရပ်ထားသော playback ကို ပြန်ဖွင့်ရန်
• `/skip` သို့မဟုတ် `/next` — နောက်သီချင်းသို့ ကျော်ရန်
• `/stop` သို့မဟုတ် `/end` — Playback ရပ်ပြီး Voice Chat မှ ထွက်ရန်
• `/clearqueue` သို့မဟုတ် `/cq` — Queue ထဲရှိ သီချင်းများကို ရှင်းရန်
• `/volume <1-200>` သို့မဟုတ် `/vol <1-200>` — အသံအတိုးအကျယ် ပြောင်းရန်
• `/mute` — အသံပိတ်ရန်
• `/unmute` — အသံပြန်ဖွင့်ရန်

💡 Command များကို Group Voice Chat ထဲတွင် အသုံးပြုပါ။

⚡️ Powered by @Mount_lvy"""

# Broadcast ပို့ရန် Chat စာရင်းများကို မှတ်ထားရန်
SERVED_CHATS = set()


def register_music(app: Client, user_client=None):
    """Register all music commands and handlers."""

    # ── 1. START COMMAND ──────────────────────────────────────────────────────
    @app.on_message(filters.command(["start", "start@bot"]))
    async def start_cmd(client: Client, message: Message):
        SERVED_CHATS.add(message.chat.id)
        user = message.from_user
        user_name = user.mention if user else "User"
        user_id = user.id if user else "Unknown"

        text = (
            f"✨ **WELCOME TO MUSIC BOT** 💫\n\n"
            f"Hey {user_name}! 👋\n"
            f"I'm your premium music companion for Telegram Voice Chats.\n\n"
            f"🚀 **Fast** • 🔴 **High Quality Audio**\n"
            f"🧠 **Smart Queue** • ⚡ **Powerful Playback**\n"
            f"👥 **Group Friendly** • 🎧 **24/7 Music**\n"
            f"───────────────────────────\n\n"
            f"👤 **Your Profile**\n"
            f"👤 User: {user_name}\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"👇 Use **/help** or click buttons below to view available commands."
        )

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 Channels", url="https://t.me/musicbotmegaliana"),
                InlineKeyboardButton("📣 Updates", url="https://t.me/musicbotmegaliana"),
            ],
            [
                InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}"),
                InlineKeyboardButton("💬 Support", url="https://t.me/musicbotmegaliana1"),
            ],
            [
                InlineKeyboardButton("❓ Help & Commands", callback_data="help_menu"),
            ]
        ])

        try:
            await message.reply_photo(photo=START_IMAGE_URL, caption=text, reply_markup=buttons)
        except Exception:
            await message.reply_text(text=text, reply_markup=buttons)

    # ── 2. HELP COMMAND ───────────────────────────────────────────────────────
    @app.on_message(filters.command(["help", "help@bot"]))
    async def help_cmd(client: Client, message: Message):
        SERVED_CHATS.add(message.chat.id)
        
        text = MUSIC_HELP_TEXT
        
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        await message.reply_text(text=text, reply_markup=buttons)

    # ── 3. PRIVATE CHAT HANDLER (BOT TO USER) ─────────────────────────────────
    @app.on_message(filters.private & ~filters.command(["start", "help", "bc", "broadcast"]))
    async def private_chat_handler(client: Client, message: Message):
        SERVED_CHATS.add(message.chat.id)
        await message.reply_text(
            "👋 **မင်္ဂလာပါခင်ဗျာ!**\n\n"
            "သီချင်းနားထောင်လိုပါက Bot ကို **Group ထဲသို့ Add** ပြီးမှ `/play <သီချင်းအမည်>` ဟု အသုံးပြုပေးပါခင်ဗျာ။\n\n"
            "💡 အကူအညီအတွက် `/help` ကို နှိပ်၍ ကြည့်ရှုနိုင်ပါသည်။"
        )

    # ── 4. PLAY COMMAND ───────────────────────────────────────────────────────
    @app.on_message(filters.command(["play", "vplay"]) & filters.group)
    async def play_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        SERVED_CHATS.add(chat_id)

        if len(message.command) < 2 and not message.reply_to_message:
            return await message.reply_text("💡 အသုံးပြုပုံ: `/play <သီချင်းအမည်>`")

        if message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text
        else:
            query = message.text.split(None, 1)[1]

        m = await message.reply_text("🔍 သီချင်း ရှာဖွေနေပါသည်...")

        try:
            # yt-dlp is synchronous; keep it off Pyrogram's event loop.
            track = await asyncio.wait_for(
                asyncio.to_thread(extract_stream_info, query),
                timeout=45,
            )
            track["requested_by"] = message.from_user.mention if message.from_user else "User"
        except asyncio.TimeoutError:
            return await m.edit_text(
                "⏳ သီချင်းရှာဖွေမှု ကြာနေပါသည်။ YouTube verification ဖြစ်နေနိုင်သဖြင့် "
                "direct YouTube link ဖြင့် ထပ်စမ်းပါ။"
            )
        except Exception as err:
            return await m.edit_text(f"❌ Error: {err}")

        try:
            duration_str = fmt_duration(track["duration"])
        except Exception:
            duration_str = str(track.get("duration", "4:50"))

        thumb = track.get("thumbnail") or START_IMAGE_URL

        q = get_queue(chat_id)
        # Queue when a track is currently playing; the old code only checked
        # whether the waiting queue already had an item, so the second track
        # incorrectly replaced/started instead of being queued.
        if get_current(chat_id) is not None or q:
            position = add_to_queue(chat_id, track)
            await m.edit_text(
                f"🎵 **Queue ထဲသို့ ထည့်လိုက်ပါပြီ!** (#{position})\n\n"
                f"📌 **ခေါင်းစဉ်:** [{track['title']}]({track.get('url', track.get('webpage_url', ''))})\n"
                f"⏱ **ကြာမြင့်ချိန်:** `{duration_str}`"
            )
        else:
            try:
                await play_track(chat_id, track)
                await m.delete()

                caption = (
                    f"🎵 **Started Streaming** | ❝\n\n"
                    f"📌 **Title :** `{track['title']}`\n"
                    f"⏱ **Duration :** `{duration_str}` Minutes\n"
                    f"👤 **Requested By :** {track['requested_by']}"
                )

                buttons = now_playing_markup(chat_id) if callable(now_playing_markup) else None

                try:
                    await message.reply_photo(
                        photo=thumb,
                        caption=caption,
                        reply_markup=buttons
                    )
                except Exception:
                    await message.reply_text(
                        text=caption,
                        reply_markup=buttons,
                        disable_web_page_preview=True
                    )

            except Exception as e:
                logger.error(f"Play Track Error: {e}")
                await message.reply_text(
                    f"❌ **Voice Chat Error:** {e}\n\n"
                    "💡 **စစ်ဆေးရန်:**\n"
                    "1. Telegram Group ထဲတွင် Group Voice Chat ကို Start ထားပါသလား။\n"
                    "2. Assistant အကောင့်ကို Group ထဲသို့ Add ထားပါသလား။"
                )

    # ── 5. PLAYER CONTROL COMMANDS (PAUSE, RESUME, SKIP, STOP, QUEUE) ────────
    @app.on_message(filters.command(["pause"]) & filters.group)
    async def pause_cmd(client: Client, message: Message):
        try:
            await pause_playback(message.chat.id)
            await message.reply_text("⏸ **သီချင်းခေတ္တ ခေတ္တရပ်လိုက်ပါပြီ (Paused)!**")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    @app.on_message(filters.command(["resume"]) & filters.group)
    async def resume_cmd(client: Client, message: Message):
        try:
            await resume_playback(message.chat.id)
            await message.reply_text("▶️ **သီချင်း ပြန်လည်ဖွင့်လိုက်ပါပြီ (Resumed)!**")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    @app.on_message(filters.command(["skip", "next"]) & filters.group)
    async def skip_cmd(client: Client, message: Message):
        try:
            next_track = await play_next(message.chat.id)
            if next_track:
                await message.reply_text(f"⏭ **နောက်သီချင်းသို့ ကူးလိုက်ပါပြီ:** `{next_track['title']}`")
            else:
                await message.reply_text("⏭ **သီချင်း ကျော်လိုက်ပါပြီ! Queue ထဲတွင် သီချင်းကုန်သွားပါပြီ။**")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    @app.on_message(filters.command(["stop", "end"]) & filters.group)
    async def stop_cmd(client: Client, message: Message):
        try:
            await stop_playback(message.chat.id)
            await message.reply_text("🛑 **သီချင်းဖွင့်ခြင်းကို ရပ်ဆိုင်းလိုက်ပါပြီ!**")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    @app.on_message(filters.command(["queue", "list"]) & filters.group)
    async def queue_cmd(client: Client, message: Message):
        q = get_queue(message.chat.id)
        if not q:
            return await message.reply_text("📜 **Queue ထဲတွင် သီချင်း မရှိသေးပါခင်ဗျာ!**")
        
        text = "📜 **လက်ရှိ Queue ထဲရှိ သီချင်းများ:**\n\n"
        for idx, track in enumerate(q, 1):
            text += f"{idx}. `{track['title']}`\n"
        await message.reply_text(text)

    @app.on_message(filters.command(["clearqueue", "cq"]) & filters.group)
    async def clearqueue_cmd(client: Client, message: Message):
        try:
            clear_queue(message.chat.id)
            await message.reply_text("🗑️ **Queue ထဲရှိ သီချင်းအားလုံးကို ရှင်းလင်းလိုက်ပါပြီ!**")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    # ── 6. OWNER REPLY BROADCAST COMMAND (/bc) ─────────────────────────────────
    @app.on_message(filters.command(["bc", "broadcast"]))
    async def broadcast_cmd(client: Client, message: Message):
        user = message.from_user
        if not user or (user.username and user.username.lower() != OWNER_USERNAME.lower()):
            return await message.reply_text("❌ **ဒီ Command ကို Bot Owner သာ သုံးခွင့်ရှိပါတယ်ခင်ဗျာ!**")

        if not message.reply_to_message:
            return await message.reply_text("💡 **အသုံးပြုပုံ:** Broadcast လုပ်ချင်သည့် စာ သို့မဟုတ် ပုံကို Reply လိုက်ပြီး `/bc` ဟု ရိုက်ပေးပါခင်ဗျာ။")

        status_msg = await message.reply_text("📢 **Broadcast စတင် ပို့ဆောင်နေပါသည်...**")
        sent = 0
        failed = 0

        for cid in list(SERVED_CHATS):
            try:
                await message.reply_to_message.copy(chat_id=cid)
                sent += 1
                await asyncio.sleep(0.3)
            except Exception:
                failed += 1

        await status_msg.edit_text(
            f"✅ **Broadcast ပို့ဆောင်ခြင်း ပြီးစီးပါပြီခင်ဗျာ!**\n\n"
            f"🎯 **အောင်မြင်စွာ ရောက်ရှိခဲ့သည်:** `{sent}` Chats\n"
            f"❌ **မရောက်ရှိခဲ့ပါ:** `{failed}` Chats"
        )

    # ── 7. CALLBACK QUERY HANDLER FOR BUTTONS ──────────────────────────────────
    @app.on_callback_query()
    async def callback_handler(client: Client, query: CallbackQuery):
        data = query.data

        if data == "help_menu":
            text = MUSIC_HELP_TEXT
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            await query.message.edit_text(text=text, reply_markup=buttons)

        elif data == "main_menu":
            user = query.from_user
            user_name = user.mention if user else "User"
            user_id = user.id if user else "Unknown"

            text = (
                f"✨ **WELCOME TO MUSIC BOT** 💫\n\n"
                f"Hey {user_name}! 👋\n"
                f"I'm your premium music companion for Telegram Voice Chats.\n\n"
                f"🚀 **Fast** • 🔴 **High Quality Audio**\n"
                f"🧠 **Smart Queue** • ⚡ **Powerful Playback**\n"
                f"👥 **Group Friendly** • 🎧 **24/7 Music**\n"
                f"───────────────────────────\n\n"
                f"👤 **Your Profile**\n"
                f"👤 User: {user_name}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"👇 Use **/help** or click buttons below to view available commands."
            )

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📢 Channels", url="https://t.me/musicbotmegaliana"),
                    InlineKeyboardButton("📣 Updates", url="https://t.me/musicbotmegaliana"),
                ],
                [
                    InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}"),
                    InlineKeyboardButton("💬 Support", url="https://t.me/musicbotmegaliana1"),
                ],
                [
                    InlineKeyboardButton("❓ Help & Commands", callback_data="help_menu"),
                ]
            ])
            await query.message.edit_text(text=text, reply_markup=buttons)

        elif data == "close_panel":
            await query.message.delete()
            