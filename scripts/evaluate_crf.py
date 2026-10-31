"""
Evaluate the trained CRF on the test set, broken down by input source.
Reports entity-level F1 per entity type using seqeval.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
from seqeval.metrics import classification_report, f1_score
from src.ner.crf_model import load_crf, predict_record


def main():
    crf = load_crf("checkpoints/crf.pkl")

    per_source = defaultdict(lambda: {"gold": [], "pred": []})

    with open("data/splits/test.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            src = rec["source"]
            pred = predict_record(crf, rec)
            per_source[src]["gold"].append(rec["labels"])
            per_source[src]["pred"].append(pred)

    print("=" * 70)
    print("CRF NER — TEST SET")
    print("=" * 70)

    print("\nMicro-F1 by input source:")
    print(f"{'Source':<20} {'Files':>6} {'Micro-F1':>10}")
    print("-" * 40)
    all_gold, all_pred = [], []
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        if src not in per_source:
            continue
        d = per_source[src]
        f1 = f1_score(d["gold"], d["pred"], average="micro")
        print(f"{src:<20} {len(d['gold']):>6} {f1:>10.4f}")
        all_gold.extend(d["gold"])
        all_pred.extend(d["pred"])
    if all_gold:
        overall_f1 = f1_score(all_gold, all_pred, average="micro")
        print(f"{'OVERALL':<20} {len(all_gold):>6} {overall_f1:>10.4f}")

    print("\n" + "=" * 70)
    print("Per-source detailed report")
    print("=" * 70)
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        if src not in per_source:
            continue
        print(f"\n--- {src.upper()} ---")
        print(classification_report(
            per_source[src]["gold"], per_source[src]["pred"],
            digits=3, zero_division=0,
        ))


if __name__ == "__main__":
    main()