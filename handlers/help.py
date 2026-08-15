"""Canonical Burmese help menu for the music and moderation bot."""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from helpers.decorators import force_join


HELP_TEXT = """✨ **MUSIC BOT — အသုံးပြုနိုင်သော Commands** ✨

━━━━━━━━━━━━━━━━━━━━━━
🆔 **Information**
━━━━━━━━━━━━━━━━━━━━━━
• `/id` — မိမိ User ID နှင့် Group/Chat ID ကြည့်ရန်
  ဥပမာ: `/id` သို့မဟုတ် user message ကို reply လုပ်ပြီး `/id`
• `/ping` — Bot online ဖြစ်/မဖြစ် စစ်ရန်
  ဥပမာ: `/ping`
• `/health` သို့မဟုတ် `/healthz` — Bot uptime နှင့် self-ping status စစ်ရန်
  ဥပမာ: `/healthz`

━━━━━━━━━━━━━━━━━━━━━━
⚙️ **General**
━━━━━━━━━━━━━━━━━━━━━━
• `/start` — Bot ၏ welcome message ကို ပြရန်
  ဥပမာ: `/start`
• `/help` — ဒီ command menu ကို ပြရန်
  ဥပမာ: `/help`

━━━━━━━━━━━━━━━━━━━━━━
👥 **Member / Music**
━━━━━━━━━━━━━━━━━━━━━━
• `/play <သီချင်းအမည် သို့မဟုတ် link>` — Voice Chat တွင် သီချင်းဖွင့်ရန်
  ဥပမာ: `/play သီချင်းအမည်`
• `/vplay <ဗီဒီယိုအမည် သို့မဟုတ် link>` — Video stream ဖွင့်ရန်
  ဥပမာ: `/vplay https://youtu.be/...`
• `/queue` သို့မဟုတ် `/list` — လက်ရှိ queue ကို ကြည့်ရန်
  ဥပမာ: `/queue`

━━━━━━━━━━━━━━━━━━━━━━
🔐 **Admin / Playback**
━━━━━━━━━━━━━━━━━━━━━━
• `/pause` — လက်ရှိ playback ကို ခဏရပ်ရန်
  ဥပမာ: `/pause`
• `/resume` — ရပ်ထားသော playback ကို ပြန်ဖွင့်ရန်
  ဥပမာ: `/resume`
• `/skip` သို့မဟုတ် `/next` — နောက်သီချင်းသို့ ကျော်ရန်
  ဥပမာ: `/skip`
• `/stop` သို့မဟုတ် `/end` — Playback ရပ်ပြီး Voice Chat မှ ထွက်ရန်
  ဥပမာ: `/stop`
• `/clearqueue` သို့မဟုတ် `/cq` — Queue ရှင်းရန်
  ဥပမာ: `/clearqueue`
• `/volume <1-200>` သို့မဟုတ် `/vol <1-200>` — အသံအတိုးအကျယ်ပြောင်းရန်
  ဥပမာ: `/volume 100`

━━━━━━━━━━━━━━━━━━━━━━
🛡️ **Moderation (Group Admin Only)**
━━━━━━━━━━━━━━━━━━━━━━
• `/ban username` — Member ကို group မှ ban လုပ်ရန်
  ဥပမာ: `/ban @username` သို့မဟုတ် user message ကို reply လုပ်ပြီး `/ban`
• `/unban username` — Ban ထားသော member ကို ပြန်ခွင့်ပြုရန်
  ဥပမာ: `/unban @username`
• `/warn username` — Member ကို warning ပေးရန်
  ဥပမာ: `/warn @username`
• `/resetwarn username` — Member ၏ warnings များ reset လုပ်ရန်
  ဥပမာ: `/resetwarn @username`
• `/mute username` — Member ကို group chat တွင် စာမပို့နိုင်အောင် mute လုပ်ရန်
  ဥပမာ: `/mute @username`
• `/unmute username` — Member ကို ပြန်လည် စာပို့ခွင့်ပြုရန်
  ဥပမာ: `/unmute @username`
• `/all <message>` — သိမ်းထားသော member များကို message နှင့် mention လုပ်ရန်
  ဥပမာ: `/all good night guys`
• `/stop` — `/all` mention broadcast ကို ချက်ချင်းရပ်ရန်
  ဥပမာ: `/stop`

💡 Moderation commands များကို Group Admin များသာ အသုံးပြုနိုင်ပါသည်။
💡 `/all` သည် bot restart ပြီးနောက် bot သိရှိထားသော member များကိုသာ mention လုပ်နိုင်ပါသည်။

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
