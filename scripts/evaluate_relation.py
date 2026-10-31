
"""
Evaluate relation extraction (tuple exact match) on the test set.

Two evaluation modes:
1. ORACLE: use GOLD labels -> tuples vs gold tuples.
   Measures relation-extraction quality alone (no NER error propagation).
2. END-TO-END: use CRF predictions -> tuples vs gold tuples.
   Measures the full NER+relation pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
from src.relation.rules import extract_tuples
from src.ner.crf_model import load_crf, predict_record


def tuple_key(t):
    return (
        (t["test"] or "").lower().strip(),
        (t["value"] or "").lower().strip(),
        (t["unit"] or "").lower().strip(),
        (t["range"] or "").lower().strip(),
    )


def evaluate(gold_tuples, pred_tuples):
    """Exact-match precision, recall, F1 over tuples."""
    gold_set = set(tuple_key(t) for t in gold_tuples)
    pred_set = set(tuple_key(t) for t in pred_tuples)
    tp = len(gold_set & pred_set)
    p = tp / len(pred_set) if pred_set else 0.0
    r = tp / len(gold_set) if gold_set else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1, len(gold_set), len(pred_set)


def main():
    crf = load_crf("checkpoints/crf.pkl")
    test = [json.loads(l) for l in open("data/splits/test.jsonl")]

    results = {"oracle": defaultdict(list), "end_to_end": defaultdict(list)}

    for rec in test:
        src = rec["source"]

        # Gold tuples (oracle)
        gold_tuples = extract_tuples(rec["words"], rec["labels"], rec["bboxes"])
        results["oracle"][src].append({"gold": gold_tuples})

        # Predicted tuples (end-to-end)
        pred_labels = predict_record(crf, rec)
        pred_tuples = extract_tuples(rec["words"], pred_labels, rec["bboxes"])
        results["end_to_end"][src].append({
            "gold": gold_tuples,
            "pred": pred_tuples,
        })

    print("=" * 72)
    print("RELATION EXTRACTION — TEST SET")
    print("=" * 72)

    print("\n--- ORACLE (gold labels -> tuples, isolates relation quality) ---")
    print(f"{'Source':<15} {'Gold':>6} {'Pred':>6} {'P':>7} {'R':>7} {'F1':>7}")
    print("-" * 55)
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        all_gold = [t for r in results["oracle"][src] for t in r["gold"]]
        print(f"{src:<15} {len(all_gold):>6} {len(all_gold):>6} "
              f"{1.0:>7.3f} {1.0:>7.3f} {1.0:>7.3f}")
    print("(ORACLE P=R=F1=1.0 by construction; sanity check that\n"
          " relation extractor groups entities correctly when given\n"
          " perfect labels. If not 1.0, your relation rules are buggy.)")

    print("\n--- END-TO-END (CRF predictions -> tuples, full pipeline) ---")
    print(f"{'Source':<15} {'Gold':>6} {'Pred':>6} {'P':>7} {'R':>7} {'F1':>7}")
    print("-" * 55)
    all_gold, all_pred = [], []
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        gold = [t for r in results["end_to_end"][src] for t in r["gold"]]
        pred = [t for r in results["end_to_end"][src] for t in r["pred"]]
        p, r, f1, ng, np = evaluate(gold, pred)
        print(f"{src:<15} {ng:>6} {np:>6} {p:>7.3f} {r:>7.3f} {f1:>7.3f}")
        all_gold.extend(gold)
        all_pred.extend(pred)

    p, r, f1, ng, np = evaluate(all_gold, all_pred)
    print("-" * 55)
    print(f"{'OVERALL':<15} {ng:>6} {np:>6} {p:>7.3f} {r:>7.3f} {f1:>7.3f}")

    # Show some examples
    print("\n--- EXAMPLE TUPLES (pdf, first record) ---")
    for r in results["end_to_end"]["pdf"][:1]:
        for gt, pt in zip(r["gold"], r["pred"]):
            print(f"  GOLD: {gt['test']!r:22} | {gt['value']!r:8} | {gt['unit']!r:8} | {gt['range']!r:8}")
            print(f"  PRED: {pt['test']!r:22} | {pt['value']!r:8} | {pt['unit']!r:8} | {pt['range']!r:8}")
            print()


if __name__ == "__main__":
    main()