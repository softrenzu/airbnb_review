
import os

import time



from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError



LISTING_URL = os.getenv("LISTING_URL", "https://www.airbnb.jp/rooms/1435115775752551185")

MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "50"))





def safe_click(page, selector: str, timeout: int = 3000) -> bool:

    """存在すればクリックして True、なければ False を返す簡易クリック"""

    try:

        page.locator(selector).first.click(timeout=timeout)

        print(f"[CLICK] {selector}")

        return True

    except Exception:

        print(f"[MISS] {selector} (TimeoutError)")

        return False





def close_popups(page):

    """翻訳ポップアップなどを閉じる"""

    print("[STEP] close_popups")

    selectors = [

        "button[aria-label='閉じる']",

        "button[aria-label='Close']",

        "button:has-text('×')",

        "button:has-text('閉じる')",

    ]

    for sel in selectors:

        if safe_click(page, sel, timeout=2000):

            # 1 回閉じられれば十分

            time.sleep(1)

            return





def scroll_page_to_reviews(page):

    """ページ全体を下に何回かスクロールしてレビューが見える位置まで動かす"""

    print("[STEP] scroll_page_to_reviews")

    for _ in range(10):

        page.mouse.wheel(0, 800)

        time.sleep(0.8)





def parse_review_block_text(raw: str):

    """

    レビューカード全体のテキストから、

    ざっくり [名前, 日付行, 本文] を推定する。

    （まず動けば OK なので多少雑でもよし）

    """

    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    if not lines:

        return "", "", ""



    name = lines[0]



    # 「◯日前」「◯週間前」「◯か月前」「2025年◯月」などが入っていそうな行を探す

    date = ""

    for line in lines[1:5]:

        if any(k in line for k in ["日前", "週間前", "か月前", "年", "月"]):

            date = line

            break



    if date and date in lines:

        start_idx = lines.index(date) + 1

    else:

        start_idx = 1



    body_lines = lines[start_idx:]

    # カード末尾の「すべて表示」は要らないので削除

    body_lines = [l for l in body_lines if l != "すべて表示"]

    body = " ".join(body_lines).strip()



    return name, date, body





def collect_visible_reviews(page):

    """

    モーダルは開かず、「今画面に見えているレビュー」をそのまま抜き出す。

    クリックは一切せず、各カード内のテキストをまとめて CSV に出す。

    """

    print("[STEP] collect_visible_reviews")



    # 「レビュー」という単語を含むセクションを探す（日本語 UI 想定）

    reviews_section = page.locator(

        "section:has-text('件のレビュー'), section:has-text('レビュー')"

    ).first



    if not reviews_section or reviews_section.count() == 0:

        print("[WARN] reviews section not found")

        return []



    # 各レビューカードはたいてい「すべて表示」リンクを含むので、それを目印にする

    more_buttons = reviews_section.locator("text=すべて表示")

    count = more_buttons.count()

    print(f"[INFO] found {count} candidate review blocks (by 'すべて表示')")



    reviews = []



    for i in range(min(count, MAX_REVIEWS)):

        btn = more_buttons.nth(i)

        # 「すべて表示」ボタンの一番近い上位要素（section/article/li/div）をレビューカードとみなす

        card = btn.locator(

            "xpath=ancestor::*[self::section or self::article or self::li or self::div][1]"

        )

        try:

            raw_text = card.inner_text()

        except Exception as e:

            print(f"[WARN] failed to read review block #{i}: {e}")

            continue



        name, date, body = parse_review_block_text(raw_text)

        if not body:

            # 本文が取れていないものはスキップ

            print(f"[WARN] empty body for review #{i}, skip")

            continue



        reviews.append(

            {

                "name": name,

                "date": date,

                "text": body,

            }

        )



    print(f"[INFO] collected {len(reviews)} visible reviews")

    return reviews





def scrape():

    print(f"[START] LISTING_URL={LISTING_URL}")



    with sync_playwright() as pw:

        browser = pw.chromium.launch(headless=False)

        context = browser.new_context()

        page = context.new_page()



        print(f"[STEP] goto: {LISTING_URL}")

        try:

            # networkidle だといつまでも待ってタイムアウトしやすいので load に変更

            page.goto(LISTING_URL, wait_until="load", timeout=120_000)

        except PlaywrightTimeoutError:

            print("[WARN] goto timeout, continue anyway")



        time.sleep(5)



        close_popups(page)

        scroll_page_to_reviews(page)



        # レビューセクションが画面にある状態でスクショ

        os.makedirs("output", exist_ok=True)

        page.screenshot(path="output/page.png", full_page=True)



        reviews = collect_visible_reviews(page)



        # CSV / MD 保存

        csv_lines = ["name,date,text"]

        md_lines = []

        for r in reviews:

            # カンマは簡易的にスペースに置き換え

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

