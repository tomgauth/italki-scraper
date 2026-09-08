"""Merge the search-derived italki + Preply JSON files into data/teachers.json.

Input files (produced by the WebSearch discovery pass, or by the scrapers):
    data/italki_teachers.json, data/preply_tutors.json

Keeps only teachers with medium or high confidence of being a native
German speaker, dedupes by URL, and normalizes the schema for
build_report.py.
"""

import argparse
import json
import re
from pathlib import Path


UNAVAILABLE_RE = re.compile(r"not (currently )?accepting new students", re.I)


def norm(entry: dict) -> dict:
    city = entry.get("city")
    berlin = bool(entry.get("berlin")) or (city or "").strip().lower() == "berlin"
    lessons = entry.get("lessons") or entry.get("reviews")
    return {
        "name": (entry.get("name") or "?").strip(),
        "url": entry.get("url"),
        "platform": entry.get("platform"),
        "photo": entry.get("photo"),
        "city": city,
        "berlin": berlin,
        "price": entry.get("price"),
        "rating": entry.get("rating"),
        "lessons": lessons,
        "teacher_type": entry.get("teacher_type"),
        "native_evidence": entry.get("native_german_evidence"),
        "confidence": entry.get("confidence_native_from_germany"),
        "bio_snippets": entry.get("bio_snippets") or [],
        "flags": entry.get("keywords_found") or [],
        "from_germany": entry.get("from_germany"),
        "teaches_beginners": entry.get("teaches_beginners"),
        "lessons_count": entry.get("lessons_count"),
        "students_count": entry.get("students_count"),
        "teacher_since": entry.get("teacher_since"),
        "is_new": bool(entry.get("is_new")),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+",
                        default=["data/italki_teachers.json", "data/preply_tutors.json"])
    parser.add_argument("--out", default="data/teachers.json")
    parser.add_argument("--min-confidence", default="medium",
                        choices=["low", "medium", "high"])
    parser.add_argument("--require-germany", action="store_true",
                        help="keep only teachers with confirmed German origin")
    args = parser.parse_args()

    order = {"low": 0, "medium": 1, "high": 2, None: 0}
    keep_from = order[args.min_confidence]

    merged, seen = [], set()
    for path in args.inputs:
        p = Path(path)
        if not p.exists():
            print(f"skipping missing {p}")
            continue
        for entry in json.loads(p.read_text()):
            t = norm(entry)
            if not t["url"] or not t["name"] or t["name"] == "?":
                continue
            key = re.sub(r"[?#].*$", "", t["url"]).rstrip("/")
            if key in seen:
                continue
            if order.get(entry.get("confidence_native_from_germany"), 0) < keep_from:
                print(f"dropping {t['name']} (confidence too low)")
                continue
            if entry.get("from_germany") is False:
                print(f"dropping {t['name']} (not from Germany)")
                continue
            if args.require_germany and entry.get("from_germany") is not True:
                print(f"dropping {t['name']} (German origin not confirmed)")
                continue
            if entry.get("teaches_beginners") is False:
                print(f"dropping {t['name']} (does not teach beginners)")
                continue
            if any(UNAVAILABLE_RE.search(s or "") for s in t["bio_snippets"]):
                print(f"dropping {t['name']} (not accepting new students)")
                continue
            seen.add(key)
            merged.append(t)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    print(f"wrote {len(merged)} teachers to {out}")


if __name__ == "__main__":
    main()
