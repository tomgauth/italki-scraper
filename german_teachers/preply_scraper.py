"""Scrape German tutors from Preply with Playwright.

Target listing (same filters Tom used): German tutors, native speakers,
English-speaking, tags adaptable + goal focused:
https://preply.com/en/online/german-tutors?tl=en&tags=ge_gco&additional=native&metadataTags=adaptable%2Cgoal_focused

Preply sits behind Cloudflare, so this uses a real browser. It walks the
listing pages, then opens each tutor profile to grab the full bio.

Usage:
    pip install playwright && playwright install chromium
    python -m german_teachers.preply_scraper --out data/preply_raw.json
"""

import argparse
import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

LISTING_URL = ("https://preply.com/en/online/german-tutors"
               "?tl=en&tags=ge_gco&additional=native&metadataTags=adaptable%2Cgoal_focused")


def extract_cards(page) -> list:
    """Tutor cards carry JSON-LD and data attributes; fall back to DOM."""
    tutors = []
    for script in page.locator("script[type='application/ld+json']").all():
        try:
            data = json.loads(script.inner_text())
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            graph = item.get("@graph", [item]) if isinstance(item, dict) else []
            for node in graph:
                if isinstance(node, dict) and node.get("@type") in ("Person", "Service"):
                    tutors.append(node)
    cards = []
    for link in page.locator("a[href*='/tutor/']").all():
        href = link.get_attribute("href") or ""
        m = re.search(r"/tutor/(\d+)", href)
        if m:
            cards.append({"id": m.group(1), "href": href})
    return tutors, cards


def scrape_profile(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)
    name = page.locator("h1").first.inner_text(timeout=10000)
    photo = None
    img = page.locator("img[alt*='" + name.split()[0] + "']").first
    try:
        photo = img.get_attribute("src")
    except Exception:
        pass
    body = page.locator("body").inner_text()
    price = None
    m = re.search(r"[€$]\s?\d+(?:[.,]\d\d)?", body)
    if m:
        price = m.group(0)
    return {"name": name, "photo": photo, "bio": body[:20000], "price": price}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/preply_raw.json")
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(locale="en-US")
        for n in range(1, args.max_pages + 1):
            url = LISTING_URL + (f"&page={n}" if n > 1 else "")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            _ld, cards = extract_cards(page)
            if not cards:
                break
            seen = {r["tutor_id"] for r in results}
            for card in cards:
                if card["id"] in seen:
                    continue
                profile_url = ("https://preply.com" + card["href"]
                               if card["href"].startswith("/") else card["href"])
                try:
                    prof = scrape_profile(page, profile_url)
                except Exception as exc:
                    print(f"profile {card['id']} failed: {exc}")
                    continue
                results.append({
                    "platform": "preply",
                    "tutor_id": card["id"],
                    "url": profile_url.split("?")[0],
                    **prof,
                })
                print(f"scraped {prof['name']} ({len(results)} total)")
                time.sleep(1.5)

        browser.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"wrote {len(results)} tutors to {out}")


if __name__ == "__main__":
    main()
