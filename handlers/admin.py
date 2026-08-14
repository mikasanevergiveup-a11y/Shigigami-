import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from helpers.player import (
    pause_playback,
    resume_playback,
    stop_playback,
    set_volume,
    mute_playback,
    unmute_playback,
    play_next,
)

logger = logging.getLogger(__name__)


def register_admin(app: Client, *args, **kwargs):
    """Register all admin music commands (accepts extra arguments safely)."""

    @app.on_message(filters.command(["pause"]) & filters.group)
    async def pause_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        if await pause_playback(chat_id):
            await message.reply_text("⏸ သီချင်းကို ခေတ္တရပ်လိုက်ပါပြီ။")
        else:
            await message.reply_text("❌ သီချင်း ဖွင့်မထားပါ သို့မဟုတ် ရပ်၍ မရပါ။")

    @app.on_message(filters.command(["resume"]) & filters.group)
    async def resume_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        if await resume_playback(chat_id):
            await message.reply_text("▶️ သီချင်းကို ပြန်ဖွင့်လိုက်ပါပြီ။")
        else:
            await message.reply_text("❌ ပြန်ဖွင့်ရန် သီချင်းမရှိပါ။")

    @app.on_message(filters.command(["stop", "end"]) & filters.group)
    async def stop_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        await stop_playback(chat_id)
        await message.reply_text("🛑 သီချင်းဖွင့်စနစ်ကို ရပ်တန့်လိုက်ပါပြီ။")

    @app.on_message(filters.command(["skip", "next"]) & filters.group)
    async def skip_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        next_track = await play_next(chat_id)
        if next_track:
            title = next_track.get("title", "Unknown")
            await message.reply_text(f"⏭ နောက်သီချင်းသို့ ကူးလိုက်ပါပြီ: **{title}**")
        else:
            await message.reply_text("⏭ Queue ထဲမှာ နောက်သီချင်း မရှိတော့ပါခင်ဗျာ။")

    @app.on_message(filters.command(["vol", "volume"]) & filters.group)
    async def volume_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) < 2:
            return await message.reply_text("💡 အသုံးပြုပုံ: `/volume 1-200` (ဥပမာ: `/volume 100`)")
        try:
            vol = int(message.command[1])
            if vol < 1 or vol > 200:
                return await message.reply_text("⚠️ Volume ပမာဏကို 1 မှ 200 အထိသာ သတ်မှတ်ပါ။")
            if await set_volume(chat_id, vol):
                await message.reply_text(f"🔊 Volume ကို **{vol}%** သို့ ပြောင်းလိုက်ပါပြီ။")
            else:
                await message.reply_text("❌ Volume ပြောင်း၍ မရပါခင်ဗျာ။")
        except ValueError:
            await message.reply_text("⚠️ ကျေးဇူးပြု၍ ကိန်းဂဏန်းသာ ရိုက်ထည့်ပါ။")

    @app.on_message(filters.command(["mute"]) & filters.group)
    async def mute_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        if await mute_playback(chat_id):
            await message.reply_text("🔇 အသံ ပိတ်လိုက်ပါပြီ။")
        else:
            await message.reply_text("❌ အသံ ပိတ်၍ မရပါခင်ဗျာ။")

    @app.on_message(filters.command(["unmute"]) & filters.group)
    async def unmute_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        if await unmute_playback(chat_id):
            await message.reply_text("🔊 အသံ ပြန်ဖွင့်လိုက်ပါပြီ။")
        else:
            await message.reply_text("❌ အသံ ပြန်ဖွင့်၍ မရပါခင်ဗျာ။")
            