import logging
from helpers.player import set_refs
from handlers.music import register_music

logger = logging.getLogger(__name__)


def register_all_handlers(bot_client, pytgcalls):
    """
    Main Bot Client ထဲသို့ Handlers အားလုံးကို Register ပြုလုပ်ပေးပြီး
    PyTgCalls reference ကို helpers/player.py သို့ ပို့ဆောင်ပေးသည်။
    """
    # ၁။ PyTgCalls instance ကို helpers/player.py ထဲသို့ ချိတ်ဆက်ပေးခြင်း
    try:
        set_refs(bot_client, pytgcalls)
        logger.info("✅ PyTgCalls reference attached to player helper.")
    except Exception as e:
        logger.error(f"❌ Failed to attach PyTgCalls reference: {e}")

    # ၂။ Music Handlers များကို Bot Client ထဲသို့ Register ပြုလုပ်ခြင်း
    try:
        register_music(bot_client)
        logger.info("✅ Music handlers successfully registered.")
    except Exception as e:
        logger.error(f"❌ Failed to register music handlers: {e}")
        