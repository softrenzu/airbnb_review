
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends xvfb xauth x11-utils libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxdamage1 libxfixes3 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 libdrm2 libxcomposite1 libxrandr2 libxshmfence1 libgbm1 libwayland-server0 libwayland-client0 libx11-xcb1 libxcb-dri3-0 libxcb1 fonts-ipafont-gothic wget ca-certificates curl unzip && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install chromium

COPY scrape_airbnb_reviews.py .

ENV LISTING_URL="https://www.airbnb.jp/rooms/1435115775752551185" MAX_REVIEWS=200

CMD xvfb-run -a -s "-screen 0 1600x1200x24" python scrape_airbnb_reviews.py

