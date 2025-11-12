# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System packages (minimal); Playwright will add its own deps via --with-deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dep file first for better layer caching
COPY requirements.txt ./

# Install Python deps and Playwright browser+deps
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install --with-deps chromium

# Copy the rest
COPY . .

# Default config via environment variables (can be overridden at runtime)
ENV LISTING_URL="https://www.airbnb.jp/rooms/1435115775752551185" \
    MAX_REVIEWS=2000 \
    CLICK_TRANSLATE=true \
    HEADFUL=false \
    SLOWMO_MS=0

# When running in Docker, config.json is optional; env vars override inside the script.
# To watch the browser, run with: -e HEADFUL=true

CMD ["python", "scrape_airbnb_reviews.py"]
