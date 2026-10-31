"""
Regex NER baseline.
Uses exact string match against known test names (no fuzzy).
Uses regex for value, unit, range.

This is the "no ML" baseline. It works on clean text and fails on OCR.
"""

import re

KNOWN_TESTS = set([
    "non-hdl cholesterol", "total cholesterol", "ldl cholesterol",
    "hdl cholesterol", "vldl cholesterol", "triglycerides",
    "bilirubin total", "uric acid", "hemoglobin", "hematocrit",
    "creatinine", "platelets", "albumin", "urea", "tsh", "t3", "t4",
    "wbc", "rbc", "alt", "ast",
])

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


def _detect_range_end(words, start):
    n = len(words)
    if start >= n:
        return start
    if (start + 2 < n
            and VALUE_RE.match(words[start].strip(",:."))
            and words[start + 1].strip() in ("-", "–", "to")
            and VALUE_RE.match(words[start + 2].strip(",:."))):
        return start + 3
    if (start + 1 < n
            and OPERATOR_RE.match(words[start].strip(",:."))
            and VALUE_RE.match(words[start + 1].strip(",:."))):
        return start + 2
    if SINGLE_RANGE_RE.match(words[start].strip(",:.")):
        return start + 1
    return start


def predict_labels(words):
    labels = ["O"] * len(words)
    n = len(words)
    i = 0
    while i < n:
        matched = False
        for span in (3, 2, 1):
            if i + span > n:
                continue
            phrase = " ".join(words[i:i + span]).lower().strip(",:.()")
            # EXACT match only (no fuzzy). This is the baseline's weakness.
            if phrase not in KNOWN_TESTS:
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
            if (j < n
                    and UNIT_RE.match(words[j].strip(",:."))
                    and not VALUE_RE.match(words[j].strip(",:."))):
                labels[j] = "B-UNIT"
                j += 1
            ref_end = _detect_range_end(words, j)
            if ref_end > j:
                labels[j] = "B-REF_RANGE"
                for k in range(j + 1, ref_end):
                    labels[k] = "I-REF_RANGE"
            i = max(i + span, ref_end)
            matched = True
            break
        if not matched:
            i += 1
    return labels