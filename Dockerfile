
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends xvfb xauth x11-utils fonts-ipafont-gothic wget ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install chromium

COPY scrape_airbnb_reviews.py .

ENV LISTING_URL="https://www.airbnb.jp/rooms/1435115775752551185" MAX_REVIEWS=200

CMD xvfb-run -a -s "-screen 0 1600x1200x24" python scrape_airbnb_reviews.py

