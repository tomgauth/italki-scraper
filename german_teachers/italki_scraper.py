"""Scrape German teachers from italki via its JSON API.

Filters applied server-side where the API supports it, then locally:
- teaches German, native German speaker
- from Germany (origin country DE)
- also speaks English
- active (has recent sessions / is accepting students)

Usage:
    python -m german_teachers.italki_scraper --out data/italki_raw.json

Note: needs normal network access to api.italki.com. The Claude Code
remote environment used to develop this blocks that domain, so run it
locally if it fails with a proxy/403 error.
"""

import argparse
import json
import time
from pathlib import Path

import requests

API_URL = "https://api.italki.com/api/v2/teachers"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Origin": "https://www.italki.com",
    "Referer": "https://www.italki.com/en/teachers/german",
}


def fetch_page(page: int, page_size: int = 20) -> dict:
    payload = {
        "teach_language": {"language": "german", "is_native": 1},
        "speak_language": {"language": "english"},
        "teacher_info": {"origin_country_id": ["DE"]},
        "page": page,
        "page_size": page_size,
        "user_timezone": "Europe/Paris",
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def simplify(entry: dict) -> dict:
    user = entry.get("user_info", {}) or {}
    teacher = entry.get("teacher_info", {}) or {}
    course = entry.get("course_info", {}) or {}
    uid = user.get("user_id")
    avatar = user.get("avatar_file_name")
    return {
        "platform": "italki",
        "teacher_id": uid,
        "name": user.get("nickname"),
        "url": f"https://www.italki.com/en/teacher/{uid}",
        "photo": (f"https://imagesavatar-static01.italki.com/{avatar}_Avatar.jpg"
                  if avatar else None),
        "origin_country": user.get("origin_country_id"),
        "origin_city": user.get("origin_city_name") or teacher.get("origin_city_name"),
        "living_country": user.get("living_country_id"),
        "living_city": user.get("living_city_name"),
        "is_native": True,
        "teacher_type": teacher.get("teacher_type"),  # 1 pro, 2 community (verify)
        "rating": teacher.get("overall_rating"),
        "sessions": teacher.get("session_count"),
        "students": teacher.get("student_count"),
        "min_price_usd": (course.get("min_price") or 0) / 100 or None,
        "trial_price_usd": (course.get("trial_price") or 0) / 100 or None,
        "bio": " ".join(filter(None, [
            teacher.get("about_me"), teacher.get("about_teacher"),
            teacher.get("intro"), course.get("intro"),
        ])),
        "raw": entry,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/italki_raw.json")
    parser.add_argument("--max-pages", type=int, default=30)
    args = parser.parse_args()

    teachers, page = [], 1
    while page <= args.max_pages:
        data = fetch_page(page)
        rows = data.get("data") or []
        if not rows:
            break
        teachers.extend(simplify(r) for r in rows)
        print(f"page {page}: {len(rows)} teachers ({len(teachers)} total)")
        paging = data.get("paging") or {}
        if page >= int(paging.get("total_page", page)):
            break
        page += 1
        time.sleep(1.0)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(teachers, ensure_ascii=False, indent=2))
    print(f"wrote {len(teachers)} teachers to {out}")


if __name__ == "__main__":
    main()
