
import os

from pathlib import Path

from playwright.sync_api import sync_playwright



LISTING_URL = os.getenv("LISTING_URL", "https://www.airbnb.jp/rooms/1435115775752551185")

OUT_DIR = Path("output")



def log(msg):

    print(msg, flush=True)



def main():

    OUT_DIR.mkdir(exist_ok=True)

    videos_dir = OUT_DIR / "videos"

    videos_dir.mkdir(exist_ok=True)



    with sync_playwright() as p:

        log("[0] launch browser (headful, video recording)")

        browser = p.chromium.launch(

            headless=False,  # ← GUIありモード（Xvfbの中で動く）

            args=[

                "--lang=ja-JP",

                "--disable-gpu",

                "--no-sandbox",

            ],

            slow_mo=500,  # 少しゆっくり動かすと動画で見やすい

        )



        context = browser.new_context(

            locale="ja-JP",

            viewport={"width": 1280, "height": 720},

            record_video_dir=str(videos_dir),  # ★ 動画を保存

        )



        page = context.new_page()



        log(f"[1] goto {LISTING_URL}")

        page.goto(LISTING_URL, wait_until="networkidle", timeout=60000)

        page.wait_for_timeout(5000)  # 5秒待ってレンダリングさせる



        # 1枚スクショも撮っておく

        png_path = OUT_DIR / "page.png"

        log(f"[2] take screenshot -> {png_path}")

        page.screenshot(path=str(png_path), full_page=True)



        log("[3] close context/browser (this finalizes video file)")

        context.close()

        browser.close()



        # record_video_dir に1つだけ動画ファイルができている想定でパスを表示

        videos = list(videos_dir.glob("**/*"))

        for v in videos:

            log(f"[VIDEO] {v}")



        log("[DONE] finished minimal capture with video.")



if __name__ == "__main__":

    main()

