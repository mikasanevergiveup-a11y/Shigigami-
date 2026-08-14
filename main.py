import asyncio
import logging
from pyrogram import Client
from pytgcalls import PyTgCalls

import config
from handlers import register_all_handlers
from keep_alive import keep_alive  # 👈 1. Keep Alive ကို ဒီနေရာမှာ Import လုပ်ထားပါသည်

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    # ── 1. User client (Assistant Account) ────────────────────────────────────
    user_client = Client(
        name="music_user",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=config.STRING_SESSION,
        in_memory=True,
    )

    # ── 2. Bot client (Main Bot Account) ──────────────────────────────────────
    bot_client = Client(
        name="music_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        in_memory=True,
    )

    # ── 3. PyTgCalls Engine ကို User Client နှင့် ချိတ်ဆက်ခြင်း ─────────────────────
    pytgcalls = PyTgCalls(user_client)

    # Handlers များ နှင့် PyTgCalls reference ကို player.py သို့ ပို့ပေးခြင်း
    register_all_handlers(bot_client, pytgcalls)

    # ── 4. User Client ကို Start လုပ်ခြင်း ───────────────────────────────────────
    logger.info("Starting user client...")
    await user_client.start()

    # ── 5. Group ID / Peer ID Error မတက်စေရန် Dialog များ Auto-Cache လုပ်ခြင်း ──────
    logger.info("Caching all dialogs for Assistant Account...")
    try:
        async for dialog in user_client.get_dialogs():
            pass
        logger.info("Successfully pre-cached all dialogs!")
    except Exception as e:
        logger.warning(f"Could not pre-cache dialogs: {e}")

    # ── 6. Voice Chat Engine (PyTgCalls) ကို စတင်ခြင်း ──────────────────────────
    logger.info("Starting PyTgCalls Voice Engine...")
    await pytgcalls.start()

    # ── 7. Bot Client ကို Start လုပ်ခြင်း ────────────────────────────────────────
    logger.info("Starting bot client...")
    await bot_client.start()

    logger.info("✅ Music Bot & Voice Engine are live!")

    # Keep running
    await asyncio.Event().wait()


if __name__ == "__main__":
    keep_alive()  # 👈 2. Bot မစမီ Flask Web Server ကို နောက်ကွယ်မှ စတင်ပေးပါမည်
    asyncio.run(main())
    