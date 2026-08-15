"""
/help command handler.
Also provides the text shown when the "Help & Commands" inline button is pressed.
"""
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from helpers.decorators import force_join


HELP_TEXT = """✨ **MUSIC BOT — အသုံးပြုနိုင်သော Commands** ✨

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

HELP_BACK_BUTTONS = InlineKeyboardMarkup(
    [[InlineKeyboardButton("« Back", callback_data="back_home")]]
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
