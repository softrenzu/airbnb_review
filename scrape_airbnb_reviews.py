
#!/usr/bin/env python3

import os

import time

import csv

from pathlib import Path

from playwright.sync_api import sync_playwright



LISTING_URL = os.getenv(

    "LISTING_URL",

    "https://www.airbnb.jp/rooms/1435115775752551185",

)

MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "300"))



OUTPUT_DIR = Path("output")

VIDEO_DIR = OUTPUT_DIR / "videos"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_DIR.mkdir(parents=True, exist_ok=True)





def log(msg: str) -> None:

    print(msg, flush=True)





def shot(page, name: str) -> None:

    path = OUTPUT_DIR / f"{name}.png"

    try:

        page.screenshot(path=str(path), full_page=True)

        log(f"[SHOT] {path}")

    except Exception as e:

        log(f"[SHOT-ERR] {name}: {e}")





def close_translation_popup(page) -> None:

    """最初に出る『翻訳しますか？』ポップアップを閉じる"""

    log("[1.1] try close translation popup if exists")

    try:

        # 「翻訳」の文字を含むダイアログを優先して探す

        dialog = page.locator("div[role='dialog']").filter(has_text="翻訳")

        if dialog.count() == 0:

            # なければ一番上の dialog を見る（初回ロード直後なら翻訳ポップアップのはず）

            dialog = page.locator("div[role='dialog']").first



        if dialog.count() == 0:

            log("[1.1] no dialog found (maybe no popup)")

            return



        # ダイアログ内のボタン（左上の X を含む）をクリックして閉じる

        btn = dialog.locator("button").first

        btn.click()

        time.sleep(1)

        shot(page, "step1_popup_closed")

        log("[1.1] translation popup closed")

    except Exception as e:

        log(f"[WARN] could not close translation popup: {e}")





def main() -> None:

    log("[0] launch browser with Xvfb + video recording")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        context = browser.new_context(

            viewport={"width": 1400, "height": 900},

            record_video_dir=str(VIDEO_DIR),

        )

        page = context.new_page()



        # 1) ページを開く

        log(f"[1] goto {LISTING_URL}")

        page.goto(LISTING_URL, wait_until="networkidle", timeout=90_000)

        time.sleep(3)

        shot(page, "step1_loaded")



        # 1.1) 翻訳ポップアップがあれば閉じる

        close_translation_popup(page)



        # 1.5) レビューが見える位置までスクロール

        log("[1.5] scroll down to reviews area before clicking")

        for i in range(8):

            page.mouse.wheel(0, 1200)

            time.sleep(0.6)

        shot(page, "step1_scrolled")



        # 2) レビューモーダルを開く

        log("[2] try open reviews modal")

        selectors = [

            "[data-testid='pdp-reviews-modal-trigger']",

            "button:has-text('すべてのレビューを表示')",

            "a:has-text('すべてのレビューを表示')",

            "button:has-text('レビュー')",

            "a:has-text('レビュー')",

        ]



        modal_opened = False

        for idx, sel in enumerate(selectors):

            log(f"[TRY] selector: {sel}")

            try:

                btn = page.locator(sel).first

                btn.scroll_into_view_if_needed(timeout=5_000)

                btn.wait_for(state="visible", timeout=5_000)

                btn.click()

                time.sleep(2)

                shot(page, f"step2_clicked_{idx}")

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



        # 3) モーダル内をスクロールしてレビュー読み込み

        log("[3] scroll reviews inside modal")

        dialog = page.locator("div[role='dialog']").first

        for i in range(25):

            try:

                dialog.evaluate("el => el.scrollBy(0, 2000)")

            except Exception:

                page.keyboard.press("PageDown")

            time.sleep(0.8)

            if i in (0, 10, 20):

                shot(page, f"step3_scroll_{i}")



        # 4) 「すべて表示」をできるだけクリック

        log("[4] expand all 'すべて表示'")

        for _ in range(5):

            btns = page.get_by_text("すべて表示", exact=False)

            count = btns.count()

            for j in range(count):

                try:

                    btns.nth(j).click(timeout=1000)

                    time.sleep(0.2)

                except Exception:

                    pass



        # 5) レビュー抽出

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



        # CSV 保存

        csv_path = OUTPUT_DIR / "reviews.csv"

        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:

            writer = csv.DictWriter(f, fieldnames=["name", "date", "text"])

            writer.writeheader()

            for r in reviews:

                writer.writerow(r)

        log(f"[DONE] CSV -> {csv_path}")



        # MD 保存

        md_path = OUTPUT_DIR / "reviews.md"

        with md_path.open("w", encoding="utf-8") as f:

            for r in reviews:

                f.write(f"## {r['name']} ({r['date']})\n\n{r['text']}\n\n---\n\n")

        log(f"[DONE] MD  -> {md_path}")



        log("[6] closing browser (finalize video)")

        context.close()

        browser.close()

        log("[DONE] finished with video")

