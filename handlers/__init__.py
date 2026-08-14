import logging

from handlers.callbacks import register_callbacks
from handlers.help import register_help
from handlers.music import register_music
from handlers.start import register_start
from helpers.player import play_next, set_refs
from helpers.queue import get_current

logger = logging.getLogger(__name__)


def register_all_handlers(bot_client, pytgcalls):
    """Register bot commands, inline callbacks, and PyTgCalls lifecycle hooks."""
    set_refs(bot_client, pytgcalls)
    # Register specific playback callbacks before music.py's generic menu callback.
    register_callbacks(bot_client)
    register_start(bot_client)
    register_help(bot_client)
    register_music(bot_client)

    # PyTgCalls 2.x emits StreamEnded updates when an audio/video source ends.
    # Advancing here makes the queue work without requiring /skip.
    try:
        from pytgcalls.types import StreamEnded

        @pytgcalls.on_update()
        async def _stream_update(update):
            if not isinstance(update, StreamEnded):
                return
            chat_id = update.chat_id
            if get_current(chat_id) is None:
                return
            try:
                await play_next(chat_id)
            except Exception:
                logger.exception("Automatic queue advance failed for chat %s", chat_id)

        logger.info("✅ PyTgCalls StreamEnded auto-next handler registered.")
    except Exception:
        logger.exception("❌ Could not register PyTgCalls StreamEnded handler.")

    logger.info("✅ Music commands and inline callbacks registered.")
