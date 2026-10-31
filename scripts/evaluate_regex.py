"""
Evaluate the regex NER baseline on train/dev/test splits,
broken down by source (pdf / clean_ocr / degraded_ocr).
Reports entity-level F1 per entity type using seqeval.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict, Counter
from seqeval.metrics import classification_report, f1_score
from src.ner.regex_baseline import predict_labels


def evaluate_split(path):
    """Return {(source, entity): (p, r, f1), ...} plus overall."""
    per_source = defaultdict(lambda: {"gold": [], "pred": []})

    for line in open(path):
        d = json.loads(line)
        src = d["source"]
        gold = d["labels"]
        pred = predict_labels(d["words"])
        per_source[src]["gold"].append(gold)
        per_source[src]["pred"].append(pred)

    results = {}
    for src, data in per_source.items():
        results[src] = {
            "n_files": len(data["gold"]),
            "f1_micro": f1_score(data["gold"], data["pred"], average="micro"),
            "report": classification_report(data["gold"], data["pred"], digits=3, zero_division=0),
        }

    # overall
    all_gold = sum((v["gold"] for v in per_source.values()), [])
    all_pred = sum((v["pred"] for v in per_source.values()), [])
    results["__overall__"] = {
        "n_files": len(all_gold),
        "f1_micro": f1_score(all_gold, all_pred, average="micro"),
    }
    return results


def main():
    print("=" * 70)
    print("REGEX NER BASELINE — TEST SET")
    print("=" * 70)

    results = evaluate_split("data/splits/test.jsonl")

    print("\nMicro-F1 by input source:")
    print(f"{'Source':<20} {'Files':>6} {'Micro-F1':>10}")
    print("-" * 40)
    for src in ("pdf", "ocr_clean", "ocr_degraded", "__overall__"):
        if src not in results:
            continue
        r = results[src]
        label = "OVERALL" if src == "__overall__" else src
        print(f"{label:<20} {r['n_files']:>6} {r['f1_micro']:>10.3f}")

    print("\n" + "=" * 70)
    print("Per-source detailed report (precision / recall / F1 per entity type)")
    print("=" * 70)
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        if src not in results:
            continue
        print(f"\n--- {src.upper()} ---")
        print(results[src]["report"])


if __name__ == "__main__":
    main()