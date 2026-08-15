# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# System deps required to compile native Python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.10-slim

LABEL org.opencontainers.image.source="https://github.com/YOUR_USER/telegram-music-bot"
LABEL maintainer="@Mount_lvy"

WORKDIR /app

# ── FFmpeg (required by SoundCloud audio streaming and PyTgCalls) ─────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy bot source
COPY . .

# Create persistent downloads directory
RUN mkdir -p downloads

# Non-root user for security
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Health-check: just verify the Python interpreter is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-u", "main.py"]
