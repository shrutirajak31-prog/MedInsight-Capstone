"""
Proximity-based relation extraction.

Given words, labels, and bounding boxes, group entities into tuples:
  (TEST, VALUE, UNIT, REF_RANGE)

Algorithm:
1. Extract entities from BIO labels (merge B-X + I-X runs into spans)
2. For each TEST entity, find the VALUE, UNIT, REF_RANGE whose y-center is
   closest to the TEST's y-center (same row) and whose x-start is to the right.
3. Emit one tuple per TEST.
"""


def spans_from_bio(words, labels, bboxes):
    """Merge BIO labels into (label, start, end, bbox, text) spans."""
    spans = []
    i = 0
    n = len(labels)
    while i < n:
        if labels[i].startswith("B-"):
            label = labels[i][2:]
            j = i + 1
            while j < n and labels[j] == f"I-{label}":
                j += 1
            xs0 = [bboxes[k][0] for k in range(i, j)]
            ys0 = [bboxes[k][1] for k in range(i, j)]
            xs1 = [bboxes[k][2] for k in range(i, j)]
            ys1 = [bboxes[k][3] for k in range(i, j)]
            spans.append({
                "label": label,
                "start": i,
                "end": j,
                "text": " ".join(words[i:j]),
                "bbox": (min(xs0), min(ys0), max(xs1), max(ys1)),
            })
            i = j
        else:
            i += 1
    return spans


def _yc(bbox):
    return (bbox[1] + bbox[3]) / 2


def _xc(bbox):
    return (bbox[0] + bbox[2]) / 2


def extract_tuples(words, labels, bboxes, y_tolerance=None):
    """
    Return list of dicts, one per TEST:
      {"test": str, "value": str|None, "unit": str|None, "range": str|None,
       "test_span": {...}, ...}

    Algorithm: for each TEST, look at entity spans to the right on the
    same y-row; take the first VALUE, first UNIT, first REF_RANGE.
    """
    spans = spans_from_bio(words, labels, bboxes)
    if not spans:
        return []

    # auto y-tolerance: 2% of page height
    max_y = max((s["bbox"][3] for s in spans), default=1)
    if y_tolerance is None:
        y_tolerance = max_y * 0.02
        y_tolerance = max(y_tolerance, 3)  # at least 3 px

    tests = [s for s in spans if s["label"] == "TEST"]
    values = [s for s in spans if s["label"] == "VALUE"]
    units = [s for s in spans if s["label"] == "UNIT"]
    ranges = [s for s in spans if s["label"] == "REF_RANGE"]

    tuples = []
    for test in tests:
        ty = _yc(test["bbox"])
        tx1 = test["bbox"][2]  # right edge of test

        def pick(candidates):
            """First entity same row, to the right of test, closest x."""
            rows = [c for c in candidates
                    if abs(_yc(c["bbox"]) - ty) <= y_tolerance
                    and c["bbox"][0] >= tx1 - 2]  # small left-tolerance
            if not rows:
                return None
            rows.sort(key=lambda c: _xc(c["bbox"]))
            return rows[0]

        v = pick(values)
        u = pick(units)
        r = pick(ranges)

        tuples.append({
            "test": test["text"],
            "value": v["text"] if v else None,
            "unit": u["text"] if u else None,
            "range": r["text"] if r else None,
            "test_span": test,
            "value_span": v,
            "unit_span": u,
            "range_span": r,
        })

    return tuples