
import os

import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError



LISTING_URL = os.getenv("LISTING_URL", "https://www.airbnb.jp/rooms/1435115775752551185")

MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "50"))





def safe_click(page, selector: str, timeout: int = 3000) -> bool:

    try:

        page.locator(selector).first.click(timeout=timeout)

        print(f"[CLICK] {selector}")

        return True

    except Exception:

        print(f"[MISS] {selector} (TimeoutError)")

        return False





def close_popups(page):

    print("[STEP] close_popups")

    selectors = [

        "button[aria-label='閉じる']",

        "button[aria-label='Close']",

        "button:has-text('×')",

        "button:has-text('閉じる')",

    ]

    for sel in selectors:

        if safe_click(page, sel, timeout=2000):

            time.sleep(1)

            return





def scroll_page_to_reviews(page):

    print("[STEP] scroll_page_to_reviews")

    # 下までかなりしっかりスクロールしておく

    for _ in range(15):

        page.mouse.wheel(0, 1000)

        time.sleep(0.6)





def parse_review_block_text(raw: str):

    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    if not lines:

        return "", "", ""

    name = lines[0]



    date = ""

    for line in lines[1:6]:

        if any(k in line for k in ["日前", "週間前", "か月前", "月", "年"]):

            date = line

            break



    if date and date in lines:

        start_idx = lines.index(date) + 1

    else:

        start_idx = 1



    body_lines = lines[start_idx:]

    body_lines = [l for l in body_lines if l != "すべて表示"]

    body = " ".join(body_lines).strip()

    return name, date, body





def collect_visible_reviews(page):

    print("[STEP] collect_visible_reviews")



    # ページ全体から「すべて表示」を探し、その一番近い親要素をレビューカードとみなす

    buttons = page.locator("text=すべて表示")

    total = buttons.count()

    print(f"[INFO] found {total} 'すべて表示' elements")



    reviews = []

    for i in range(total):

        btn = buttons.nth(i)

        card = btn.locator(

            "xpath=ancestor::*[self::section or self::article or self::li or self::div][1]"

        )



        # レビューには必ず <time> が含まれている想定。なければスキップ（写真の「すべて表示」などを除外）

        try:

            if card.locator("time").count() == 0:

                continue

            raw_text = card.inner_text()

        except Exception as e:

            print(f"[WARN] failed to read review block #{i}: {e}")

            continue



        name, date, body = parse_review_block_text(raw_text)

        if not body:

            print(f"[WARN] empty body for review #{i}, skip")

            continue



        reviews.append({"name": name, "date": date, "text": body})



        if len(reviews) >= MAX_REVIEWS:

            break



    print(f"[INFO] collected {len(reviews)} visible reviews")

    return reviews





def scrape():

    print(f"[START] LISTING_URL={LISTING_URL}")



    os.makedirs("output", exist_ok=True)



    with sync_playwright() as pw:

        # PDF 出力のため headless=True。動画は output/videos に保存。

        browser = pw.chromium.launch(headless=True)

        context = browser.new_context(record_video_dir="output/videos")

        page = context.new_page()



        print(f"[STEP] goto: {LISTING_URL}")

        try:

            page.goto(LISTING_URL, wait_until="load", timeout=120_000)

        except PlaywrightTimeoutError:

            print("[WARN] goto timeout, continue anyway")



        time.sleep(5)



        close_popups(page)

        scroll_page_to_reviews(page)



        # スクリーンショットと PDF を保存

        page.screenshot(path="output/page.png", full_page=True)

        try:

            page.pdf(path="output/page.pdf", format="A4", print_background=True)

            print("[INFO] saved output/page.pdf")

        except Exception as e:

            print(f"[WARN] page.pdf failed: {e}")



        reviews = collect_visible_reviews(page)



        csv_lines = ["name,date,text"]

        md_lines = []

        for r in reviews:

            safe_name = r["name"].replace(",", " ")

            safe_date = r["date"].replace(",", " ")

            safe_text = r["text"].replace("\n", " ").replace(",", " ")

            csv_lines.append(f"{safe_name},{safe_date},{safe_text}")

            md_lines.append(f"### {r['name']}\n- {r['date']}\n{r['text']}\n")



        with open("output/reviews.csv", "w", encoding="utf-8") as f:

            f.write("\n".join(csv_lines))

        with open("output/reviews.md", "w", encoding="utf-8") as f:

            f.write("\n".join(md_lines))



        print(f"[DONE] wrote {len(reviews)} reviews to output/reviews.csv")



        context.close()

        browser.close()





if __name__ == "__main__":

    scrape()

