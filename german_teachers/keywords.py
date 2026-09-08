"""Keyword matching and scoring for Tom's ideal German teacher profile.

Groups are weighted: lifestyle / SRS / chunk-based signals are rare and
high-value, style signals are common and lower-value. A teacher's score is
the sum of the weights of every group that matched at least once.
"""

import re
import unicodedata

# group -> (weight, [regex patterns, case-insensitive])
KEYWORD_GROUPS = {
    "berlin": (3, [r"\bberlin\b"]),
    "anki_srs": (4, [r"\banki\b", r"spaced[- ]repetition", r"\bsrs\b", r"flash[- ]?cards?"]),
    "lifestyle": (4, [r"\bvegans?\b", r"\bvegetarian(ism)?\b", r"effective altruis[mt]",
                      r"\brationalist\b", r"\brationality\b"]),
    "chunks": (4, [r"chunk[- ]based", r"\bchunks?\b", r"\bchunking\b", r"lexical approach",
                   r"syntactic approach"]),
    "conversational": (2, [r"conversation(al)?", r"\bspeaking practice\b", r"\bchat\b",
                           r"\bdiscussions?\b"]),
    "unconventional": (2, [r"unconventional", r"\bno textbooks?\b", r"without (a )?textbook",
                           r"not (very |too )?academic", r"less academic", r"\brelaxed\b",
                           r"\blaid[- ]back\b", r"\bcasual\b", r"\bfun\b", r"no pressure",
                           r"without pressure", r"creative methods?"]),
    "flexible": (3, [r"\bflexible\b", r"\bflexibility\b", r"\badaptable\b", r"\btailor(ed)?\b",
                     r"\bcustomiz", r"\bpersonaliz", r"adapted? to (you|your)"]),
    "goal_based": (3, [r"goal[- ](oriented|focused|based)", r"\byour goals\b", r"\bobjectives?\b",
                       r"reach your goals?"]),
    "beginner": (3, [r"\bbeginners?\b", r"\bA1\b", r"\bA2\b", r"from (scratch|zero)",
                     r"absolute beginner"]),
}

LABELS = {
    "berlin": "Berlin",
    "anki_srs": "Anki / SRS",
    "lifestyle": "Vegan / EA / rationality",
    "chunks": "Chunk-based",
    "conversational": "Conversational",
    "unconventional": "Unconventional / relaxed",
    "flexible": "Flexible",
    "goal_based": "Goal-based",
    "beginner": "Beginner-friendly",
}

MAX_SCORE = sum(w for w, _ in KEYWORD_GROUPS.values())


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return text.encode("ascii", "ignore").decode("ascii").lower()


def match_keywords(text: str) -> dict:
    """Return {group: [matched fragments]} for every group that hits."""
    text = _norm(text)
    hits = {}
    for group, (_w, patterns) in KEYWORD_GROUPS.items():
        found = []
        for pat in patterns:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                frag = m.group(0)
                if frag not in found:
                    found.append(frag)
        if found:
            hits[group] = found
    return hits


def score(hits: dict) -> int:
    return sum(KEYWORD_GROUPS[g][0] for g in hits)
