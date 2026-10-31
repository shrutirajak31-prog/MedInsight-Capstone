"""
Annotate processed reports with BIO labels.

Strategy: because synthetic data has known test names, we walk words in
reading order and emit:
  - B-TEST / I-TEST for known test names (word-level fuzzy match)
  - B-VALUE / I-VALUE for the first number after a test
  - B-UNIT / I-UNIT for the first unit-like token after the value
  - B-REF_RANGE / I-REF_RANGE for range-like tokens (<200, 0.4 - 4.0, 5 - 40)

Fixed bugs so far:
  1. Multi-word test spans require all tokens to be alphabetic (no digits).
  2. Single-token RANGE_RE requires an operator or dash.
  3. Multi-token ranges checked BEFORE single-token ranges.
  4. Guard against ref_start >= len(words) — page may end mid-row.
  5. Word-level fuzzy match: prevents "Range Total" from matching
     "total cholesterol" at the whole-phrase level.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os
import re
from rapidfuzz import fuzz

KNOWN_TESTS = [
    "non-hdl cholesterol", "total cholesterol", "ldl cholesterol",
    "hdl cholesterol", "vldl cholesterol", "triglycerides",
    "bilirubin total", "uric acid", "hemoglobin", "hematocrit",
    "creatinine", "platelets", "albumin", "urea", "tsh", "t3", "t4",
    "wbc", "rbc", "alt", "ast",
]

VALUE_RE = re.compile(r"^\d+(\.\d+)?$")

UNIT_RE = re.compile(
    r"^(mg[/]?dl|mgldl|miu[/]?l|ng[/]?dl|ug[/]?dl|g[/]?dl|u[/]?l|"
    r"10\^?[36][/]?u[/]?l|%)$",
    re.IGNORECASE,
)

OPERATOR_RE = re.compile(r"^[<>]$")

SINGLE_RANGE_RE = re.compile(
    r"^([<>]\s*\d+(\.\d+)?|\d+(\.\d+)?\s*[-–]\s*\d+(\.\d+)?)$"
)


def _is_alpha_token(tok):
    t = tok.strip(",:.()")
    return bool(t) and t.replace("-", "").replace("'", "").isalpha()


def fuzzy_test_match(text, threshold_single=75, threshold_multi=70):
    """
    Word-level fuzzy match.

    Requires the same word count as the canonical test, then averages
    per-word best-match scores. This prevents "Range Total" from matching
    "total cholesterol" (score 60) while still accepting OCR errors like
    "VDL Choleaterd" -> "vldl cholesterol" (score 73).
    """
    t = text.lower().strip(",:.()")
    words_t = t.split()
    if not words_t:
        return None

    best_score = 0.0
    best = None

    for canonical in KNOWN_TESTS:
        words_c = canonical.split()
        if len(words_t) != len(words_c):
            continue
        per_word = [max(fuzz.ratio(wt, wc) for wc in words_c) for wt in words_t]
        avg = sum(per_word) / len(per_word)
        if avg > best_score:
            best_score = avg
            best = canonical

    threshold = threshold_multi if len(words_t) > 1 else threshold_single
    return best if best_score >= threshold else None


def _detect_ref_range_end(words, ref_start):
    n = len(words)
    if ref_start >= n:
        return ref_start

    # 3-token: "value - value"
    if (ref_start + 2 < n
            and VALUE_RE.match(words[ref_start].strip(",:."))
            and words[ref_start + 1].strip() in ("-", "–", "to")
            and VALUE_RE.match(words[ref_start + 2].strip(",:."))):
        return ref_start + 3

    # 2-token: "< value" / "> value"
    if (ref_start + 1 < n
            and OPERATOR_RE.match(words[ref_start].strip(",:."))
            and VALUE_RE.match(words[ref_start + 1].strip(",:."))):
        return ref_start + 2

    # 1-token: "<200" / "0.4-4.0"
    if SINGLE_RANGE_RE.match(words[ref_start].strip(",:.")):
        return ref_start + 1

    return ref_start


def annotate_words(words):
    labels = ["O"] * len(words)
    n = len(words)
    i = 0

    while i < n:
        matched = False
        for span in (3, 2, 1):
            if i + span > n:
                continue
            phrase_tokens = words[i:i + span]
            if span > 1 and not all(_is_alpha_token(t) for t in phrase_tokens):
                continue
            phrase = " ".join(phrase_tokens)
            canonical = fuzzy_test_match(phrase)
            if not canonical:
                continue

            labels[i] = "B-TEST"
            for k in range(1, span):
                labels[i + k] = "I-TEST"

            j = i + span
            while j < n and words[j].strip() in ("", ":", "-", "|"):
                j += 1

            if j < n and VALUE_RE.match(words[j].strip(",:.")):
                labels[j] = "B-VALUE"
                j += 1
                if (j < n and VALUE_RE.match(words[j].strip(",:."))
                        and len(words[j].strip(",:.")) <= 2):
                    labels[j] = "I-VALUE"
                    j += 1

            if (j < n
                    and UNIT_RE.match(words[j].strip(",:."))
                    and not VALUE_RE.match(words[j].strip(",:."))):
                labels[j] = "B-UNIT"
                j += 1

            ref_start = j
            if ref_start >= n:
                i = n
                matched = True
                break

            ref_end = _detect_ref_range_end(words, ref_start)
            if ref_end > ref_start:
                labels[ref_start] = "B-REF_RANGE"
                for k in range(ref_start + 1, ref_end):
                    labels[k] = "I-REF_RANGE"

            i = max(i + span, ref_end)
            matched = True
            break

        if not matched:
            i += 1

    return labels


def process_file(in_path, out_path):
    d = json.load(open(in_path))
    out_words, out_labels, out_bboxes = [], [], []
    for page in d["pages"]:
        texts = [w["text"] for w in page["words"]]
        bboxes = [w["bbox"] for w in page["words"]]
        out_words.extend(texts)
        out_labels.extend(annotate_words(texts))
        out_bboxes.extend(bboxes)

    json.dump({
        "id": d["id"],
        "source": d["source"],
        "words": out_words,
        "bboxes": out_bboxes,
        "labels": out_labels,
    }, open(out_path, "w"), default=float)


def main():
    os.makedirs("data/annotated", exist_ok=True)
    for f in os.listdir("data/annotated"):
        if f.endswith(".json"):
            os.remove(f"data/annotated/{f}")

    for fname in sorted(os.listdir("data/processed")):
        if not fname.endswith(".json"):
            continue
        process_file(f"data/processed/{fname}", f"data/annotated/{fname}")
        print(f"[annotated] {fname}")

    print(f"\nDone. Files in data/annotated: {len(os.listdir('data/annotated'))}")


if __name__ == "__main__":
    main()