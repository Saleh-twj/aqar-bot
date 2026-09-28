import json, asyncio, re, os
from playwright.async_api import async_playwright

BASE = "https://aqaralmuhaysini.com"
START = f"{BASE}/nearproperties?latitude=24&longitude=46"
NEXT_BTN = "text=/^(التالي|Next|›|»|>)$/"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(START, wait_until="networkidle")

        links, page_no = set(), 1
        while True:
            await page.mouse.wheel(0, 50000)
            await page.wait_for_timeout(1500)
            found = await page.eval_on_selector_all(
                "a[href*='propertydetails']", "els => els.map(e => e.href)")
            before = len(links)
            links.update(found)
            print(f"صفحة {page_no}: {len(links)} إعلان")

            nxt = page.locator(NEXT_BTN).last
            if await nxt.count() and await nxt.is_visible() and await nxt.is_enabled():
                await nxt.click()
                await page.wait_for_load_state("networkidle")
                page_no += 1
            elif len(links) == before:
                break

        results = []
        for i, url in enumerate(sorted(links), 1):
            await page.goto(url, wait_until="networkidle")
            text = await page.inner_text("body")
            results.append({
                "id": re.search(r"propertydetails/(\d+)", url).group(1),
                "url": url,
                "title": await page.title(),
                "text": re.sub(r"\s+", " ", text).strip(),
            })
            print(f"[{i}/{len(links)}] {url}")

        await browser.close()

        texts = [r["text"] for r in results]
    pre = len(os.path.commonprefix(texts))
    suf = len(os.path.commonprefix([t[::-1] for t in texts]))
    for r in results:
        r["text"] = r["text"][pre:len(r["text"]) - suf][:600]
    json.dump(results, open("properties.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"تم: {len(results)} عقار")

asyncio.run(main())
