"""Render the branded HTML report from data/teachers.json.

Usage:
    python -m german_teachers.build_report \
        --data data/teachers.json --out report/german-teachers.html

The template lives in german_teachers/template.html and contains the
placeholder __TEACHERS_JSON__ plus __GENERATED_AT__.
"""

import argparse
import json
from datetime import date
from pathlib import Path

from german_teachers.keywords import KEYWORD_GROUPS, LABELS, match_keywords, score

HERE = Path(__file__).parent

# discovery-pass tags -> keyword groups
FLAG_TO_GROUP = {
    "berlin": "berlin",
    "anki": "anki_srs", "spaced repetition": "anki_srs", "srs": "anki_srs",
    "vegan": "lifestyle", "vegetarian": "lifestyle", "effective altruism": "lifestyle",
    "rationality": "lifestyle", "lifestyle": "lifestyle",
    "chunk-based": "chunks", "chunks": "chunks",
    "conversational": "conversational",
    "relaxed": "unconventional", "unconventional": "unconventional",
    "no-textbook": "unconventional",
    "flexible": "flexible", "adaptable": "flexible",
    "goal-oriented": "goal_based", "goal-focused": "goal_based",
    "beginner-friendly": "beginner",
}


ITALKI_BONUS = 2      # Tom has credit on italki, so italki profiles get a boost
TOP_MATCH_MIN = 10    # score at or above this = "coup de coeur" tier
NEW_MAX_LESSONS = 300  # under this (or explicit newness) = trainable new teacher


def enrich(teacher: dict) -> dict:
    text = " ".join(filter(None, [
        teacher.get("bio", ""),
        " ".join(teacher.get("bio_snippets", []) or []),
        teacher.get("city") or "",
        teacher.get("living_city") or "",
    ]))
    hits = match_keywords(text)
    if teacher.get("berlin"):
        hits.setdefault("berlin", ["berlin"])
    for flag in teacher.get("flags") or []:
        group = FLAG_TO_GROUP.get(str(flag).strip().lower())
        if group:
            hits.setdefault(group, [str(flag)])
    if teacher.get("teaches_beginners") is True:
        hits.setdefault("beginner", ["teaches beginners"])
    teacher["keyword_groups"] = sorted(hits.keys())
    teacher["keyword_labels"] = [LABELS[g] for g in sorted(hits, key=lambda g: -KEYWORD_GROUPS[g][0])]
    teacher["score"] = score(hits) + (ITALKI_BONUS if teacher.get("platform") == "italki" else 0)
    lessons = teacher.get("lessons_count")
    teacher["is_new"] = bool(teacher.get("is_new")) or (
        lessons is not None and lessons < NEW_MAX_LESSONS)
    teacher["is_top"] = teacher["score"] >= TOP_MATCH_MIN
    return teacher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/teachers.json")
    parser.add_argument("--out", default="report/german-teachers.html")
    args = parser.parse_args()

    teachers = json.loads(Path(args.data).read_text())
    teachers = [enrich(t) for t in teachers]
    teachers.sort(key=lambda t: -t["score"])

    template = (HERE / "template.html").read_text()
    teachers_json = json.dumps(teachers, ensure_ascii=False).replace("</", "<\\/")
    html = (template
            .replace("__TEACHERS_JSON__", teachers_json)
            .replace("__GENERATED_AT__", date.today().strftime("%d/%m/%Y")))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"wrote {out} with {len(teachers)} teachers")


if __name__ == "__main__":
    main()
