
import os

import time

from playwright.sync_api import sync_playwright



LISTING_URL = os.getenv("LISTING_URL", "https://www.airbnb.jp/rooms/1435115775752551185")

MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "50"))



def log(msg):

    print(msg, flush=True)



def safe_click(page, selector, desc="", timeout=5000):

    try:

        page.locator(selector).first.click(timeout=timeout)

        log(f"[CLICK] {desc or selector}")

        return True

    except Exception as e:

        log(f"[MISS] {desc or selector} ({e.__class__.__name__})")

        return False



def close_popups(page):

    log("[STEP] close_popups")

    selectors = [

        "button[aria-label='閉じる']",

        "button[aria-label='Close']",

        "button:has-text('×')",

        "button:has-text('閉じる')",

    ]

    for sel in selectors:

        if safe_click(page, sel, desc="popup close", timeout=1500):

            time.sleep(1)



def scroll_page_to_reviews(page):

    log("[STEP] scroll_page_to_reviews")

    for i in range(20):

        page.mouse.wheel(0, 800)

        time.sleep(0.5)



def open_reviews_section(page):

    log("[STEP] open_reviews_section")

    candidates = [

        "text=件のレビュー",

        "text=レビュー",

        "button:has-text('レビュー')",

        "[data-testid='reviews']",

    ]

    for sel in candidates:

        loc = page.locator(sel).first

        try:

            if loc.is_visible():

                loc.click()

                log(f"[OK] clicked reviews selector: {sel}")

                return True

        except Exception:

            pass

    log("[WARN] reviews button not found / not clickable")

    return False



def collect_reviews(page):

    log("[STEP] collect_reviews")

    os.makedirs("output", exist_ok=True)

    selectors = [

        "div[data-testid='review-card']",

        "section:has-text('レビュー') div[data-testid='review']",

    ]

    reviews = None

    for sel in selectors:

        loc = page.locator(sel)

        count = loc.count()

        log(f"[INFO] selector {sel} -> {count} nodes")

        if count > 0:

            reviews = loc

            break

    rows = ["name,date,text"]

    md_blocks = []

    if reviews is None:

        log("[WARN] no reviews found")

    else:

        count = min(reviews.count(), MAX_REVIEWS)

        log(f"[INFO] extracting {count} reviews")

        for i in range(count):

            r = reviews.nth(i)

            try:

                name = r.locator("h3").first.inner_text() if r.locator("h3").count() else ""

                date = r.locator("time").first.inner_text() if r.locator("time").count() else ""

                text = r.inner_text().replace("\n", " ").strip()

                rows.append(f"{name},{date},{text}")

                md_blocks.append(f"### {name}\n- {date}\n{text}\n")

            except Exception as e:

                log(f"[ERR] review {i}: {e}")

    with open("output/reviews.csv", "w") as f:

        f.write("\n".join(rows))

    with open("output/reviews.md", "w") as f:

        f.write("\n".join(md_blocks))

    page.screenshot(path="output/page.png", full_page=True)

    log(f"[DONE] wrote {len(rows)-1} reviews to output/reviews.csv")



def scrape():

    log(f"[START] LISTING_URL={LISTING_URL}")

    with sync_playwright() as pw:

        browser = pw.chromium.launch(

            headless=False,

            args=[

                "--disable-dev-shm-usage",

                "--no-sandbox",

            ],

        )

        context = browser.new_context(record_video_dir="output/videos")

        page = context.new_page()

        log(f"[STEP] goto: {LISTING_URL}")

        page.goto(LISTING_URL, timeout=180000)  # networkidle はやめる

        page.wait_for_timeout(5000)

        close_popups(page)

        scroll_page_to_reviews(page)

        opened = open_reviews_section(page)

        if opened:

            page.wait_for_timeout(5000)

        collect_reviews(page)

        context.close()

        browser.close()

        log("[END] done")



if __name__ == "__main__":

    scrape()

