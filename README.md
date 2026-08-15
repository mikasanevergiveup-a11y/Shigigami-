# 🎵 Telegram Music Bot

A fully featured Telegram Voice Chat Music Bot built with:
- **Pyrogram** — Telegram MTProto client
- **PyTgCalls** — Voice call streaming
- **yt-dlp** — SoundCloud audio extraction
- **FFmpeg** — Audio/video processing

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎵 Audio streaming | Play SoundCloud music in group voice chats |
| 🎧 SoundCloud fallback | Search multiple SoundCloud results and skip DRM/unplayable tracks |
| 📋 Smart queue | Per-group song queue with auto-advance |
| 🔂 Loop mode | Loop the current track |
| 🔊 Volume control | Adjust volume 1–200% |
| ⏯ Inline controls | Pause / Resume / Skip / Stop from inline buttons |
| 🛡 Force-join | Require users to join a channel before using the bot |
| 👮 Admin commands | Admins + authorized users control playback |
| 🎧 Song download | Download audio files directly to chat |

---

## 🗂 Project Structure

```
telegram-music-bot/
├── main.py              # Entry point
├── config.py            # Config from env vars
├── handlers/
│   ├── __init__.py      # Handler registration
│   ├── start.py         # /start — welcome message
│   ├── help.py          # /help — command list
│   ├── music.py         # /play /queue /ping
│   ├── admin.py         # /pause /resume /skip /end /stop /volume /auth /unauth
│   └── callbacks.py     # Inline button callbacks
├── helpers/
│   ├── __init__.py
│   ├── queue.py         # Per-chat queue management
│   ├── downloader.py    # SoundCloud audio downloader
│   ├── player.py        # PyTgCalls helpers & now-playing UI
│   └── decorators.py    # @force_join and @admin_only decorators
├── assets/
│   └── banner.jpg       # (optional) Welcome banner image
├── downloads/           # Auto-created; holds temporary audio files
├── requirements.txt
├── Dockerfile
├── render.yaml          # Render Blueprint
└── deploy.py            # Autonomous GitHub + Render deployment script
```

---

## 🚀 Quick Deploy

### Option A — Autonomous deploy script

```bash
export GITHUB_PAT="your_github_pat"
export RENDER_API_KEY="your_render_api_key"
export API_ID="your_api_id"
export API_HASH="your_api_hash"
export BOT_TOKEN="your_bot_token"
export STRING_SESSION="your_pyrogram_session_string"

pip install requests
python deploy.py
```

The script will:
1. Create a private GitHub repo and push all source files
2. Create a Render Background Worker linked to the repo
3. Inject all env vars into Render
4. Poll until the service is LIVE

### Option B — Manual Docker

```bash
docker build -t music-bot .
docker run -d \
  -e API_ID=... \
  -e API_HASH=... \
  -e BOT_TOKEN=... \
  -e STRING_SESSION=... \
  music-bot
```

---

## ⚙️ Environment Variables

| Variable | Description |
|----------|-------------|
| `API_ID` | Telegram app ID (from my.telegram.org) |
| `API_HASH` | Telegram app hash |
| `BOT_TOKEN` | Bot token from @BotFather |
| `STRING_SESSION` | Pyrogram `StringSession` for the user account |

> **Security:** Never commit `.env` files or session strings to a public repo.

---

## 🤖 Commands

### Member Commands
| Command | Description |
|---------|-------------|
| `/play <song>` | Search SoundCloud and play audio in group VC |
| `/queue` | View upcoming songs |
| `/song <name>` | Download SoundCloud audio file |
| `/ping` | Check bot response speed |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/pause` | Pause current stream |
| `/resume` | Resume playback |
| `/skip` | Skip to next song |
| `/end` or `/stop` | Stop VC streaming |
| `/volume <1-200>` | Adjust volume |
| `/auth` | Authorize a user (reply to their message) |
| `/unauth` | Remove a user's authorization |

---

## 🔒 Security Notes

- All credentials are loaded from **environment variables** — never from source code.
- The `STRING_SESSION` provides full Telegram account access. Keep it private.
- Regularly rotate your session string if you suspect exposure.
- The Docker image runs as a **non-root user** (`botuser`).

---

## ⚡️ Powered by [@Mount_lvy](https://t.me/Mount_lvy)
