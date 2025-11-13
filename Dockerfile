
FROM python:3.12-slim



WORKDIR /app



# 基本ツールと Xvfb

RUN apt-get update && apt-get install -y --no-install-recommends \

    xvfb wget unzip libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \

    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \

    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \

    && rm -rf /var/lib/apt/lists/*



COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



# ▼ Playwright のブラウザをインストール（重要!!）

RUN python -m playwright install chromium



COPY scrape_airbnb_reviews.py .



CMD bash -lc "Xvfb :99 -screen 0 1280x720x16 & sleep 2 && export DISPLAY=:99 && python /app/scrape_airbnb_reviews.py"

