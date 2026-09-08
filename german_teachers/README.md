# German teachers pipeline

Finds German teachers on italki and Preply matching Tom's profile:
native German speakers born in Germany, English-speaking, active, with a
conversational / flexible / goal-based style, plus rare affinity signals
(Berlin, Anki, spaced repetition, vegan / vegetarian, effective altruism,
rationality, chunk-based learning).

## Files

- `italki_scraper.py`: pulls teachers from the italki JSON API
  (native German filter, speaks English, origin country DE).
- `preply_scraper.py`: Playwright scraper for the Preply listing
  (native + adaptable + goal focused filters) and tutor profiles.
- `keywords.py`: weighted keyword groups + scoring. `build_report.py` adds a
  +2 italki bonus (Tom has credit there) and classifies two tiers:
  `is_top` (score >= 10) and `is_new` (< 300 lessons or newly joined,
  trainable teachers with open calendars).
- `merge_search_data.py`: merges/normalizes datasets into `data/teachers.json`.
- `build_report.py` + `template.html`: renders `report/german-teachers.html`,
  a filterable card view in the De Prof à Pro v3 brand style.

## Run

```bash
pip install requests playwright && playwright install chromium
python -m german_teachers.italki_scraper --out data/italki_teachers.json
python -m german_teachers.preply_scraper --out data/preply_tutors.json
python -m german_teachers.merge_search_data --out data/teachers.json
python -m german_teachers.build_report --data data/teachers.json --out report/german-teachers.html
```

## Note on the first dataset (Sept 2026)

The Claude Code remote environment that produced the first
`data/teachers.json` blocks direct HTTP access to italki.com and
preply.com (network egress policy), so that dataset was assembled from
public web search snippets of teacher profiles instead of live scraping:
photos and some prices are missing, and availability could not be read.
Run the two scrapers above from a normal network to refresh the dataset
with photos, prices and current availability, then rebuild the report.
