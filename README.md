
---

## 🐳 Dockerで実行する

### ビルド
```bash
docker build -t airbnb-reviews .
```

### 実行（出力を ./output に保存）
```bash
mkdir -p output
docker run --rm -v "$PWD/output:/app" \
  -e LISTING_URL="https://www.airbnb.jp/rooms/1435115775752551185" \
  -e MAX_REVIEWS=1000 \
  airbnb-reviews
```
> ブラウザUIを出すには `-e HEADFUL=true` を付与（LinuxでX11/Wayland設定が必要）。

### docker-compose 版
```bash
docker compose up --build
```

---

## 🐙 GitHub登録手順

```bash
git init
git add .
git commit -m "Initial commit: Dockerized Airbnb Reviews Scraper"
git branch -M main
git remote add origin https://github.com/<your-account>/<your-repo>.git
git push -u origin main
```

- CI（GitHub Actions）: `.github/workflows/ci.yml` を同梱。
- ライセンス: `LICENSE`（MIT）。著作権表記にお名前/社名/年を追記してください。
