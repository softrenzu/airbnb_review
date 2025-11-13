
import os

import time

from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError



LISTING_URL = os.getenv("LISTING_URL", "https://www.airbnb.jp/rooms/1435115775752551185")

OUTPUT_DIR = Path("output")



def close_popups(page):

    # 翻訳ポップアップなどをなるべく閉じる（失敗しても無視）

    selectors = [

        "button[aria-label='閉じる']",

        "button[aria-label='Close']",

        "button:has-text('×')",

    ]

    for sel in selectors:

        try:

            page.locator(sel).first.click(timeout=2000)

            print(f"[CLICK] popup close: {sel}")

            time.sleep(1)

            return

        except PlaywrightTimeoutError:

            print(f"[MISS] popup close: {sel}")



def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)



    print(f"[START] LISTING_URL={LISTING_URL}")



    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(viewport={"width": 1280, "height": 720})

        page = context.new_page()



        print("[STEP] goto:", LISTING_URL)

        page.goto(LISTING_URL, wait_until="networkidle", timeout=120000)



        # ちょっと待ってからポップアップ閉じる

        time.sleep(5)

        print("[STEP] close_popups")

        close_popups(page)



        # レビューが見えるあたりまで軽くスクロール（失敗しても気にしない）

        try:

            print("[STEP] scroll a bit")

            page.mouse.wheel(0, 800)

            time.sleep(3)

            page.mouse.wheel(0, 800)

            time.sleep(3)

        except Exception as e:

            print("[WARN] scroll failed:", e)



        # フルページでスクリーンショット

        png_path = OUTPUT_DIR / "page.png"

        print("[STEP] screenshot ->", png_path)

        page.screenshot(path=str(png_path), full_page=True)



        # ページのテキストも保存（後で解析する用）

        txt_path = OUTPUT_DIR / "page.txt"

        print("[STEP] save body text ->", txt_path)

        try:

            body_text = page.inner_text("body")

        except Exception:

            body_text = page.content()

        txt_path.write_text(body_text, encoding="utf-8")



        print("[END] done")



        context.close()

        browser.close()



if __name__ == "__main__":

    main()

