
import os,time

from playwright.sync_api import sync_playwright

LISTING_URL=os.getenv("LISTING_URL");MAX_REVIEWS=int(os.getenv("MAX_REVIEWS","50"))

def safe_click(p,s,t=3000):

    try:p.locator(s).first.click(timeout=t);return True

    except:return False

def close_popup(p):

    for s in ["button[aria-label='閉じる']","button[aria-label='Close']","button:has-text('×')"]:

        if safe_click(p,s,1000):print("[INFO] Close popup:",s);return

def scroll_reviews(p):

    for _ in range(4):p.keyboard.press("PageDown");time.sleep(1)

def find_btn(p):

    for c in ["text=レビュー","text=件のレビュー","button:has-text('レビュー')","[data-testid='reviews']"]:

        if p.locator(c).first.is_visible():return c

    return None

def scrape():

    with sync_playwright() as pw:

        b=pw.chromium.launch(headless=False)

        c=b.new_context(record_video_dir="output/videos")

        p=c.new_page()

        print("[1] goto",LISTING_URL)

        p.goto(LISTING_URL,wait_until="networkidle",timeout=120000);time.sleep(3)

        print("[2] popup");close_popup(p);time.sleep(2)

        print("[3] scroll");scroll_reviews(p)

        print("[4] detect btn");btn=find_btn(p)

        if btn:print("[INFO] click",btn);p.locator(btn).click()

        else:print("[WARN] no reviews button")

        time.sleep(3)

        print("[5] extract")

        rev=p.locator("section:has-text('レビュー') div[data-testid='review']")

        n=rev.count()

        csv=["name,date,text"];md=[]

        for i in range(min(n,MAX_REVIEWS)):

            r=rev.nth(i)

            name=r.locator("h3").inner_text() if r.locator("h3").count() else ""

            date=r.locator("time").inner_text() if r.locator("time").count() else ""

            text=r.inner_text().replace("\n"," ").strip()

            csv.append(f"{name},{date},{text}");md.append(f"### {name}\n- {date}\n{text}\n")

        os.makedirs("output",exist_ok=True)

        open("output/reviews.csv","w").write("\n".join(csv))

        open("output/reviews.md","w").write("\n".join(md))

        p.screenshot(path="output/page.png")

        c.close();b.close();print("[DONE]",n)

if __name__=="__main__":scrape()

