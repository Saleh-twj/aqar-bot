import json, asyncio, re, os
from playwright.async_api import async_playwright

STARTS = [f"https://aqaralmuhaysini.com/propertielist?regionId={i}" for i in range(1, 21)]
SEL = "a[href*='propertydetails']"
NEXT_BTN = "text=/التالي/"
LINKS_JS = "sel => [...document.querySelectorAll(sel)].map(e => e.href).join(',')"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        links = set()
        for start in STARTS:
            await page.goto(start, wait_until="networkidle")
            await page.wait_for_timeout(1500)
            page_no = 1
            while True:
                found = await page.eval_on_selector_all(SEL, "els => els.map(e => e.href)")
                before = len(links)
                links.update(found)
                print(f"{start} | صفحة {page_no}: {len(links)} إعلان")

                if page_no > 1 and len(links) == before:
                    break
                nxt = page.locator(NEXT_BTN).last
                if not (await nxt.count() and await nxt.is_visible() and await nxt.is_enabled()):
                    break

                prev = await page.evaluate(LINKS_JS, SEL)
                await nxt.click()
                try:  # ينتظر لين تتغير العقارات فعلاً
                    await page.wait_for_function(
                        f"prev => ({LINKS_JS})(\"{SEL}\") !== prev", arg=prev, timeout=10000)
                except Exception:
                    break
                await page.wait_for_timeout(500)
                page_no += 1

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
