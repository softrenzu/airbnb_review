
import os

import time

import csv

from pathlib import Path

from playwright.sync_api import sync_playwright



LISTING_URL = os.getenv("LISTING_URL", "https://www.airbnb.jp/rooms/1435115775752551185")

MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "300"))

OUTPUT_DIR = Path("output")

VIDEO_DIR = OUTPUT_DIR / "videos"



OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_DIR.mkdir(parents=True, exist_ok=True)



def log(msg: str):

    print(msg, flush=True)



def shot(page, name: str):

    """各ステップでスクショを取る"""

    path = OUTPUT_DIR / f"{name}.png"

    page.screenshot(path=str(path), full_page=True)

    log(f"[SHOT] {path}")



def main():

    log("[0] launch browser with Xvfb + video recording")



    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        context = browser.new_context(

            viewport={"width": 1400, "height": 900},

            record_video_dir=str(VIDEO_DIR),

        )

        page = context.new_page()



        log(f"[1] goto {LISTING_URL}")

        page.goto(LISTING_URL, wait_until="networkidle", timeout=90_000)

        shot(page, "step1_loaded")



        # ===== レビューを開く強化版 =====

        log("[2] try open reviews modal")



        selectors = [

            '[data-testid="pdp-reviews-modal-trigger"]',

            'button:has-text("レビュー")',

            'a:has-text("レビュー")',

            'div:has-text("件のレビュー")',

        ]



        modal_opened = False

        for sel in selectors:

            log(f"[TRY] selector: {sel}")

            try:

                btn = page.locator(sel).first

                btn.wait_for(state="visible", timeout=8000)

                btn.click()

                time.sleep(2)

                shot(page, f"step2_click_{sel.replace('/', '_')}")

                modal_opened = True

                break

            except Exception as e:

                log(f"[NG] {sel}: {e}")



        if not modal_opened:

            log("[FATAL] Could NOT open reviews modal")

            shot(page, "step2_fail")

            context.close()

            browser.close()

            return



        log("[OK] modal opened")

        shot(page, "step2_modal_opened")



        # ===== モーダル内スクロール =====

        log("[3] scroll reviews")

        dialog = page.locator("div[role='dialog']").first



        for i in range(25):

            try:

                dialog.evaluate("el => el.scrollBy(0, 2000)")

            except Exception:

                page.keyboard.press("PageDown")

            time.sleep(0.8)

            shot(page, f"step3_scroll_{i}")



        # ===== 「すべて表示」をできるだけ全部クリック =====

        log("[4] expand all 'すべて表示'")

        for i in range(5):

            btns = page.get_by_text("すべて表示", exact=False)

            for j in range(btns.count()):

                try:

                    btns.nth(j).click(timeout=1000)

                    time.sleep(0.2)

                except Exception:

                    pass

            shot(page, f"step4_expand_{i}")



        # ===== レビュー抽出（シンプル版） =====

        log("[5] extract reviews")

        cards = page.locator("[data-testid='review-card']")

        count = cards.count()

        log(f"[INFO] found {count} review cards")



        reviews = []

        for i in range(count):

            if len(reviews) >= MAX_REVIEWS:

                break

            card = cards.nth(i)

            try:

                txt = card.inner_text().strip()

            except Exception:

                continue

            if not txt:

                continue

            lines = [l.strip() for l in txt.splitlines() if l.strip()]

            if not lines:

                continue

            name = lines[0]

            date = ""

            body = "\n".join(lines[1:])

            reviews.append({"name": name, "date": date, "text": body})



        # ===== CSV 保存 =====

        csv_path = OUTPUT_DIR / "reviews.csv"

        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:

            writer = csv.DictWriter(f, fieldnames=["name", "date", "text"])

            writer.writeheader()

            for r in reviews:

                writer.writerow(r)

        log(f"[DONE] CSV -> {csv_path}")



        log("[6] closing browser (finalize video)")

        context.close()

        browser.close()

        log("[DONE] finished with video")



if __name__ == "__main__":

    main()

