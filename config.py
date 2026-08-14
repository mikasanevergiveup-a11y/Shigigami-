import os

# ── Telegram API credentials ──────────────────────────────────────────────────
API_ID          = int(os.environ.get("API_ID", 0))
API_HASH        = os.environ.get("API_HASH", "")
BOT_TOKEN       = os.environ.get("BOT_TOKEN", "")
STRING_SESSION  = os.environ.get("STRING_SESSION", "")

# ── Force-join channel ────────────────────────────────────────────────────────
FORCE_JOIN_CHANNEL  = "musicbotmegaliana"          # username without @
FORCE_JOIN_LINK     = "https://t.me/musicbotmegaliana"

# ── Bot branding / links ──────────────────────────────────────────────────────
CHANNEL_LINK    = "https://t.me/musicbotmegaliana"
UPDATES_LINK    = "https://t.me/musicbotmegaliana"
OWNER_LINK      = "https://t.me/Mount_lvy"
SUPPORT_LINK    = "https://t.me/musicbotmegaliana1"
POWERED_BY      = "@Mount_lvy"

# ── Paths ─────────────────────────────────────────────────────────────────────
DOWNLOADS_DIR   = os.path.join(os.path.dirname(__file__), "downloads")
BANNER_PATH     = os.path.join(os.path.dirname(__file__), "assets", "banner.jpg")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
