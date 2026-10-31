"""
Split annotated data into train/dev/test by base report ID.
Grouping is done via regex so that "report_077_pdf" and
"report_077_0_clean_ocr" both map to base id "report_077".
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os
import random
import glob
import re

random.seed(42)


def base_report_id(rid):
    """Strip _pdf / _clean_ocr / _degraded_ocr and any trailing page number."""
    for suffix in ("_pdf", "_clean_ocr", "_degraded_ocr"):
        if rid.endswith(suffix):
            rid = rid[:-len(suffix)]
            break
    m = re.match(r"^(report_\d+)", rid)
    return m.group(1) if m else rid


def main():
    os.makedirs("data/splits", exist_ok=True)

    by_report = {}
    for f in sorted(glob.glob("data/annotated/*.json")):
        rid = base_report_id(os.path.basename(f).replace(".json", ""))
        by_report.setdefault(rid, []).append(f)

    report_ids = sorted(by_report.keys())
    random.shuffle(report_ids)

    n = len(report_ids)
    n_test = max(1, int(n * 0.15))
    n_dev = max(1, int(n * 0.15))

    test_ids = set(report_ids[:n_test])
    dev_ids = set(report_ids[n_test:n_test + n_dev])
    train_ids = set(report_ids[n_test + n_dev:])

    for name, ids in [("train", train_ids), ("dev", dev_ids), ("test", test_ids)]:
        out_path = f"data/splits/{name}.jsonl"
        with open(out_path, "w") as out:
            for rid in sorted(ids):
                for f in by_report[rid]:
                    d = json.load(open(f))
                    out.write(json.dumps(d) + "\n")
        n_lines = sum(1 for _ in open(out_path))
        print(f"{name}: {len(ids)} reports, {n_lines} files")

    print(f"Total reports: {n}")


if __name__ == "__main__":
    main()